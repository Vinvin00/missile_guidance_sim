"""Continue training an existing checkpoint past the fixed 5-checkpoint budget.

The Phase-2 lineage (``train_rl.py``) is capped at exactly 5 checkpoints by
design. This script is for lineages, like a hardened domain-randomization
run, where more training is wanted after that budget: it loads the last
checkpoint, runs one more block of timesteps under the same sampler, saves
the next checkpoint number, and evaluates on the frozen 9-case set.

Example:
    python scripts/continue_training.py \\
        --output-dir outputs/hard_lineage --from-checkpoint 5 \\
        --domain-randomization
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import VecMonitor

from guidance_sim.rl.domain_randomization import (
    randomized_initial_conditions,
    randomized_maneuver_factory,
)
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.training import (
    ActionLayout,
    PPOTrainingConfig,
    action_dimension,
    evaluate_policy,
)
import gymnasium as gym
import numpy as np
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.utils import set_random_seed


def build_vec_env(config: PPOTrainingConfig, checkpoint_index: int, domain_randomization: bool) -> VecMonitor:
    run_seed = config.seed + 10_000 * (checkpoint_index - 1)
    set_random_seed(run_seed)
    n_action = action_dimension(config.action_layout)
    if domain_randomization:
        sampler, maneuver = randomized_initial_conditions, randomized_maneuver_factory
    else:
        from guidance_sim.rl.training import training_initial_conditions, training_maneuver_factory
        sampler, maneuver = training_initial_conditions, training_maneuver_factory

    def make_env() -> gym.Env:
        env = InterceptionEnv(
            config=config.simulation_config(),
            reward_config=config.reward_config(),
            initial_condition_sampler=sampler,
            maneuver_factory=maneuver,
            action_layout=config.action_layout,
        )
        return gym.wrappers.RescaleAction(
            env,
            min_action=np.full(n_action, -1.0, dtype=np.float32),
            max_action=np.full(n_action, 1.0, dtype=np.float32),
        )

    vec_env = DummyVecEnv([make_env for _ in range(config.n_envs)])
    vec_env.seed(run_seed)
    return VecMonitor(vec_env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--from-checkpoint", type=int, required=True, help="checkpoint number to resume from")
    parser.add_argument("--timesteps", type=int, default=20_480)
    parser.add_argument("--domain-randomization", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    overrides: dict = {"timesteps_per_checkpoint": args.timesteps}
    if args.seed is not None:
        overrides["seed"] = args.seed
    config = PPOTrainingConfig(**overrides)
    checkpoint_dir = args.output_dir / "checkpoints"
    previous_path = checkpoint_dir / f"rl_checkpoint_{args.from_checkpoint:02d}.zip"
    next_index = args.from_checkpoint + 1
    next_path = checkpoint_dir / f"rl_checkpoint_{next_index:02d}.zip"
    if next_path.exists():
        raise FileExistsError(f"refusing to overwrite {next_path}")
    if not previous_path.exists():
        raise FileNotFoundError(previous_path)

    vec_env = build_vec_env(config, next_index, args.domain_randomization)
    model = RecurrentPPO.load(previous_path, env=vec_env, device="cpu")
    model.set_random_seed(config.seed + 10_000 * (next_index - 1))
    model.learn(total_timesteps=args.timesteps, reset_num_timesteps=False)
    model.save(next_path)
    vec_env.close()

    evaluation = evaluate_policy(model, action_layout=config.action_layout)
    print(f"Checkpoint {next_index} saved: {next_path}")
    print(
        f"Fixed eval: {evaluation.n_hits}/{evaluation.n_cases} hits "
        f"({100.0 * evaluation.hit_rate:.1f}%)"
    )
    print(
        "Mean/median miss distance: "
        f"{evaluation.mean_miss_distance_m:.3f} / {evaluation.median_miss_distance_m:.3f} m"
    )


if __name__ == "__main__":
    main()
