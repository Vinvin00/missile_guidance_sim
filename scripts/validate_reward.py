"""Offline reward validation: replay classical laws and archived RL checkpoints.

No training.  Writes ``outputs/reward_redesign_validation.json`` and prints
the three gate results.  Exit status 1 if any gate fails.
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Callable

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.factories import classical_law_factories
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.maneuvers import ConstantTurn
from guidance_sim.rl.actions import ACTION_LAYOUT_WORLD3, world_to_lateral
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.reward import RewardConfig
from guidance_sim.rl.training import (
    FIXED_EVALUATION_CASES,
    PPOTrainingConfig,
    evaluate_policy,
)
from guidance_sim.simulation.engine import SimulationConfig

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
MARGIN = 10.0


def _rollout(
    env: InterceptionEnv,
    policy: Callable[[InterceptionEnv, dict[str, object]], np.ndarray],
    seed: int = 0,
) -> dict[str, float | str]:
    _, info = env.reset(seed=seed)
    total = 0.0
    shaping = 0.0
    effort = 0.0
    terminal = 0.0
    while True:
        action = policy(env, info)
        _, reward, terminated, truncated, info = env.step(action)
        total += float(reward)
        shaping += float(info["reward_terms"]["shaping"])
        effort += float(info["reward_terms"]["effort"])
        terminal += float(info["reward_terms"]["terminal"])
        if terminated or truncated:
            abs_sum = abs(shaping) + abs(effort) + abs(terminal)
            return {
                "total": total,
                "shaping": shaping,
                "effort": effort,
                "terminal": terminal,
                "legacy_episode_reward": float(info["legacy_episode_reward"]),
                "outcome": str(info["outcome"]),
                "min_range_m": float(info["min_range_m"]),
                "final_range_m": float(info["range_m"]),
                "final_time_s": float(info["time_s"]),
                "shaping_share": abs(shaping) / abs_sum if abs_sum else 0.0,
                "effort_share": abs(effort) / abs_sum if abs_sum else 0.0,
                "terminal_share": abs(terminal) / abs_sum if abs_sum else 0.0,
            }


def _guidance_policy(law_factory: Callable[[InterceptionEnv], GuidanceLaw]):
    holder: dict[str, GuidanceLaw | None] = {"law": None}

    def policy(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
        assert env.pursuer is not None and env.target is not None
        if holder["law"] is None:
            holder["law"] = law_factory(env)
        command = holder["law"].compute_command(
            env.pursuer.state, env.target.state, env.config.dt
        )
        if env.action_layout == "lateral2":
            return world_to_lateral(command, env.pursuer.state.velocity)
        return np.asarray(command, dtype=float).reshape(3)

    return policy


_CLASSICAL_FACTORIES = classical_law_factories(
    lambda env: env.target, pn_n=4.0, apn_n=4.0, ogl_n=3.0
)
_pn_factory = _CLASSICAL_FACTORIES["PN"]
_apn_factory = _CLASSICAL_FACTORIES["APN"]
_ogl_factory = _CLASSICAL_FACTORIES["OGL"]


def _classical_cases() -> list[dict[str, object]]:
    hit_config = SimulationConfig(dt=0.02, max_time=45.0, intercept_radius=5.0)
    timeout_config = SimulationConfig(dt=0.02, max_time=2.0, intercept_radius=5.0)
    turn_config = SimulationConfig(dt=0.02, max_time=25.0, intercept_radius=5.0)
    rows: list[dict[str, object]] = []
    laws = (
        ("PN", _pn_factory),
        ("APN", _apn_factory),
        ("OGL", _ogl_factory),
    )
    for name, factory in laws:
        hit_env = InterceptionEnv(config=hit_config)
        hit = _rollout(hit_env, _guidance_policy(factory), seed=0)
        hit["law"] = name
        hit["scenario"] = "demo_hit"
        rows.append(hit)

        timeout_env = InterceptionEnv(config=timeout_config)
        timeout = _rollout(timeout_env, _guidance_policy(factory), seed=0)
        timeout["law"] = name
        timeout["scenario"] = "demo_forced_timeout"
        rows.append(timeout)

        turn_env = InterceptionEnv(
            config=turn_config,
            maneuver_factory=lambda _rng: ConstantTurn(accel=5.0 * G0),
        )
        turn = _rollout(turn_env, _guidance_policy(factory), seed=0)
        turn["law"] = name
        turn["scenario"] = "constant_turn_5g"
        rows.append(turn)
    return rows


def _gate_classical(rows: list[dict[str, object]]) -> dict[str, object]:
    per_law: dict[str, dict[str, list[float]]] = {}
    for row in rows:
        law = str(row["law"])
        bucket = per_law.setdefault(law, {"hits": [], "misses": []})
        if row["outcome"] == "hit":
            bucket["hits"].append(float(row["total"]))
        else:
            bucket["misses"].append(float(row["total"]))
    details = {}
    passed = True
    for law, bucket in per_law.items():
        hit_mean = float(np.mean(bucket["hits"])) if bucket["hits"] else None
        miss_mean = float(np.mean(bucket["misses"])) if bucket["misses"] else None
        law_pass = (
            hit_mean is not None
            and miss_mean is not None
            and hit_mean > miss_mean + MARGIN
        )
        passed = passed and law_pass
        details[law] = {
            "hit_mean": hit_mean,
            "miss_mean": miss_mean,
            "n_hits": len(bucket["hits"]),
            "n_misses": len(bucket["misses"]),
            "passed": law_pass,
        }
    return {"passed": passed, "margin": MARGIN, "per_law": details}


def _zero_action(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
    return np.zeros(env.action_space.shape, dtype=float)


def _turn_away_policy(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
    assert env.pursuer is not None and env.target is not None
    los = env.target.state.position - env.pursuer.state.position
    lateral = world_to_lateral(los, env.pursuer.state.velocity)
    norm = float(np.linalg.norm(lateral))
    if norm < 1e-9:
        return np.array([env.action_limit_m_s2, 0.0])
    return (-lateral / norm) * env.action_limit_m_s2


def _gate_flyby_loiter() -> dict[str, object]:
    config = SimulationConfig(dt=0.02, max_time=25.0, intercept_radius=5.0)
    flyby = _rollout(InterceptionEnv(config=config), _zero_action, seed=1)
    loiter = _rollout(InterceptionEnv(config=config), _turn_away_policy, seed=1)
    passed = (
        flyby["outcome"] != "hit"
        and loiter["outcome"] != "hit"
        and float(flyby["min_range_m"]) < float(loiter["min_range_m"])
        and float(flyby["total"]) > float(loiter["total"]) + MARGIN
    )
    return {
        "passed": passed,
        "flyby": flyby,
        "loiter": loiter,
        "margin": MARGIN,
    }


def _checkpoint_path(index: int) -> Path:
    return CHECKPOINT_DIR / f"rl_checkpoint_{index:02d}.zip"


def _gate_checkpoints() -> dict[str, object]:
    from sb3_contrib import RecurrentPPO

    sim = PPOTrainingConfig().simulation_config()
    scores: dict[str, dict[str, object]] = {}
    for index in (2, 3, 4):
        path = _checkpoint_path(index)
        if not path.exists():
            return {"passed": False, "error": f"missing {path}"}
        model = RecurrentPPO.load(path, device="cpu")
        summary = evaluate_policy(
            model,
            cases=FIXED_EVALUATION_CASES,
            simulation_config=sim,
            action_layout=ACTION_LAYOUT_WORLD3,
        )
        scores[f"cp{index}"] = {
            "mean_episode_reward": summary.mean_episode_reward,
            "mean_legacy_episode_reward": summary.mean_legacy_episode_reward,
            "mean_progress_reward": summary.mean_progress_reward,
            "mean_effort_penalty": summary.mean_effort_penalty,
            "mean_terminal_reward": summary.mean_terminal_reward,
            "mean_miss_distance_m": summary.mean_miss_distance_m,
            "n_hits": summary.n_hits,
            "cases": [asdict(case) for case in summary.cases],
        }
    labels = ("cp2", "cp3", "cp4")
    rewards = np.array(
        [float(scores[label]["mean_episode_reward"]) for label in labels]
    )
    misses = np.array(
        [float(scores[label]["mean_miss_distance_m"]) for label in labels]
    )
    # Corrected criterion: reward ranking must match miss ranking
    # (higher return ↔ lower mean miss). Expected: CP3 best, CP2 middle, CP4 worst.
    order_by_reward = tuple(labels[i] for i in np.argsort(-rewards))
    order_by_miss = tuple(labels[i] for i in np.argsort(misses))
    expected_order = ("cp3", "cp2", "cp4")
    passed = order_by_reward == order_by_miss == expected_order
    return {
        "passed": passed,
        "criterion": (
            "new-reward ranking of CP2/CP3/CP4 must match mean-miss ranking "
            "(expected CP3 best, CP2 middle, CP4 worst); supersedes "
            "'CP3/CP4 clearly worse than CP2'"
        ),
        "order_by_reward_best_to_worst": list(order_by_reward),
        "order_by_miss_best_to_worst": list(order_by_miss),
        "expected_order_best_to_worst": list(expected_order),
        "mean_episode_rewards": {
            label: float(scores[label]["mean_episode_reward"]) for label in labels
        },
        "mean_miss_distances_m": {
            label: float(scores[label]["mean_miss_distance_m"]) for label in labels
        },
        "scores": scores,
    }


def _term_shares(rows: list[dict[str, object]]) -> dict[str, float]:
    shaping = np.array([abs(float(row["shaping"])) for row in rows])
    effort = np.array([abs(float(row["effort"])) for row in rows])
    terminal = np.array([abs(float(row["terminal"])) for row in rows])
    totals = shaping + effort + terminal
    totals = np.where(totals == 0.0, 1.0, totals)
    return {
        "mean_abs_shaping": float(np.mean(shaping)),
        "mean_abs_effort": float(np.mean(effort)),
        "mean_abs_terminal": float(np.mean(terminal)),
        "mean_shaping_share": float(np.mean(shaping / totals)),
        "mean_effort_share": float(np.mean(effort / totals)),
        "mean_terminal_share": float(np.mean(terminal / totals)),
    }


def main() -> int:
    reward_config = RewardConfig()
    classical = _classical_cases()
    gate1 = _gate_classical(classical)
    gate3 = _gate_flyby_loiter()
    gate2 = _gate_checkpoints()
    representative = classical + [gate3["flyby"], gate3["loiter"]]
    payload = {
        "reward_config": asdict(reward_config),
        "action_space": {
            "training_layout": "lateral2",
            "replay_layout_for_archived_policies": "world3",
            "touches_frozen_guidance_law": False,
        },
        "term_scale_calibration": _term_shares(representative),
        "weight_annealing_plan": {
            "applied": False,
            "until_hit_rate_below_0.10": {
                "shaping_weight": 50.0,
                "terminal_weight": 0.5,
            },
            "hit_rate_0.10_to_0.40": {
                "shaping_weight": 50.0,
                "terminal_weight": 1.0,
            },
            "hit_rate_above_0.40": {
                "shaping_weight": 15.0,
                "terminal_weight": 1.0,
            },
            "fallback_if_hit_rate_never_exceeds_0.10": {
                "trigger": (
                    "after two consecutive checkpoints with hit_rate < 0.10 and "
                    "no improvement in mean miss vs the previous checkpoint"
                ),
                "action": (
                    "keep shaping_weight=50; raise terminal_weight from 0.5 to 1.0 "
                    "so closest-approach credit is not permanently half-weighted; "
                    "do not drop shaping_weight"
                ),
                "rationale": (
                    "The <10% band currently only defines an early schedule and "
                    "never exits. Without a fallback the run would stay on "
                    "terminal_weight=0.5 indefinitely even if miss distance is "
                    "improving. Raising the terminal weight restores the calibrated "
                    "miss grading without weakening dense shaping while hits are rare."
                ),
            },
            "notes": (
                "Annealing is reported for review only and was not applied. "
                "This pass freezes shaping_weight=50, terminal_weight=1, "
                "shaping_gamma=1 (undiscounted PBRS telescope for logged returns). "
                "The fallback above is a proposal only."
            ),
        },
        "t_go_continuity": {
            "pre_fix_worst_jump": {
                "range_m": 500.0,
                "abs_d_phi": 0.010308,
                "abs_d_shaping": 0.5154,
                "note": (
                    "At Vc=1±ε with collinear geometry, t_go jumped 25s→5s. "
                    "Per-step shaping jump ~0.52 vs mean per-step shaping ~0.02 "
                    "on a ~25-unit episode — material for learning gradients."
                ),
            },
            "formulation": (
                "t_go = min(range / max(|Vc|, vc_min), t_go_max); "
                "no closing/receding branch"
            ),
        },
        "gates": {
            "classical_hit_above_miss": gate1,
            "reward_ranks_with_miss_distance": gate2,
            "flyby_above_loiter": gate3,
        },
        "classical_rows": classical,
        "all_gates_passed": bool(
            gate1["passed"] and gate2["passed"] and gate3["passed"]
        ),
    }
    out_path = OUTPUT_DIR / "reward_redesign_validation.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {out_path}")
    print(
        "Gate 1 classical hit > miss:",
        gate1["passed"],
        json.dumps(gate1["per_law"], sort_keys=True),
    )
    print(
        "Gate 2 reward ranks with miss:",
        gate2["passed"],
        {k: v for k, v in gate2.items() if k != "scores"},
    )
    print(
        "Gate 3 flyby > loiter:",
        gate3["passed"],
        f"flyby={gate3['flyby']['total']:.3f} loiter={gate3['loiter']['total']:.3f}",
    )
    print("Term shares:", json.dumps(payload["term_scale_calibration"], sort_keys=True))
    print("All gates passed:", payload["all_gates_passed"])
    return 0 if payload["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
