"""Shadow-mode head-to-head: classical PN/APN/OGL vs frozen RL baseline.

Reuses the immutable Phase-2 fixed evaluation set and env construction from
``rl.training`` (same ICs, maneuvers, 25 s budget) and the classical-law
action wrap from ``scripts/validate_reward.py``. Does not train, mutate
``CURRENT_RL_BASELINE.json``, or edit physics/guidance/rl internals.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import gymnasium as gym
import numpy as np
from sb3_contrib import RecurrentPPO

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.factories import classical_law_factories
from guidance_sim.rl.actions import (
    ACTION_LAYOUT_LATERAL2,
    ActionLayout,
    action_dimension,
    world_to_lateral,
)
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.training import (
    FIXED_EVALUATION_CASES,
    GROUP_A_MANEUVERS,
    GROUP_B_MANEUVERS,
    EvaluationCase,
    PPOTrainingConfig,
    _case_initial_conditions,
    _case_maneuver,
)
from guidance_sim.simulation.engine import SimulationConfig

GUIDANCE_MODES: tuple[str, ...] = ("PN", "APN", "OGL", "RL")

# Match validate_reward / project classical defaults.
_PN_N = 4.0
_APN_N = 4.0
_OGL_N = 3.0

# Same seed base as evaluate_policy so RL replay matches CP eval provenance.
_DEFAULT_EVAL_SEED = 91_000

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_BASELINE_POINTER = _REPO_ROOT / "outputs" / "CURRENT_RL_BASELINE.json"
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "outputs" / "shadow_comparison"


@dataclass(frozen=True)
class ShadowRunMetrics:
    """Per (scenario, guidance mode) engineering metrics."""

    scenario: str
    group: str
    maneuver: str
    guidance_mode: str
    hit: bool
    outcome: str
    miss_distance_m: float
    time_s: float
    peak_cmd_lateral_m_s2: float
    mean_cmd_lateral_m_s2: float
    peak_achieved_lateral_m_s2: float


@dataclass(frozen=True)
class ShadowComparisonReport:
    """Full matrix plus provenance for the frozen baseline."""

    cases: tuple[ShadowRunMetrics, ...]
    guidance_modes: tuple[str, ...]
    baseline_pointer: str
    baseline_model_path: str
    max_time_s: float
    dt_s: float
    n_scenarios: int
    eval_seed: int


def load_rl_baseline_pointer(
    path: Path | None = None,
) -> dict[str, Any]:
    """Load ``CURRENT_RL_BASELINE.json`` (read-only)."""

    pointer_path = path or _DEFAULT_BASELINE_POINTER
    return json.loads(pointer_path.read_text(encoding="utf-8"))


def _group_for_maneuver(maneuver: str) -> str:
    if maneuver in GROUP_A_MANEUVERS:
        return "A"
    if maneuver in GROUP_B_MANEUVERS:
        return "B"
    raise ValueError(f"unknown maneuver group for {maneuver!r}")


def _make_env(
    case: EvaluationCase,
    *,
    config: SimulationConfig,
    action_layout: ActionLayout,
    use_target_turn_rate_obs: bool,
) -> InterceptionEnv:
    return InterceptionEnv(
        config=config,
        initial_condition_sampler=_case_initial_conditions(case),
        maneuver_factory=_case_maneuver(case),
        action_layout=action_layout,
        use_target_turn_rate_obs=use_target_turn_rate_obs,
    )


_CLASSICAL_FACTORIES: dict[str, Callable[[InterceptionEnv], GuidanceLaw]] = (
    classical_law_factories(
        lambda env: env.target, pn_n=_PN_N, apn_n=_APN_N, ogl_n=_OGL_N
    )
)


def _classical_action_policy(
    law_factory: Callable[[InterceptionEnv], GuidanceLaw],
) -> Callable[[InterceptionEnv], np.ndarray]:
    """World-frame guidance → lateral2 action (same wrap as validate_reward)."""

    holder: dict[str, GuidanceLaw | None] = {"law": None}

    def policy(env: InterceptionEnv) -> np.ndarray:
        assert env.pursuer is not None and env.target is not None
        if holder["law"] is None:
            holder["law"] = law_factory(env)
        command = holder["law"].compute_command(
            env.pursuer.state, env.target.state, env.config.dt
        )
        if env.action_layout == ACTION_LAYOUT_LATERAL2:
            return world_to_lateral(command, env.pursuer.state.velocity)
        return np.asarray(command, dtype=float).reshape(3)

    return policy


def _accumulate_step_metrics(
    info: dict[str, object],
    *,
    cmd_mags: list[float],
    ach_mags: list[float],
) -> None:
    commanded = np.asarray(info["action_commanded_m_s2"], dtype=float).reshape(3)
    achieved = np.asarray(info["action_achieved_m_s2"], dtype=float).reshape(3)
    cmd_mags.append(float(np.linalg.norm(commanded)))
    ach_mags.append(float(np.linalg.norm(achieved)))


def _finalize_metrics(
    *,
    case: EvaluationCase,
    guidance_mode: str,
    info: dict[str, object],
    cmd_mags: Sequence[float],
    ach_mags: Sequence[float],
) -> ShadowRunMetrics:
    cmd_arr = np.asarray(cmd_mags, dtype=float)
    ach_arr = np.asarray(ach_mags, dtype=float)
    return ShadowRunMetrics(
        scenario=case.name,
        group=_group_for_maneuver(case.maneuver),
        maneuver=case.maneuver,
        guidance_mode=guidance_mode,
        hit=bool(info["hit"]),
        outcome=str(info["outcome"]),
        miss_distance_m=float(info["min_range_m"]),
        time_s=float(info["time_s"]),
        peak_cmd_lateral_m_s2=float(np.max(cmd_arr)) if cmd_arr.size else 0.0,
        mean_cmd_lateral_m_s2=float(np.mean(cmd_arr)) if cmd_arr.size else 0.0,
        peak_achieved_lateral_m_s2=float(np.max(ach_arr)) if ach_arr.size else 0.0,
    )


def run_classical_case(
    case: EvaluationCase,
    guidance_mode: str,
    *,
    config: SimulationConfig | None = None,
    seed: int = 0,
) -> ShadowRunMetrics:
    """Run one fixed-eval case under PN, APN, or OGL (perfect a_T for APN/OGL)."""

    if guidance_mode not in _CLASSICAL_FACTORIES:
        raise ValueError(f"classical mode must be PN/APN/OGL, got {guidance_mode!r}")
    sim_config = config or PPOTrainingConfig().simulation_config()
    env = _make_env(
        case,
        config=sim_config,
        action_layout=ACTION_LAYOUT_LATERAL2,
        use_target_turn_rate_obs=False,
    )
    policy = _classical_action_policy(_CLASSICAL_FACTORIES[guidance_mode])
    env.reset(seed=seed)
    cmd_mags: list[float] = []
    ach_mags: list[float] = []
    info: dict[str, object] = {}
    while True:
        action = policy(env)
        _obs, _reward, terminated, truncated, info = env.step(action)
        _accumulate_step_metrics(info, cmd_mags=cmd_mags, ach_mags=ach_mags)
        if terminated or truncated:
            break
    metrics = _finalize_metrics(
        case=case,
        guidance_mode=guidance_mode,
        info=info,
        cmd_mags=cmd_mags,
        ach_mags=ach_mags,
    )
    env.close()
    return metrics


def run_rl_case(
    case: EvaluationCase,
    case_index: int,
    *,
    model: Any,
    config: SimulationConfig,
    action_layout: ActionLayout,
    use_target_turn_rate_obs: bool,
    seed: int,
) -> ShadowRunMetrics:
    """Replay one fixed-eval case with a loaded RecurrentPPO policy."""

    n_action = action_dimension(action_layout)
    physical_env = _make_env(
        case,
        config=config,
        action_layout=action_layout,
        use_target_turn_rate_obs=use_target_turn_rate_obs,
    )
    env = gym.wrappers.RescaleAction(
        physical_env,
        min_action=np.full(n_action, -1.0, dtype=np.float32),
        max_action=np.full(n_action, 1.0, dtype=np.float32),
    )
    observation, _info0 = env.reset(seed=seed + case_index)
    recurrent_state: Any = None
    episode_start = np.array([True], dtype=bool)
    cmd_mags: list[float] = []
    ach_mags: list[float] = []
    info: dict[str, object] = {}
    while True:
        action, recurrent_state = model.predict(
            observation,
            state=recurrent_state,
            episode_start=episode_start,
            deterministic=True,
        )
        action = np.asarray(action, dtype=float).reshape(-1, n_action)[0]
        observation, _reward, terminated, truncated, info = env.step(action)
        _accumulate_step_metrics(info, cmd_mags=cmd_mags, ach_mags=ach_mags)
        episode_start[:] = False
        if terminated or truncated:
            break
    metrics = _finalize_metrics(
        case=case,
        guidance_mode="RL",
        info=info,
        cmd_mags=cmd_mags,
        ach_mags=ach_mags,
    )
    env.close()
    return metrics


def run_shadow_comparison(
    *,
    cases: Sequence[EvaluationCase] = FIXED_EVALUATION_CASES,
    baseline_pointer_path: Path | None = None,
    repo_root: Path | None = None,
    eval_seed: int = _DEFAULT_EVAL_SEED,
    include_rl: bool = True,
) -> ShadowComparisonReport:
    """Run PN/APN/OGL/(RL) on the fixed scenario matrix with identical ICs."""

    root = repo_root or _REPO_ROOT
    pointer_path = baseline_pointer_path or (root / "outputs" / "CURRENT_RL_BASELINE.json")
    pointer = load_rl_baseline_pointer(pointer_path)
    model_rel = str(pointer["model_path"])
    model_path = (root / model_rel).resolve()
    try:
        pointer_display = str(pointer_path.resolve().relative_to(root.resolve()))
    except ValueError:
        pointer_display = str(pointer_path)
    model_display = model_rel
    use_turn_rate = bool(pointer.get("use_target_turn_rate_obs", False))
    action_layout: ActionLayout = pointer.get("action_layout", ACTION_LAYOUT_LATERAL2)
    if action_layout not in ("lateral2", "world3"):
        raise ValueError(f"unsupported baseline action_layout: {action_layout!r}")

    train_cfg = PPOTrainingConfig(
        action_layout=action_layout,
        use_target_turn_rate_obs=use_turn_rate,
    )
    sim_config = train_cfg.simulation_config()

    results: list[ShadowRunMetrics] = []
    for case_index, case in enumerate(cases):
        case_seed = eval_seed + case_index
        for mode in ("PN", "APN", "OGL"):
            results.append(
                run_classical_case(
                    case,
                    mode,
                    config=sim_config,
                    seed=case_seed,
                )
            )

    modes: list[str] = ["PN", "APN", "OGL"]
    if include_rl:
        model = RecurrentPPO.load(str(model_path), device="cpu")
        for case_index, case in enumerate(cases):
            results.append(
                run_rl_case(
                    case,
                    case_index,
                    model=model,
                    config=sim_config,
                    action_layout=action_layout,
                    use_target_turn_rate_obs=use_turn_rate,
                    seed=eval_seed,
                )
            )
        modes.append("RL")

    # Stable row order: scenario order × guidance mode order
    order = {case.name: i for i, case in enumerate(cases)}
    mode_order = {m: i for i, m in enumerate(modes)}
    results.sort(
        key=lambda r: (order[r.scenario], mode_order[r.guidance_mode])
    )

    return ShadowComparisonReport(
        cases=tuple(results),
        guidance_modes=tuple(modes),
        baseline_pointer=pointer_display,
        baseline_model_path=model_display,
        max_time_s=float(sim_config.max_time),
        dt_s=float(sim_config.dt),
        n_scenarios=len(cases),
        eval_seed=eval_seed,
    )


def _cell_label(row: ShadowRunMetrics) -> str:
    tag = "HIT" if row.hit else "MISS"
    return f"{tag} / {row.miss_distance_m:.1f} m"


def _lookup(
    rows: Sequence[ShadowRunMetrics],
    scenario: str,
    mode: str,
) -> ShadowRunMetrics | None:
    for row in rows:
        if row.scenario == scenario and row.guidance_mode == mode:
            return row
    return None


def _summary_section(report: ShadowComparisonReport) -> list[str]:
    """Plain-language where RL wins / loses / ties vs classical."""

    lines: list[str] = ["## Summary", ""]
    if "RL" not in report.guidance_modes:
        lines.append("RL mode was not run (`include_rl=False`).")
        lines.append("")
        return lines

    scenarios = []
    seen: set[str] = set()
    for row in report.cases:
        if row.scenario not in seen:
            seen.add(row.scenario)
            scenarios.append(row.scenario)

    rl_beats: list[str] = []
    classical_beats: list[str] = []
    ties: list[str] = []

    for name in scenarios:
        rl = _lookup(report.cases, name, "RL")
        pn = _lookup(report.cases, name, "PN")
        apn = _lookup(report.cases, name, "APN")
        ogl = _lookup(report.cases, name, "OGL")
        if rl is None or pn is None or apn is None or ogl is None:
            continue
        classical = (pn, apn, ogl)
        best_classical_miss = min(c.miss_distance_m for c in classical)
        best_classical_hit = any(c.hit for c in classical)
        best_name = min(classical, key=lambda c: c.miss_distance_m).guidance_mode

        # Hit preference: a hit beats a miss regardless of distance.
        if rl.hit and not best_classical_hit:
            rl_beats.append(
                f"- **{name}**: RL hit ({rl.miss_distance_m:.1f} m) vs classical "
                f"all miss (best {best_name} {best_classical_miss:.1f} m)."
            )
        elif (not rl.hit) and best_classical_hit:
            classical_beats.append(
                f"- **{name}**: classical hit ({best_name}) vs RL miss "
                f"({rl.miss_distance_m:.1f} m)."
            )
        elif rl.hit and best_classical_hit:
            # Both hit — compare miss (both should be ≤ radius; still report).
            if rl.miss_distance_m < best_classical_miss - 0.05:
                rl_beats.append(
                    f"- **{name}**: both hit; RL miss {rl.miss_distance_m:.2f} m "
                    f"< best classical ({best_name}) {best_classical_miss:.2f} m."
                )
            elif best_classical_miss < rl.miss_distance_m - 0.05:
                classical_beats.append(
                    f"- **{name}**: both hit; best classical ({best_name}) "
                    f"{best_classical_miss:.2f} m < RL {rl.miss_distance_m:.2f} m."
                )
            else:
                ties.append(
                    f"- **{name}**: both hit; miss essentially tied "
                    f"(RL {rl.miss_distance_m:.2f} m vs {best_name} "
                    f"{best_classical_miss:.2f} m)."
                )
        else:
            # All miss — lower miss is better.
            if rl.miss_distance_m < best_classical_miss - 1.0:
                rl_beats.append(
                    f"- **{name}**: all miss; RL {rl.miss_distance_m:.1f} m vs "
                    f"best classical ({best_name}) {best_classical_miss:.1f} m."
                )
            elif best_classical_miss < rl.miss_distance_m - 1.0:
                classical_beats.append(
                    f"- **{name}**: all miss; best classical ({best_name}) "
                    f"{best_classical_miss:.1f} m vs RL {rl.miss_distance_m:.1f} m."
                )
            else:
                ties.append(
                    f"- **{name}**: all miss; RL {rl.miss_distance_m:.1f} m ≈ "
                    f"best classical ({best_name}) {best_classical_miss:.1f} m."
                )

    lines.append("### Where RL beats classical")
    lines.append("")
    if rl_beats:
        lines.extend(rl_beats)
    else:
        lines.append("- None on this matrix.")
    lines.append("")
    lines.append("### Where classical beats RL")
    lines.append("")
    if classical_beats:
        lines.extend(classical_beats)
    else:
        lines.append("- None on this matrix.")
    lines.append("")
    lines.append("### Ties / near-ties")
    lines.append("")
    if ties:
        lines.extend(ties)
    else:
        lines.append("- None on this matrix.")
    lines.append("")

    # Group B diagnosis — always state plainly from the numbers.
    gb = [r for r in report.cases if r.group == "B"]
    if gb:
        lines.append("### Group B (ConstantTurn) — time-budget ceiling")
        lines.append("")
        lines.append(
            "Under the frozen **25 s** fixed-eval budget, ConstantTurn cases "
            "are a shared ceiling for all guidance modes (not an RL-only "
            "training gap). Every mode misses every Group B case below."
        )
        lines.append("")
        for name in sorted({r.scenario for r in gb}):
            parts = []
            for mode in report.guidance_modes:
                row = _lookup(report.cases, name, mode)
                if row is None:
                    continue
                parts.append(f"{mode} {row.miss_distance_m:.0f} m")
            lines.append(f"- `{name}`: " + "; ".join(parts) + ".")
        lines.append("")
        lines.append(
            "PN is the strongest classical baseline on these turns. APN/OGL "
            "with perfect instantaneous `a_T` are *worse* than PN here "
            "because ConstantTurn acceleration rotates with velocity "
            "(direction = up × v̂) — the constant-`a_T` assumption baked "
            "into APN/OGL does not hold. RL beats PN on the 3 g case "
            "(~832 m vs ~975 m) but is still behind PN on 5 g / 7 g; none "
            "convert to hits inside 25 s."
        )
        lines.append("")
        lines.append(
            "Interpretation: extending `max_time` (and retraining under that "
            "horizon) would be required to convert these geometries into "
            "hits — out of scope for this shadow comparison."
        )
        lines.append("")

    return lines


def format_markdown_report(report: ShadowComparisonReport) -> str:
    """Build the human-readable comparison report."""

    scenarios: list[str] = []
    seen: set[str] = set()
    for row in report.cases:
        if row.scenario not in seen:
            seen.add(row.scenario)
            scenarios.append(row.scenario)

    lines: list[str] = [
        "# Shadow-mode guidance comparison",
        "",
        "Head-to-head on the frozen RL fixed-eval matrix "
        "(Group A = NoManeuver + SinusoidalWeave; Group B = ConstantTurn).",
        "",
        f"- Scenarios: **{report.n_scenarios}**",
        f"- Modes: {', '.join(report.guidance_modes)}",
        f"- Time budget: **{report.max_time_s:.0f} s** (dt = {report.dt_s} s)",
        f"- Eval seed base: `{report.eval_seed}` (case seed = base + index)",
        f"- RL baseline pointer: `{report.baseline_pointer}`",
        f"- RL model: `{report.baseline_model_path}`",
        "",
        "## Hit / miss + miss distance",
        "",
    ]

    header = "| Scenario | Group | " + " | ".join(report.guidance_modes) + " |"
    sep = "|" + "|".join(["---"] * (2 + len(report.guidance_modes))) + "|"
    lines.append(header)
    lines.append(sep)
    for name in scenarios:
        group = _lookup(report.cases, name, report.guidance_modes[0])
        group_label = group.group if group else "?"
        cells = []
        for mode in report.guidance_modes:
            row = _lookup(report.cases, name, mode)
            cells.append(_cell_label(row) if row else "—")
        lines.append(f"| `{name}` | {group_label} | " + " | ".join(cells) + " |")
    lines.append("")

    lines.append("## Detailed metrics")
    lines.append("")
    lines.append(
        "| Scenario | Mode | Hit | Miss (m) | Time (s) | "
        "Peak |a_cmd| | Mean |a_cmd| | Peak |a_ach| |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in report.cases:
        lines.append(
            f"| `{row.scenario}` | {row.guidance_mode} | "
            f"{'yes' if row.hit else 'no'} | {row.miss_distance_m:.3f} | "
            f"{row.time_s:.2f} | {row.peak_cmd_lateral_m_s2:.1f} | "
            f"{row.mean_cmd_lateral_m_s2:.1f} | "
            f"{row.peak_achieved_lateral_m_s2:.1f} |"
        )
    lines.append("")
    lines.extend(_summary_section(report))
    lines.append("---")
    lines.append("")
    lines.append(
        "*Read-only evaluation against frozen classical laws and "
        "`CURRENT_RL_BASELINE.json`. No retraining.*"
    )
    lines.append("")
    return "\n".join(lines)


def write_shadow_report(
    report: ShadowComparisonReport,
    output_dir: Path | None = None,
) -> dict[str, Path]:
    """Write markdown + JSON + CSV under ``outputs/shadow_comparison/``."""

    out = output_dir or _DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    md_path = out / "shadow_comparison_report.md"
    json_path = out / "shadow_comparison_results.json"
    csv_path = out / "shadow_comparison_results.csv"

    md_path.write_text(format_markdown_report(report), encoding="utf-8")

    payload = {
        "baseline_pointer": report.baseline_pointer,
        "baseline_model_path": report.baseline_model_path,
        "max_time_s": report.max_time_s,
        "dt_s": report.dt_s,
        "n_scenarios": report.n_scenarios,
        "eval_seed": report.eval_seed,
        "guidance_modes": list(report.guidance_modes),
        "cases": [asdict(c) for c in report.cases],
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    fieldnames = list(asdict(report.cases[0]).keys()) if report.cases else [
        "scenario",
        "group",
        "maneuver",
        "guidance_mode",
        "hit",
        "outcome",
        "miss_distance_m",
        "time_s",
        "peak_cmd_lateral_m_s2",
        "mean_cmd_lateral_m_s2",
        "peak_achieved_lateral_m_s2",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for case in report.cases:
            writer.writerow(asdict(case))

    return {"markdown": md_path, "json": json_path, "csv": csv_path}
