#!/usr/bin/env python3
"""Zero-shot transfer: frozen RL baseline (and information-matched PN) on the
held-out evasive set, point-mass plant vs 6-DOF pursuer.

No retraining and no edits to rl/environment.py (owned by feature/rl-training).
The pursuer swap happens right after `InterceptionEnv.reset`, exactly the
one-line swap docs/rl-interface-6dof.md hands off. The reset observation is
unaffected: the rigid body starts with the same world State.

Usage:
    python scripts/eval_6dof_transfer.py --law rl --plant 6dof --cases 300 \
        --output outputs/6dof_transfer/rl_6dof.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from guidance_sim.physics.entities import INTERCEPTOR_6DOF, RigidBodyEntity
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.evasive_scenarios import build_held_out_cases


def _patch_env_for_6dof() -> None:
    original_reset = InterceptionEnv.reset

    def reset(self, *args, **kwargs):
        observation, info = original_reset(self, *args, **kwargs)
        assert self._pursuer_vehicle == INTERCEPTOR_6DOF.vehicle, "env pursuer != 6-DOF interceptor airframe"
        self.pursuer = RigidBodyEntity.from_state(self.pursuer.state, INTERCEPTOR_6DOF, name=self.pursuer.name)
        return observation, info

    InterceptionEnv.reset = reset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--law", choices=("rl", "pn"), required=True)
    parser.add_argument("--plant", choices=("pointmass", "6dof"), required=True)
    parser.add_argument("--cases", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if args.plant == "6dof":
        _patch_env_for_6dof()

    started = time.time()
    if args.law == "rl":
        from sb3_contrib import RecurrentPPO

        from guidance_sim.rl.training import _jsonable_evaluation, evaluate_policy, evasive_redesign_config

        baseline = json.loads(Path("outputs/CURRENT_RL_BASELINE.json").read_text())
        config = evasive_redesign_config()
        model = RecurrentPPO.load(baseline["model_path"], device="cpu")
        evaluation = evaluate_policy(
            model,
            cases=build_held_out_cases(args.cases),
            simulation_config=config.simulation_config(),
            action_layout=config.action_layout,
            use_target_turn_rate_obs=config.use_target_turn_rate_obs,
            tracking=config.tracking,
            reward_config=config.reward_config(),
        )
        payload = _jsonable_evaluation(evaluation)
        rows = [{"maneuver": c.maneuver, "hit": c.hit, "miss_distance_m": c.miss_distance_m}
                for c in evaluation.cases]
    else:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from run_evasive_pn_baseline import run_baseline

        payload = run_baseline(args.cases, args.output.parent / f"_pn_{args.plant}")
        rows = payload["cases"]

    misses = np.array([r["miss_distance_m"] for r in rows])
    summary = {
        "law": args.law,
        "plant": args.plant,
        "n": len(rows),
        "hits": int(sum(r["hit"] for r in rows)),
        "median_miss_m": float(np.median(misses)),
        "p90_miss_m": float(np.percentile(misses, 90)),
        "max_miss_m": float(misses.max()),
        "by_maneuver": {},
        "wall_s": round(time.time() - started, 1),
    }
    for kind in sorted({r["maneuver"] for r in rows}):
        sub = [r for r in rows if r["maneuver"] == kind]
        summary["by_maneuver"][kind] = {
            "hits": int(sum(r["hit"] for r in sub)),
            "n": len(sub),
            "median_miss_m": float(np.median([r["miss_distance_m"] for r in sub])),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "rows": rows, "raw": payload}, indent=2, default=float) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
