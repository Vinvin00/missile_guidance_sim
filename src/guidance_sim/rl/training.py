"""Checkpointed recurrent-PPO training and fixed-set evaluation.

The five checkpoints are separate invocations by design.  ``run_checkpoint``
trains exactly one fifth of the fixed 102,400-step budget, saves a new model,
evaluates it on the same nine deterministic engagements, updates the training
curve, and exits.  A later checkpoint resumes from the preceding model without
overwriting any artifact.

The public ``InterceptionEnv`` action remains a physical world-frame command
bounded at 25 g.  PPO sees a standard ``[-1, 1]^3`` wrapper which linearly
maps each component to that physical bound; the environment still applies its
radial norm limit and the existing lag/aerodynamic/structural clamps.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any, Protocol, Sequence

import gymnasium as gym
import numpy as np
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.utils import set_random_seed
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import (
    ConstantTurn,
    ManeuverProfile,
    NoManeuver,
    SinusoidalWeave,
)
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.simulation.engine import SimulationConfig


@dataclass(frozen=True)
class PPOTrainingConfig:
    """Compute-bounded recurrent-PPO configuration for all five checkpoints."""

    total_checkpoints: int = 5
    timesteps_per_checkpoint: int = 20_480
    n_envs: int = 4
    seed: int = 20_260_909
    dt: float = 0.02
    max_time: float = 25.0
    intercept_radius: float = 5.0
    autopilot_tau: float = 0.2
    learning_rate: float = 3.0e-4
    n_steps: int = 512
    batch_size: int = 256
    n_epochs: int = 5
    gamma: float = 0.995
    gae_lambda: float = 0.95
    ent_coef: float = 1.0e-3
    lstm_hidden_size: int = 64

    def __post_init__(self) -> None:
        if self.total_checkpoints != 5:
            raise ValueError("Phase 2 requires exactly five checkpoints")
        if self.timesteps_per_checkpoint <= 0 or self.n_envs <= 0:
            raise ValueError("training timesteps and environment count must be positive")
        rollout_size = self.n_steps * self.n_envs
        if self.timesteps_per_checkpoint % rollout_size:
            raise ValueError(
                "timesteps_per_checkpoint must be divisible by n_steps * n_envs"
            )
        if rollout_size % self.batch_size:
            raise ValueError("batch_size must divide n_steps * n_envs")
        if self.dt <= 0.0 or self.max_time <= 0.0:
            raise ValueError("simulation dt and max_time must be positive")

    @property
    def total_timesteps(self) -> int:
        return self.total_checkpoints * self.timesteps_per_checkpoint

    def simulation_config(self) -> SimulationConfig:
        return SimulationConfig(
            dt=self.dt,
            max_time=self.max_time,
            intercept_radius=self.intercept_radius,
            autopilot_tau=self.autopilot_tau,
        )


@dataclass(frozen=True)
class EvaluationCase:
    """One immutable member of the fixed Phase-2 evaluation set."""

    name: str
    target_position_m: tuple[float, float, float]
    target_velocity_m_s: tuple[float, float, float]
    maneuver: str
    maneuver_accel_g: float = 0.0
    frequency_hz: float = 0.0
    phase_rad: float = 0.0


FIXED_EVALUATION_CASES: tuple[EvaluationCase, ...] = (
    EvaluationCase(
        "no_maneuver_center",
        (6_500.0, 0.0, 3_200.0),
        (-190.0, 0.0, 0.0),
        "none",
    ),
    EvaluationCase(
        "no_maneuver_demo",
        (7_000.0, 400.0, 3_300.0),
        (-200.0, 0.0, 0.0),
        "none",
    ),
    EvaluationCase(
        "no_maneuver_offset",
        (7_800.0, -800.0, 3_500.0),
        (-210.0, 0.0, 0.0),
        "none",
    ),
    EvaluationCase(
        "constant_turn_left_3g",
        (6_500.0, 300.0, 3_200.0),
        (-190.0, 0.0, 0.0),
        "constant_turn",
        maneuver_accel_g=3.0,
    ),
    EvaluationCase(
        "constant_turn_right_5g",
        (7_000.0, -400.0, 3_300.0),
        (-200.0, 0.0, 0.0),
        "constant_turn",
        maneuver_accel_g=-5.0,
    ),
    EvaluationCase(
        "constant_turn_left_7g",
        (7_800.0, 700.0, 3_500.0),
        (-210.0, 0.0, 0.0),
        "constant_turn",
        maneuver_accel_g=7.0,
    ),
    EvaluationCase(
        "weave_3g_055hz",
        (6_500.0, -300.0, 3_200.0),
        (-190.0, 0.0, 0.0),
        "weave",
        maneuver_accel_g=3.0,
        frequency_hz=0.55,
        phase_rad=0.0,
    ),
    EvaluationCase(
        "weave_5g_070hz",
        (7_000.0, 400.0, 3_300.0),
        (-200.0, 0.0, 0.0),
        "weave",
        maneuver_accel_g=5.0,
        frequency_hz=0.70,
        phase_rad=np.pi / 3.0,
    ),
    EvaluationCase(
        "weave_7g_090hz",
        (7_800.0, -700.0, 3_500.0),
        (-210.0, 0.0, 0.0),
        "weave",
        maneuver_accel_g=7.0,
        frequency_hz=0.90,
        phase_rad=2.0 * np.pi / 3.0,
    ),
)


@dataclass(frozen=True)
class CaseEvaluation:
    name: str
    maneuver: str
    hit: bool
    outcome: str
    miss_distance_m: float
    episode_reward: float
    final_time_s: float
    control_effort_m2_s3: float


@dataclass(frozen=True)
class EvaluationSummary:
    n_cases: int
    n_hits: int
    hit_rate: float
    mean_miss_distance_m: float
    median_miss_distance_m: float
    mean_episode_reward: float
    mean_control_effort_m2_s3: float
    cases: tuple[CaseEvaluation, ...]


@dataclass(frozen=True)
class CurveSummary:
    checkpoint_episodes: int
    total_episodes: int
    first_quintile_mean_reward: float | None
    last_quintile_mean_reward: float | None
    reward_change: float | None
    best_episode_reward: float | None


@dataclass(frozen=True)
class CheckpointReport:
    checkpoint_index: int
    checkpoint_path: Path
    cumulative_timesteps: int
    curve_path: Path
    episode_csv_path: Path
    evaluation_path: Path
    progress_path: Path
    curve: CurveSummary
    evaluation: EvaluationSummary
    convergence_warning: bool


class PredictPolicy(Protocol):
    def predict(
        self,
        observation: np.ndarray,
        *,
        state: Any = None,
        episode_start: np.ndarray | None = None,
        deterministic: bool = True,
    ) -> tuple[np.ndarray, Any]: ...


def training_initial_conditions(
    rng: np.random.Generator,
) -> tuple[State, State]:
    """Seeded variations around the established demo/envelope IC family."""

    target_range_m = float(rng.uniform(6_000.0, 8_000.0))
    lateral_offset_m = float(rng.uniform(-800.0, 800.0))
    target_altitude_m = float(rng.uniform(3_100.0, 3_500.0))
    target_speed_m_s = float(rng.uniform(180.0, 220.0))
    heading_error_rad = float(np.deg2rad(rng.uniform(-2.0, 2.0)))
    pursuer_speed_m_s = 350.0
    return (
        State(
            position=[0.0, 0.0, 3_000.0],
            velocity=[
                pursuer_speed_m_s * np.cos(heading_error_rad),
                pursuer_speed_m_s * np.sin(heading_error_rad),
                0.0,
            ],
        ),
        State(
            position=[target_range_m, lateral_offset_m, target_altitude_m],
            velocity=[-target_speed_m_s, 0.0, 0.0],
        ),
    )


def training_maneuver_factory(rng: np.random.Generator) -> ManeuverProfile:
    """Equal seeded mix of no maneuver, constant turn, and 0.5--1 Hz weave."""

    profile_index = int(rng.integers(0, 3))
    if profile_index == 0:
        return NoManeuver()

    magnitude_m_s2 = float(rng.uniform(3.0, 7.0) * G0)
    if profile_index == 1:
        turn_sign = -1.0 if float(rng.random()) < 0.5 else 1.0
        return ConstantTurn(accel=turn_sign * magnitude_m_s2)

    return SinusoidalWeave(
        amplitude=magnitude_m_s2,
        frequency_hz=float(rng.uniform(0.5, 1.0)),
        phase=float(rng.uniform(0.0, 2.0 * np.pi)),
    )


def _case_initial_conditions(
    case: EvaluationCase,
):
    def sample(_rng: np.random.Generator) -> tuple[State, State]:
        return (
            State(
                position=[0.0, 0.0, 3_000.0],
                velocity=[350.0, 0.0, 0.0],
            ),
            State(
                position=case.target_position_m,
                velocity=case.target_velocity_m_s,
            ),
        )

    return sample


def _case_maneuver(case: EvaluationCase):
    def make(_rng: np.random.Generator) -> ManeuverProfile:
        if case.maneuver == "none":
            return NoManeuver()
        if case.maneuver == "constant_turn":
            return ConstantTurn(accel=case.maneuver_accel_g * G0)
        if case.maneuver == "weave":
            return SinusoidalWeave(
                amplitude=case.maneuver_accel_g * G0,
                frequency_hz=case.frequency_hz,
                phase=case.phase_rad,
            )
        raise ValueError(f"unsupported evaluation maneuver: {case.maneuver}")

    return make


def make_training_vec_env(
    config: PPOTrainingConfig,
    checkpoint_index: int,
) -> VecMonitor:
    """Construct fresh deterministic vector environments for one checkpoint."""

    run_seed = config.seed + 10_000 * (checkpoint_index - 1)
    set_random_seed(run_seed)

    def make_env() -> gym.Env:
        physical_env = InterceptionEnv(
            config=config.simulation_config(),
            initial_condition_sampler=training_initial_conditions,
            maneuver_factory=training_maneuver_factory,
        )
        return gym.wrappers.RescaleAction(
            physical_env,
            min_action=np.full(3, -1.0, dtype=np.float32),
            max_action=np.full(3, 1.0, dtype=np.float32),
        )

    vec_env = DummyVecEnv([make_env for _ in range(config.n_envs)])
    vec_env.seed(run_seed)
    return VecMonitor(vec_env)


class EpisodeCSVCallback(BaseCallback):
    """Append completed episode returns without relying on TensorBoard."""

    fieldnames = (
        "checkpoint",
        "episode",
        "total_timesteps",
        "episode_reward",
        "episode_length",
        "outcome",
        "min_range_m",
        "final_time_s",
    )

    def __init__(self, path: Path, checkpoint_index: int) -> None:
        super().__init__(verbose=0)
        self.path = path
        self.checkpoint_index = checkpoint_index
        self.rows: list[dict[str, object]] = []
        self._episode_number = _count_csv_rows(path)

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", ())
        dones = self.locals.get("dones", ())
        for done, info in zip(dones, infos):
            episode = info.get("episode")
            if not bool(done) or not isinstance(episode, dict):
                continue
            self._episode_number += 1
            row: dict[str, object] = {
                "checkpoint": self.checkpoint_index,
                "episode": self._episode_number,
                "total_timesteps": self.num_timesteps,
                "episode_reward": float(episode["r"]),
                "episode_length": int(episode["l"]),
                "outcome": str(info.get("outcome", "unknown")),
                "min_range_m": float(info.get("min_range_m", np.nan)),
                "final_time_s": float(info.get("time_s", np.nan)),
            }
            self.rows.append(row)
            _append_csv_row(self.path, self.fieldnames, row)
        return True


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _append_csv_row(
    path: Path,
    fieldnames: Sequence[str],
    row: dict[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def evaluate_policy(
    model: PredictPolicy,
    *,
    cases: Sequence[EvaluationCase] = FIXED_EVALUATION_CASES,
    simulation_config: SimulationConfig | None = None,
    seed: int = 91_000,
) -> EvaluationSummary:
    """Evaluate a policy on the immutable, ordered scenario set."""

    config = simulation_config or PPOTrainingConfig().simulation_config()
    results: list[CaseEvaluation] = []
    for case_index, case in enumerate(cases):
        physical_env = InterceptionEnv(
            config=config,
            initial_condition_sampler=_case_initial_conditions(case),
            maneuver_factory=_case_maneuver(case),
        )
        env = gym.wrappers.RescaleAction(
            physical_env,
            min_action=np.full(3, -1.0, dtype=np.float32),
            max_action=np.full(3, 1.0, dtype=np.float32),
        )
        observation, info = env.reset(seed=seed + case_index)
        recurrent_state: Any = None
        episode_start = np.array([True], dtype=bool)
        episode_reward = 0.0
        control_effort = 0.0
        while True:
            action, recurrent_state = model.predict(
                observation,
                state=recurrent_state,
                episode_start=episode_start,
                deterministic=True,
            )
            action = np.asarray(action, dtype=float).reshape(-1, 3)[0]
            observation, reward, terminated, truncated, info = env.step(action)
            episode_reward += float(reward)
            commanded = np.asarray(info["action_commanded_m_s2"], dtype=float)
            control_effort += float(np.dot(commanded, commanded) * config.dt)
            episode_start[:] = False
            if terminated or truncated:
                break
        results.append(
            CaseEvaluation(
                name=case.name,
                maneuver=case.maneuver,
                hit=bool(info["hit"]),
                outcome=str(info["outcome"]),
                miss_distance_m=float(info["min_range_m"]),
                episode_reward=episode_reward,
                final_time_s=float(info["time_s"]),
                control_effort_m2_s3=control_effort,
            )
        )
        env.close()

    miss_distances = np.array([result.miss_distance_m for result in results])
    rewards = np.array([result.episode_reward for result in results])
    efforts = np.array([result.control_effort_m2_s3 for result in results])
    n_hits = sum(result.hit for result in results)
    return EvaluationSummary(
        n_cases=len(results),
        n_hits=n_hits,
        hit_rate=float(n_hits / len(results)),
        mean_miss_distance_m=float(np.mean(miss_distances)),
        median_miss_distance_m=float(np.median(miss_distances)),
        mean_episode_reward=float(np.mean(rewards)),
        mean_control_effort_m2_s3=float(np.mean(efforts)),
        cases=tuple(results),
    )


def _curve_summary(
    checkpoint_rows: Sequence[dict[str, object]],
    total_episodes: int,
) -> CurveSummary:
    rewards = np.array(
        [float(row["episode_reward"]) for row in checkpoint_rows],
        dtype=float,
    )
    if rewards.size == 0:
        return CurveSummary(0, total_episodes, None, None, None, None)
    quintile_size = max(1, rewards.size // 5)
    first = float(np.mean(rewards[:quintile_size]))
    last = float(np.mean(rewards[-quintile_size:]))
    return CurveSummary(
        checkpoint_episodes=int(rewards.size),
        total_episodes=total_episodes,
        first_quintile_mean_reward=first,
        last_quintile_mean_reward=last,
        reward_change=last - first,
        best_episode_reward=float(np.max(rewards)),
    )


def plot_training_curve(csv_path: Path, out_path: Path) -> None:
    """Write raw episode rewards plus a 20-episode moving average."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    episodes = np.array([int(row["episode"]) for row in rows])
    rewards = np.array([float(row["episode_reward"]) for row in rows])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(episodes, rewards, alpha=0.35, linewidth=1.0, label="episode reward")
    if rewards.size:
        window = min(20, rewards.size)
        moving = np.convolve(rewards, np.ones(window) / window, mode="valid")
        ax.plot(
            episodes[window - 1 :],
            moving,
            linewidth=2.0,
            label=f"{window}-episode mean",
        )
    ax.set_xlabel("Completed episode")
    ax.set_ylabel("Return")
    ax.set_title("Recurrent PPO training curve")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _jsonable_evaluation(summary: EvaluationSummary) -> dict[str, object]:
    payload = asdict(summary)
    payload["cases"] = [asdict(case) for case in summary.cases]
    return payload


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _previous_no_improvement_streak(
    output_dir: Path,
    checkpoint_index: int,
    current_reward: float | None,
) -> int:
    if checkpoint_index <= 1 or current_reward is None:
        return 0
    previous_path = output_dir / f"rl_checkpoint_{checkpoint_index - 1:02d}.json"
    if not previous_path.exists():
        return 0
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    previous_reward = previous["curve"]["last_quintile_mean_reward"]
    previous_streak = int(previous.get("no_improvement_streak", 0))
    if previous_reward is None:
        return 0
    threshold = max(1.0, 0.02 * abs(float(previous_reward)))
    improved = current_reward > float(previous_reward) + threshold
    return 0 if improved else previous_streak + 1


def _append_progress(
    path: Path,
    *,
    config: PPOTrainingConfig,
    report: CheckpointReport,
) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Phase 2 training progress\n\n"
            f"- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)\n"
            "- Policy action: normalized `[-1, 1]^3`, rescaled to the unchanged "
            "physical 25 g environment action before dynamics\n"
            f"- Fixed budget: {config.total_timesteps:,} timesteps in "
            f"{config.total_checkpoints} checkpoints of "
            f"{config.timesteps_per_checkpoint:,}\n"
            f"- Training seed: {config.seed}\n"
            f"- Fixed evaluation set: {len(FIXED_EVALUATION_CASES)} engagements "
            "(3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)\n\n",
            encoding="utf-8",
        )

    curve = report.curve
    evaluation = report.evaluation
    lines = [
        f"## Checkpoint {report.checkpoint_index}",
        "",
        f"- Cumulative timesteps: {report.cumulative_timesteps:,}",
        f"- Episodes completed this checkpoint: {curve.checkpoint_episodes}",
        f"- Episodes completed total: {curve.total_episodes}",
        (
            "- First/last quintile mean reward: "
            f"{curve.first_quintile_mean_reward:.6f} / "
            f"{curve.last_quintile_mean_reward:.6f}"
            if curve.first_quintile_mean_reward is not None
            and curve.last_quintile_mean_reward is not None
            else "- First/last quintile mean reward: unavailable"
        ),
        (
            f"- Within-checkpoint reward change: {curve.reward_change:+.6f}"
            if curve.reward_change is not None
            else "- Within-checkpoint reward change: unavailable"
        ),
        f"- Fixed-eval hit rate: {evaluation.n_hits}/{evaluation.n_cases} "
        f"({100.0 * evaluation.hit_rate:.1f}%)",
        f"- Fixed-eval mean/median miss distance: "
        f"{evaluation.mean_miss_distance_m:.3f} / "
        f"{evaluation.median_miss_distance_m:.3f} m",
        f"- Fixed-eval mean episode reward: {evaluation.mean_episode_reward:.6f}",
        f"- Possible convergence warning: {report.convergence_warning}",
        f"- Model: `{report.checkpoint_path.relative_to(path.parent.parent)}`",
        f"- Evaluation details: "
        f"`{report.evaluation_path.relative_to(path.parent.parent)}`",
        f"- Training curve: `{report.curve_path.relative_to(path.parent.parent)}`",
        "",
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def run_checkpoint(
    checkpoint_index: int,
    *,
    output_dir: Path | str = Path("outputs"),
    config: PPOTrainingConfig | None = None,
) -> CheckpointReport:
    """Train, save, evaluate, report, then return after one checkpoint."""

    config = config or PPOTrainingConfig()
    if not 1 <= checkpoint_index <= config.total_checkpoints:
        raise ValueError(
            f"checkpoint_index must be in [1, {config.total_checkpoints}]"
        )

    output_dir = Path(output_dir)
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_path = checkpoint_dir / f"rl_checkpoint_{checkpoint_index:02d}.zip"
    previous_path = checkpoint_dir / f"rl_checkpoint_{checkpoint_index - 1:02d}.zip"
    if checkpoint_path.exists():
        raise FileExistsError(f"refusing to overwrite {checkpoint_path}")
    if checkpoint_index > 1 and not previous_path.exists():
        raise FileNotFoundError(f"required preceding checkpoint is missing: {previous_path}")

    episode_csv_path = output_dir / "training_episodes.csv"
    curve_path = output_dir / "training_curve.png"
    evaluation_path = output_dir / f"rl_checkpoint_{checkpoint_index:02d}_eval.json"
    metadata_path = output_dir / f"rl_checkpoint_{checkpoint_index:02d}.json"
    progress_path = output_dir / "training_progress.md"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    vec_env = make_training_vec_env(config, checkpoint_index)
    callback = EpisodeCSVCallback(episode_csv_path, checkpoint_index)
    run_seed = config.seed + 10_000 * (checkpoint_index - 1)
    if checkpoint_index == 1:
        model = RecurrentPPO(
            "MlpLstmPolicy",
            vec_env,
            learning_rate=config.learning_rate,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            n_epochs=config.n_epochs,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            ent_coef=config.ent_coef,
            policy_kwargs={
                "lstm_hidden_size": config.lstm_hidden_size,
                "n_lstm_layers": 1,
                "net_arch": {"pi": [64, 64], "vf": [64, 64]},
            },
            seed=run_seed,
            device="cpu",
            verbose=1,
        )
        reset_num_timesteps = True
    else:
        model = RecurrentPPO.load(previous_path, env=vec_env, device="cpu")
        model.set_random_seed(run_seed)
        reset_num_timesteps = False

    try:
        model.learn(
            total_timesteps=config.timesteps_per_checkpoint,
            callback=callback,
            reset_num_timesteps=reset_num_timesteps,
            progress_bar=False,
        )
        model.save(checkpoint_path)
        cumulative_timesteps = int(model.num_timesteps)
    finally:
        vec_env.close()

    evaluation = evaluate_policy(
        model,
        simulation_config=config.simulation_config(),
    )
    total_episodes = _count_csv_rows(episode_csv_path)
    curve = _curve_summary(callback.rows, total_episodes)
    no_improvement_streak = _previous_no_improvement_streak(
        output_dir,
        checkpoint_index,
        curve.last_quintile_mean_reward,
    )
    # At checkpoint 2, one non-improving transition already represents two
    # consecutive checkpoint summaries with no reward improvement.
    convergence_warning = no_improvement_streak >= 1

    _write_json(evaluation_path, _jsonable_evaluation(evaluation))
    plot_training_curve(episode_csv_path, curve_path)
    report = CheckpointReport(
        checkpoint_index=checkpoint_index,
        checkpoint_path=checkpoint_path,
        cumulative_timesteps=cumulative_timesteps,
        curve_path=curve_path,
        episode_csv_path=episode_csv_path,
        evaluation_path=evaluation_path,
        progress_path=progress_path,
        curve=curve,
        evaluation=evaluation,
        convergence_warning=convergence_warning,
    )
    _write_json(
        metadata_path,
        {
            "checkpoint_index": checkpoint_index,
            "cumulative_timesteps": cumulative_timesteps,
            "config": asdict(config),
            "curve": asdict(curve),
            "evaluation": _jsonable_evaluation(evaluation),
            "no_improvement_streak": no_improvement_streak,
            "convergence_warning": convergence_warning,
            "versions": {
                "numpy": version("numpy"),
                "sb3-contrib": version("sb3-contrib"),
                "stable-baselines3": version("stable-baselines3"),
                "torch": version("torch"),
            },
        },
    )
    _append_progress(progress_path, config=config, report=report)
    return report
