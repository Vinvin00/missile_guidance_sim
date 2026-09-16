#!/usr/bin/env python3
"""Capture one RL baseline evaluation episode into a viz-ready JSON rollout.

Run with the *training* worktree interpreter and package path so this script
never edits RL training code:

  cd ../missile_guidance_sim
  .venv/bin/python ../missile-sim-viz/scripts/capture_rl_rollout.py

Writes under missile-sim-viz/outputs/rl_rollouts/. Default case is the
confirmed Group A hit ``no_maneuver_demo`` from CURRENT_RL_BASELINE.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import torch
from sb3_contrib import RecurrentPPO

# Must match guidance_sim.ml.policy_inference.FrozenPolicy: multi-threaded CPU
# matmul reduction order isn't fixed across process launches, so this golden
# capture and the live serving path must both pin 1 thread or they silently
# diverge after enough recurrent steps (confirmed empirically -- see
# NOTES.md 2026-09-16).
torch.set_num_threads(1)

from guidance_sim.rl.actions import ACTION_LAYOUT_LATERAL2, action_dimension
from guidance_sim.rl.environment import InterceptionEnv, TrackingConfig
from guidance_sim.rl.training import (
    FIXED_EVALUATION_CASES,
    PPOTrainingConfig,
    _case_initial_conditions,
    _case_maneuver,
)

VIZ_ROOT = Path(__file__).resolve().parents[1]
TRAINING_ROOT = VIZ_ROOT.parent / "missile_guidance_sim"
DEFAULT_OUT_DIR = VIZ_ROOT / "outputs" / "rl_rollouts"


def _vec3(values: np.ndarray) -> dict[str, float]:
    arr = np.asarray(values, dtype=float).reshape(3)
    return {"x": float(arr[0]), "y": float(arr[1]), "z": float(arr[2])}


def _body(position: np.ndarray, velocity: np.ndarray) -> dict[str, Any]:
    return {
        "position_m": _vec3(position),
        "velocity_m_s": _vec3(velocity),
    }


def _load_baseline_pointer(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def capture_case(
    *,
    case_name: str,
    model_path: Path,
    use_target_turn_rate_obs: bool,
    tracking_enabled: bool,
    max_time_s: float,
    action_layout: str,
    seed: int,
) -> dict[str, Any]:
    case = next(c for c in FIXED_EVALUATION_CASES if c.name == case_name)
    case_index = next(
        i for i, c in enumerate(FIXED_EVALUATION_CASES) if c.name == case_name
    )
    config = PPOTrainingConfig(
        action_layout=action_layout,  # type: ignore[arg-type]
        use_target_turn_rate_obs=use_target_turn_rate_obs,
        max_time=max_time_s,
    ).simulation_config()
    n_action = action_dimension(action_layout)  # type: ignore[arg-type]

    physical_env = InterceptionEnv(
        config=config,
        initial_condition_sampler=_case_initial_conditions(case),
        maneuver_factory=_case_maneuver(case),
        action_layout=action_layout,  # type: ignore[arg-type]
        use_target_turn_rate_obs=use_target_turn_rate_obs,
        tracking=TrackingConfig(enabled=tracking_enabled),
    )
    env = gym.wrappers.RescaleAction(
        physical_env,
        min_action=np.full(n_action, -1.0, dtype=np.float32),
        max_action=np.full(n_action, 1.0, dtype=np.float32),
    )
    model = RecurrentPPO.load(str(model_path), device="cpu")

    observation, info = env.reset(seed=seed + case_index)
    assert physical_env.pursuer is not None and physical_env.target is not None

    frames: list[dict[str, Any]] = [
        {
            "time_s": 0.0,
            "pursuer": _body(
                physical_env.pursuer.state.position,
                physical_env.pursuer.state.velocity,
            ),
            "target": _body(
                physical_env.target.state.position,
                physical_env.target.state.velocity,
            ),
            "range_m": float(info["range_m"]),
            "pursuer_accel_cmd_m_s2": _vec3(np.zeros(3)),
            "pursuer_accel_achieved_m_s2": _vec3(np.zeros(3)),
        }
    ]

    recurrent_state: Any = None
    episode_start = np.array([True], dtype=bool)
    last_info = info
    while True:
        action, recurrent_state = model.predict(
            observation,
            state=recurrent_state,
            episode_start=episode_start,
            deterministic=True,
        )
        action = np.asarray(action, dtype=float).reshape(-1, n_action)[0]
        observation, _reward, terminated, truncated, info = env.step(action)
        last_info = info
        frames.append(
            {
                "time_s": float(info["time_s"]),
                "pursuer": _body(
                    physical_env.pursuer.state.position,
                    physical_env.pursuer.state.velocity,
                ),
                "target": _body(
                    physical_env.target.state.position,
                    physical_env.target.state.velocity,
                ),
                "range_m": float(info["range_m"]),
                "pursuer_accel_cmd_m_s2": _vec3(info["action_commanded_m_s2"]),
                "pursuer_accel_achieved_m_s2": _vec3(
                    info["action_achieved_m_s2"]
                ),
            }
        )
        episode_start[:] = False
        if terminated or truncated:
            break

    # Match SimulationResult intercept convention: no command after hit.
    if bool(last_info.get("hit")):
        frames[-1]["pursuer_accel_cmd_m_s2"] = _vec3(np.zeros(3))
        frames[-1]["pursuer_accel_achieved_m_s2"] = _vec3(np.zeros(3))

    env.close()
    return {
        "schema_version": 1,
        "case_name": case.name,
        "maneuver": case.maneuver,
        "group": "A" if case.maneuver in {"none", "weave"} else "B",
        "hit": bool(last_info["hit"]),
        "outcome": str(last_info["outcome"]),
        "closest_approach_m": float(last_info["min_range_m"]),
        "final_time_s": float(last_info["time_s"]),
        "dt_s": float(config.dt),
        "frame_count": len(frames),
        "frames": frames,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        default="no_maneuver_demo",
        help="FIXED_EVALUATION_CASES name (default: no_maneuver_demo)",
    )
    parser.add_argument(
        "--training-root",
        type=Path,
        default=TRAINING_ROOT,
        help="Path to missile_guidance_sim worktree (read-only)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="Directory for captured rollout JSON",
    )
    args = parser.parse_args()

    baseline_path = args.training_root / "outputs" / "CURRENT_RL_BASELINE.json"
    baseline = _load_baseline_pointer(baseline_path)
    model_path = args.training_root / baseline["model_path"]
    if not model_path.is_file():
        raise FileNotFoundError(f"checkpoint not found: {model_path}")

    rollout = capture_case(
        case_name=args.case,
        model_path=model_path,
        use_target_turn_rate_obs=bool(baseline["use_target_turn_rate_obs"]),
        tracking_enabled=bool(baseline.get("tracking_enabled", False)),
        max_time_s=float(baseline.get("max_time_s", 25.0)),
        action_layout=str(baseline.get("action_layout", ACTION_LAYOUT_LATERAL2)),
        seed=91_000,
    )
    rollout["baseline"] = {
        "pointer": str(baseline_path.resolve()),
        "model_path": str(model_path.resolve()),
        "branch_name": baseline.get("branch_name"),
        "observation_dim": baseline.get("observation_dim"),
        "use_target_turn_rate_obs": baseline.get("use_target_turn_rate_obs"),
        "tracking_enabled": baseline.get("tracking_enabled", False),
        "cumulative_timesteps": baseline.get("cumulative_timesteps"),
    }

    if not rollout["hit"]:
        raise SystemExit(
            f"refusing to write non-hit rollout for {args.case}: "
            f"outcome={rollout['outcome']} miss={rollout['closest_approach_m']:.3f} m"
        )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{args.case}.json"
    out_path.write_text(json.dumps(rollout, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {out_path}  frames={rollout['frame_count']}  "
        f"miss={rollout['closest_approach_m']:.3f} m  hit={rollout['hit']}"
    )


if __name__ == "__main__":
    main()
