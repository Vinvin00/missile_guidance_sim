"""Train and evaluate exactly one Phase-2 recurrent-PPO checkpoint.

Examples:
    python scripts/train_rl.py --checkpoint 1
    python scripts/train_rl.py --checkpoint 2
    python scripts/train_rl.py --checkpoint 1 \\
        --output-dir outputs/observation_target_turn_rate \\
        --use-target-turn-rate-obs

Each invocation refuses to overwrite an existing checkpoint and exits after
writing the model, cumulative training curve, fixed-set evaluation, and
``training_progress.md`` under ``--output-dir``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guidance_sim.rl.training import PPOTrainingConfig, run_checkpoint


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--checkpoint",
        type=int,
        required=True,
        choices=range(1, 6),
        help="one-based checkpoint number; only this checkpoint will run",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "outputs",
    )
    parser.add_argument(
        "--use-target-turn-rate-obs",
        action="store_true",
        help=(
            "append target turn-rate channels (13-D obs). Start a fresh "
            "output-dir lineage; do not resume CP1–CP4 trained without it."
        ),
    )
    parser.add_argument(
        "--domain-randomization",
        action="store_true",
        help=(
            "train on closer starts, faster targets, and higher-g maneuvers "
            "(guidance_sim.rl.domain_randomization) instead of the frozen "
            "training distribution."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="override PPOTrainingConfig.seed, e.g. for a second training-seed run",
    )
    parser.add_argument(
        "--pursuer-plant",
        choices=("pointmass", "6dof"),
        default="pointmass",
        help=(
            "'6dof' trains against the rigid-body interceptor airframe "
            "(INTERCEPTOR_6DOF) instead of the point mass. Start a fresh "
            "output-dir lineage: the point-mass-trained checkpoints do not "
            "transfer (docs/rl-interface-6dof.md, 0/300 zero-shot)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    overrides: dict = {
        "use_target_turn_rate_obs": bool(args.use_target_turn_rate_obs),
        "domain_randomization": bool(args.domain_randomization),
        "pursuer_plant": args.pursuer_plant,
    }
    if args.seed is not None:
        overrides["seed"] = args.seed
    config = PPOTrainingConfig(**overrides)
    report = run_checkpoint(
        checkpoint_index=args.checkpoint,
        output_dir=args.output_dir,
        config=config,
    )
    evaluation = report.evaluation
    curve = report.curve
    print(f"Checkpoint {report.checkpoint_index} complete; training stopped.")
    print(f"Cumulative timesteps: {report.cumulative_timesteps:,}")
    print(f"use_target_turn_rate_obs: {config.use_target_turn_rate_obs}")
    print(f"pursuer_plant: {config.pursuer_plant}")
    print(f"Episodes this checkpoint: {curve.checkpoint_episodes}")
    if curve.first_quintile_mean_reward is not None:
        print(
            "First/last quintile mean reward: "
            f"{curve.first_quintile_mean_reward:.6f} / "
            f"{curve.last_quintile_mean_reward:.6f}"
        )
    print(
        f"Fixed eval: {evaluation.n_hits}/{evaluation.n_cases} hits "
        f"({100.0 * evaluation.hit_rate:.1f}%)"
    )
    print(
        "Mean/median miss distance: "
        f"{evaluation.mean_miss_distance_m:.3f} / "
        f"{evaluation.median_miss_distance_m:.3f} m"
    )
    print(
        "Group B (ConstantTurn) hits / mean miss: "
        f"{evaluation.group_b.n_hits}/{evaluation.group_b.n_cases} / "
        f"{evaluation.group_b.mean_miss_distance_m:.3f} m"
    )
    print(f"Model: {report.checkpoint_path}")
    print(f"Training curve: {report.curve_path}")
    print(f"Progress log: {report.progress_path}")
    if report.convergence_warning:
        print(
            "WARNING: Group A (NoManeuver+Weave) has not improved across "
            "two checkpoints."
        )


if __name__ == "__main__":
    main()
