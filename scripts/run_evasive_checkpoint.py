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
    parser.add_argument(
        "--miss-tanh-scale",
        type=float,
        default=None,
        help=(
            "Override the terminal miss-penalty scale (m). The lineage default "
            "of 3000 m leaves only 0.13 reward between a 9 m and a 5 m miss, "
            "which is where every checkpoint actually finishes."
        ),
    )
    parser.add_argument(
        "--shaping-gamma",
        type=float,
        default=None,
        help=(
            "Override the discount used inside the ZEM-potential shaping term "
            "(RewardConfig.shaping_gamma). The lineage default of 1.0 does not "
            "match PPO's own gamma=0.995, so a cycle that raises then lowers "
            "the potential can net positive discounted return without closing "
            "the engagement."
        ),
    )
    parser.add_argument(
        "--effort-weight",
        type=float,
        default=None,
        help=(
            "Override RewardConfig.effort_weight (default 5). Raise to penalize "
            "command-RMS runaway across checkpoints."
        ),
    )
    parser.add_argument(
        "--zem-t-go-max",
        type=float,
        default=None,
        help=(
            "Override the ZEM potential's lookahead cap in seconds (default "
            "10). The old default coupled this to max_time, so a heading "
            "wobble of a couple degrees could swing the extrapolated miss "
            "point by hundreds of metres whenever closing velocity was near "
            "zero -- a free reward signal unrelated to actually closing."
        ),
    )
    parser.add_argument(
        "--n-envs",
        type=int,
        default=None,
        help="Override PPOTrainingConfig.n_envs (default 4). Lower under memory pressure.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override PPOTrainingConfig.seed, for a second seed of the same config.",
    )
    args = parser.parse_args()

    overrides: dict[str, object] = {}
    if args.miss_tanh_scale is not None:
        overrides["miss_tanh_scale_m"] = args.miss_tanh_scale
    if args.shaping_gamma is not None:
        overrides["shaping_gamma"] = args.shaping_gamma
    if args.effort_weight is not None:
        overrides["effort_weight"] = args.effort_weight
    if args.zem_t_go_max is not None:
        overrides["zem_t_go_max_s"] = args.zem_t_go_max
    if args.seed is not None:
        overrides["seed"] = args.seed
    if args.n_envs is not None:
        overrides["n_envs"] = args.n_envs
    config = evasive_redesign_config(**overrides)
    print(
        f"CP{args.checkpoint}: evasive lineage | "
        f"max_time={config.max_time:g}s t_go_max={config.reward_config().t_go_max_s:g}s | "
        f"tracking={config.tracking.enabled} | obs={len(config.observation_names)}-D | "
        f"miss_tanh_scale={config.miss_tanh_scale_m:g}m shaping_gamma={config.shaping_gamma:g} "
        f"effort_weight={config.effort_weight:g} "
        f"-> out={args.output_dir}"
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
