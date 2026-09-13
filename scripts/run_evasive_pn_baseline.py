#!/usr/bin/env python3
"""Classical PN reference on the held-out evasive set, under delayed tracking.

Gives the evasive lineage the same thing the old lineage had: a classical
number to be judged against. PN consumes exactly the estimator output the
policy sees, so the comparison is information-matched rather than PN being
handed ground truth.

Writes ``outputs/evasive_delayed_tracking/pn_baseline.json``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.rl.actions import ACTION_LAYOUT_LATERAL2, world_to_lateral
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.evasive_scenarios import build_held_out_cases
from guidance_sim.rl.training import (
    _case_initial_conditions,
    _case_maneuver,
    evasive_redesign_config,
)

_PN_N = 4.0
_EVAL_SEED = 91_000


def run_baseline(n_cases: int, output_dir: Path) -> dict:
    config = evasive_redesign_config()
    cases = build_held_out_cases(n_cases)
    rows = []
    for index, case in enumerate(cases):
        env = InterceptionEnv(
            config=config.simulation_config(),
            reward_config=config.reward_config(),
            initial_condition_sampler=_case_initial_conditions(case),
            maneuver_factory=_case_maneuver(case),
            action_layout=ACTION_LAYOUT_LATERAL2,
            tracking=config.tracking,
        )
        law = ProportionalNavigation(navigation_constant=_PN_N)
        env.reset(seed=_EVAL_SEED + index)
        while True:
            command = law.compute_command(
                env.pursuer.state, env._tracked_target_state(), env.config.dt
            )
            action = world_to_lateral(command, env.pursuer.state.velocity)
            _obs, _reward, terminated, truncated, info = env.step(action)
            if terminated or truncated:
                break
        rows.append(
            {
                "name": case.name,
                "maneuver": case.maneuver,
                "hit": bool(info["hit"]),
                "outcome": str(info["outcome"]),
                "miss_distance_m": float(info["min_range_m"]),
                "final_time_s": float(info["time_s"]),
            }
        )
        env.close()

    by_kind: dict[str, dict] = {}
    for row in rows:
        bucket = by_kind.setdefault(
            row["maneuver"], {"n": 0, "hits": 0, "misses": []}
        )
        bucket["n"] += 1
        bucket["hits"] += int(row["hit"])
        bucket["misses"].append(row["miss_distance_m"])
    for bucket in by_kind.values():
        bucket["hit_rate"] = bucket["hits"] / bucket["n"]
        bucket["median_miss_m"] = float(np.median(bucket["misses"]))
        bucket["mean_miss_m"] = float(np.mean(bucket["misses"]))
        del bucket["misses"]

    misses = np.array([row["miss_distance_m"] for row in rows])
    payload = {
        "guidance": f"PN N={_PN_N}",
        "n_cases": len(rows),
        "max_time_s": config.max_time,
        "tracking_enabled": config.tracking.enabled,
        "eval_seed": _EVAL_SEED,
        "hit_rate": float(sum(r["hit"] for r in rows) / len(rows)),
        "mean_miss_m": float(np.mean(misses)),
        "median_miss_m": float(np.median(misses)),
        "by_maneuver": by_kind,
        "cases": rows,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "pn_baseline.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=50)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/evasive_delayed_tracking"),
    )
    args = parser.parse_args()

    payload = run_baseline(args.cases, args.output_dir)
    print(
        f"PN baseline: {payload['hit_rate'] * 100:.1f}% hits over "
        f"{payload['n_cases']} held-out cases; median miss "
        f"{payload['median_miss_m']:.1f} m"
    )
    for kind, bucket in sorted(payload["by_maneuver"].items()):
        print(
            f"  {kind:15s} {bucket['hits']:2d}/{bucket['n']:2d} hits  "
            f"median {bucket['median_miss_m']:8.1f} m"
        )


if __name__ == "__main__":
    main()
