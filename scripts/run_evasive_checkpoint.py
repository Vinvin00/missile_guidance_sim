#!/usr/bin/env python3
"""Run one checkpoint of the evasive + delayed-tracking retrain lineage.

Isolated from every existing lineage: artifacts land under
``outputs/evasive_delayed_tracking/`` and ``CURRENT_RL_BASELINE.json`` is not
touched. Promotion, if it ever happens, is a separate explicitly-logged step.

This is a from-scratch retrain, not a fine-tune -- the observation contract
(12-D, with tracking staleness/uncertainty and without the privileged
turn-rate channel), the maneuver distribution, and the time budget all differ
from the frozen lineage, so no previous checkpoint is a valid initialization.

Usage:
    python scripts/run_evasive_checkpoint.py --checkpoint 1
"""

from __future__ import annotations

import argparse
from pathlib import Path

from guidance_sim.rl.training import evasive_redesign_config, run_checkpoint

DEFAULT_OUTPUT_DIR = Path("outputs/evasive_delayed_tracking")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    config = evasive_redesign_config()
    print(
        f"CP{args.checkpoint}: evasive lineage | "
        f"max_time={config.max_time:g}s t_go_max={config.reward_config().t_go_max_s:g}s | "
        f"tracking={config.tracking.enabled} | obs={len(config.observation_names)}-D"
    )
    report = run_checkpoint(
        args.checkpoint,
        output_dir=args.output_dir,
        config=config,
    )
    evaluation = report.evaluation
    print(
        f"\nCP{args.checkpoint} held-out: {evaluation.n_hits}/{evaluation.n_cases} hits "
        f"({evaluation.hit_rate * 100:.1f}%), mean miss {evaluation.mean_miss_distance_m:.1f} m, "
        f"mean reward {evaluation.mean_episode_reward:.2f}"
    )
    if report.convergence_warning:
        print("STOP CONDITION: no joint improvement -- review gate before continuing.")


if __name__ == "__main__":
    main()
