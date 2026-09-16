#!/usr/bin/env python3
"""Re-evaluate a trained checkpoint on a larger held-out set than the 50
cases used during training/checkpoint selection.

`build_held_out_cases(n_cases=N)` is a deterministic extension of the same
seed stream (seed_base + 100*index), so cases 0-49 are identical to the
50-case set used throughout the CP1-CP6 lineage and cases 50-(N-1) are new,
never seen during checkpoint selection -- this is the natural way to get
more statistical power without touching the original reference set.

Usage:
    python scripts/eval_checkpoint_large_heldout.py \
        --model outputs/evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_06.zip \
        --cases 300 --output outputs/evasive_largeeval_300/seed3_cp6.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sb3_contrib import RecurrentPPO

from guidance_sim.rl.evasive_scenarios import build_held_out_cases
from guidance_sim.rl.training import (
    _jsonable_evaluation,
    evaluate_policy,
    evasive_redesign_config,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--cases", type=int, default=300)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = evasive_redesign_config()
    model = RecurrentPPO.load(args.model, device="cpu")
    cases = build_held_out_cases(args.cases)
    evaluation = evaluate_policy(
        model,
        cases=cases,
        simulation_config=config.simulation_config(),
        action_layout=config.action_layout,
        use_target_turn_rate_obs=config.use_target_turn_rate_obs,
        tracking=config.tracking,
        reward_config=config.reward_config(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(_jsonable_evaluation(evaluation), indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"{args.model}: {evaluation.n_hits}/{evaluation.n_cases} hits "
        f"({evaluation.hit_rate * 100:.1f}%), median miss "
        f"{evaluation.median_miss_distance_m:.1f} m -> {args.output}"
    )


if __name__ == "__main__":
    main()
