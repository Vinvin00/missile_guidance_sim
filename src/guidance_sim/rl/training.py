"""Checkpointed recurrent-PPO training and fixed-set evaluation.

The five checkpoints are separate invocations by design.  ``run_checkpoint``
trains exactly one fifth of the fixed 102,400-step budget, saves a new model,
evaluates it on the same nine deterministic engagements, updates the training
curve, and exits.  A later checkpoint resumes from the preceding model without
overwriting any artifact.

The public ``InterceptionEnv`` action defaults to a two-component lateral
command in the velocity-normal plane, boxed at 25 g per component and then
radially clipped in world axes.  PPO sees ``[-1, 1]^2``.  Archived
three-component policies replay through ``action_layout="world3"``.  Domain
randomization exists but is off by default so the first retrain stays on
the frozen training distribution.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from importlib.metadata import version
import json
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, Sequence

import gymnasium as gym
import numpy as np
import torch
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
from guidance_sim.rl.actions import (
    ACTION_LAYOUT_LATERAL2,
    ActionLayout,
    action_dimension,
)
from guidance_sim.rl.domain_randomization import (
    randomized_initial_conditions,
    randomized_maneuver_factory,
)
from guidance_sim.rl.environment import (
    InterceptionEnv,
    TrackingConfig,
    observation_names,
)
from guidance_sim.rl.evasive_scenarios import (
    build_held_out_cases,
    evasive_initial_conditions,
    evasive_maneuver_factory,
)
from guidance_sim.rl.reward import RewardConfig
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
    domain_randomization: bool = False
    action_layout: ActionLayout = ACTION_LAYOUT_LATERAL2
    # "pointmass" (default) preserves every existing lineage bit-identical.
    # "6dof" swaps the pursuer for the rigid-body airframe (INTERCEPTOR_6DOF)
    # per docs/rl-interface-6dof.md's retraining recommendation -- the point
    # mass this policy was trained on has zero-shot transfer to it (0/300).
    pursuer_plant: Literal["pointmass", "6dof"] = "pointmass"
    # Off by default: preserves CP1–CP4 obs contract. New experiment branch only.
    use_target_turn_rate_obs: bool = False
    # Evasive-redesign lineage: real evasion maneuvers + delayed/estimated
    # tracking. Off by default so the frozen lineage above is untouched;
    # `evasive_redesign_config()` turns both on together.
    use_evasive_maneuvers: bool = False
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    # Miss-penalty grading scale. The terminal penalty is
    # miss_penalty * tanh(min_range / scale), so beyond ~3x the scale it is
    # flat and supplies no gradient at all.
    miss_tanh_scale_m: float = 1_000.0
    # Discount applied inside the ZEM-potential shaping term. Ng et al.
    # (1999) potential-based shaping is policy-invariant only when this
    # equals the agent's own discount (`gamma` above); left at the
    # RewardConfig default of 1.0 it does not, and the mismatch lets a
    # cycle that raises then lowers the potential net positive discounted
    # return without ever closing the engagement.
    shaping_gamma: float = 1.0
    # Achieved-effort penalty weight. Raised on the shaping_gamma follow-up
    # lineage to curb the CP1→CP2 command-RMS runaway (103→157) that survived
    # the discount-mismatch fix.
    effort_weight: float = 5.0
    # Prices the step-to-step change in commanded (pre-lag) accel rather
    # than just its achieved (post-lag) magnitude (RewardConfig.effort_rate_weight).
    # 0 keeps every existing lineage's reward bit-identical.
    effort_rate_weight: float = 0.0
    # ZEM potential's lookahead cap, independent of max_time. reward_config()
    # used to set this to max_time so raising the episode budget couldn't
    # silently saturate the horizon -- but that also means the shaping term
    # extrapolates the CURRENT velocity up to max_time ahead whenever closing
    # velocity is near zero (normal against an evasive target), so a heading
    # wobble of a couple degrees swings the extrapolated miss point by
    # hundreds of metres and phi with it. That's a free, physically-fake
    # reward signal the policy can farm by oscillating heading -- the actual
    # cause of the cmd_rms runaway, not effort weight or shaping_gamma. A
    # short, fixed cap keeps the lookahead near real terminal-guidance
    # timescales regardless of episode length.
    zem_t_go_max_s: float = 10.0
    # Terminal closest-approach precision bonus (RewardConfig.precision_weight).
    # 0 keeps every existing lineage's reward bit-identical.
    precision_weight: float = 0.0
    # Fine-tune knob: when set, a resumed checkpoint's action log-std is reset
    # to this value and its learning_rate/ent_coef replaced by this config's.
    # Trained policies sit at std ~0.7 (~175 m/s^2 of exploration noise),
    # which swamps metre-scale terminal precision. None = resume unchanged.
    finetune_log_std: float | None = None

    def __post_init__(self) -> None:
        if self.total_checkpoints != 5:
            raise ValueError("Phase 2 requires exactly five checkpoints")
        if self.action_layout not in ("lateral2", "world3"):
            raise ValueError("action_layout must be 'lateral2' or 'world3'")
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
        if self.pursuer_plant not in ("pointmass", "6dof"):
            raise ValueError("pursuer_plant must be 'pointmass' or '6dof'")

    @property
    def observation_names(self) -> tuple[str, ...]:
        return observation_names(
            use_target_turn_rate_obs=self.use_target_turn_rate_obs,
            use_tracking_obs=self.tracking.enabled,
        )

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

    def reward_config(self) -> RewardConfig:
        """Reward config with the ZEM horizon pinned to the episode budget.

        ``t_go_max_s`` and ``max_time`` are independently settable and were
        both left at 25.0, so changing the budget alone would silently leave
        the ZEM potential saturating at the old horizon. Deriving one from the
        other removes that footgun.
        """

        return RewardConfig(
            t_go_max_s=self.zem_t_go_max_s,
            miss_tanh_scale_m=self.miss_tanh_scale_m,
            shaping_gamma=self.shaping_gamma,
            effort_weight=self.effort_weight,
            effort_rate_weight=self.effort_rate_weight,
            precision_weight=self.precision_weight,
        )


EVASIVE_MAX_TIME_S = 45.0
EVASIVE_MISS_TANH_SCALE_M = 3_000.0
EVASIVE_TIMESTEPS_PER_CHECKPOINT = 204_800


def evasive_redesign_config(**overrides: Any) -> PPOTrainingConfig:
    """Config for the evasive + delayed-tracking lineage (CP1 onward).

    Turns on, together: the v1 evasion maneuver set, the seeker/estimator
    chain, and the extended time budget. The privileged turn-rate observation
    stays off -- it is ground-truth target acceleration, which no seeker can
    measure, and the env refuses to serve it alongside tracking.
    """

    settings: dict[str, Any] = {
        "use_evasive_maneuvers": True,
        "tracking": TrackingConfig(enabled=True),
        # An evasion maneuver the interceptor structurally cannot recover from
        # inside the budget tests the budget, not evasion handling. 45 s
        # matches the existing grounded figure in run_seeker_noise_sweep.py.
        "max_time": EVASIVE_MAX_TIME_S,
        "use_target_turn_rate_obs": False,
        # The first attempt died in the flat tail of the miss penalty: from a
        # 7 km start an untrained policy misses by 1-5 km, where tanh(r/1000)
        # has a gradient of ~0.001 and nothing pulls it back. 3 km keeps the
        # whole from-scratch operating range on a live slope.
        "miss_tanh_scale_m": EVASIVE_MISS_TANH_SCALE_M,
        # Episodes here run ~1.8x longer than the frozen lineage's, so the
        # inherited 20,480 cadence bought only ~10 episodes per checkpoint.
        # Compute is not the constraint it was: this trains in ~2 minutes.
        "timesteps_per_checkpoint": EVASIVE_TIMESTEPS_PER_CHECKPOINT,
    }
    settings.update(overrides)
    return PPOTrainingConfig(**settings)


@dataclass(frozen=True)
class EvaluationCase:
    """One member of an evaluation set.

    The frozen Phase-2 cases are fully described by the scalar fields. Cases
    drawn from a richer maneuver library (break turn, vertical jink, ...)
    cannot be, so they may instead carry explicit builders; when set, those
    take precedence over the scalar fields.
    """

    name: str
    target_position_m: tuple[float, float, float]
    target_velocity_m_s: tuple[float, float, float]
    maneuver: str
    maneuver_accel_g: float = 0.0
    frequency_hz: float = 0.0
    phase_rad: float = 0.0
    maneuver_builder: Callable[[np.random.Generator], ManeuverProfile] | None = None
    initial_condition_builder: (
        Callable[[np.random.Generator], tuple[State, State]] | None
    ) = None


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
    progress_reward: float
    effort_penalty: float
    terminal_reward: float
    legacy_episode_reward: float
    final_time_s: float
    control_effort_m2_s3: float
    commanded_rms_m_s2: float
    achieved_rms_m_s2: float
    commanded_along_track_fraction: float


@dataclass(frozen=True)
class EvalGroupSummary:
    """Aggregate metrics for one reporting slice of the fixed eval set."""

    name: str
    n_cases: int
    n_hits: int
    hit_rate: float
    mean_miss_distance_m: float
    median_miss_distance_m: float
    mean_episode_reward: float
    mean_control_effort_m2_s3: float
    n_ground_impacts: int
    n_timeouts: int


# Group A: feasible within the frozen 25 s budget (NoManeuver + Weave).
# Group B: budget-constrained ConstantTurn (tracked, not used for stop).
GROUP_A_MANEUVERS = frozenset({"none", "weave"})
GROUP_B_MANEUVERS = frozenset({"constant_turn"})


@dataclass(frozen=True)
class EvaluationSummary:
    n_cases: int
    n_hits: int
    n_ground_impacts: int
    n_timeouts: int
    hit_rate: float
    mean_miss_distance_m: float
    median_miss_distance_m: float
    mean_episode_reward: float
    mean_progress_reward: float
    mean_effort_penalty: float
    mean_terminal_reward: float
    mean_legacy_episode_reward: float
    mean_control_effort_m2_s3: float
    mean_commanded_rms_m_s2: float
    mean_achieved_rms_m_s2: float
    mean_commanded_along_track_fraction: float
    group_a: EvalGroupSummary
    group_b: EvalGroupSummary
    cases: tuple[CaseEvaluation, ...]


def _summarize_eval_group(
    name: str,
    cases: Sequence[CaseEvaluation],
) -> EvalGroupSummary:
    if not cases:
        return EvalGroupSummary(
            name=name,
            n_cases=0,
            n_hits=0,
            hit_rate=0.0,
            mean_miss_distance_m=0.0,
            median_miss_distance_m=0.0,
            mean_episode_reward=0.0,
            mean_control_effort_m2_s3=0.0,
            n_ground_impacts=0,
            n_timeouts=0,
        )
    misses = np.array([case.miss_distance_m for case in cases], dtype=float)
    rewards = np.array([case.episode_reward for case in cases], dtype=float)
    efforts = np.array([case.control_effort_m2_s3 for case in cases], dtype=float)
    n_hits = sum(case.hit for case in cases)
    return EvalGroupSummary(
        name=name,
        n_cases=len(cases),
        n_hits=n_hits,
        hit_rate=float(n_hits / len(cases)),
        mean_miss_distance_m=float(np.mean(misses)),
        median_miss_distance_m=float(np.median(misses)),
        mean_episode_reward=float(np.mean(rewards)),
        mean_control_effort_m2_s3=float(np.mean(efforts)),
        n_ground_impacts=sum(case.outcome == "miss" for case in cases),
        n_timeouts=sum(case.outcome == "timeout" for case in cases),
    )


def group_summary_from_case_dicts(
    name: str,
    case_dicts: Sequence[dict[str, object]],
    *,
    maneuvers: frozenset[str],
) -> EvalGroupSummary:
    """Rebuild a group summary from archived per-case JSON (CP1–3 provenance)."""

    selected = [case for case in case_dicts if str(case["maneuver"]) in maneuvers]
    if not selected:
        return _summarize_eval_group(name, ())
    reconstructed = [
        CaseEvaluation(
            name=str(case["name"]),
            maneuver=str(case["maneuver"]),
            hit=bool(case["hit"]),
            outcome=str(case["outcome"]),
            miss_distance_m=float(case["miss_distance_m"]),
            episode_reward=float(case["episode_reward"]),
            progress_reward=float(case.get("progress_reward", 0.0)),
            effort_penalty=float(case.get("effort_penalty", 0.0)),
            terminal_reward=float(case.get("terminal_reward", 0.0)),
            legacy_episode_reward=float(case.get("legacy_episode_reward", 0.0)),
            final_time_s=float(case.get("final_time_s", 0.0)),
            control_effort_m2_s3=float(case["control_effort_m2_s3"]),
            commanded_rms_m_s2=float(case.get("commanded_rms_m_s2", 0.0)),
            achieved_rms_m_s2=float(case.get("achieved_rms_m_s2", 0.0)),
            commanded_along_track_fraction=float(
                case.get("commanded_along_track_fraction", 0.0)
            ),
        )
        for case in selected
    ]
    return _summarize_eval_group(name, reconstructed)


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
    if case.initial_condition_builder is not None:
        return case.initial_condition_builder

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
    if case.maneuver_builder is not None:
        return case.maneuver_builder

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
    n_action = action_dimension(config.action_layout)
    if config.use_evasive_maneuvers:
        initial_condition_sampler = evasive_initial_conditions
        maneuver_factory = evasive_maneuver_factory
    elif config.domain_randomization:
        initial_condition_sampler = randomized_initial_conditions
        maneuver_factory = randomized_maneuver_factory
    else:
        initial_condition_sampler = training_initial_conditions
        maneuver_factory = training_maneuver_factory

    def make_env() -> gym.Env:
        physical_env = InterceptionEnv(
            config=config.simulation_config(),
            reward_config=config.reward_config(),
            initial_condition_sampler=initial_condition_sampler,
            maneuver_factory=maneuver_factory,
            action_layout=config.action_layout,
            use_target_turn_rate_obs=config.use_target_turn_rate_obs,
            tracking=config.tracking,
            pursuer_plant=config.pursuer_plant,
        )
        return gym.wrappers.RescaleAction(
            physical_env,
            min_action=np.full(n_action, -1.0, dtype=np.float32),
            max_action=np.full(n_action, 1.0, dtype=np.float32),
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
        "legacy_episode_reward",
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
                "legacy_episode_reward": float(
                    info.get("legacy_episode_reward", np.nan)
                ),
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
    action_layout: ActionLayout = ACTION_LAYOUT_LATERAL2,
    use_target_turn_rate_obs: bool = False,
    tracking: TrackingConfig | None = None,
    reward_config: RewardConfig | None = None,
    pursuer_plant: Literal["pointmass", "6dof"] = "pointmass",
) -> EvaluationSummary:
    """Evaluate a policy on the immutable, ordered scenario set."""

    config = simulation_config or PPOTrainingConfig().simulation_config()
    n_action = action_dimension(action_layout)
    results: list[CaseEvaluation] = []
    for case_index, case in enumerate(cases):
        physical_env = InterceptionEnv(
            config=config,
            reward_config=reward_config,
            initial_condition_sampler=_case_initial_conditions(case),
            maneuver_factory=_case_maneuver(case),
            pursuer_plant=pursuer_plant,
            action_layout=action_layout,
            use_target_turn_rate_obs=use_target_turn_rate_obs,
            tracking=tracking,
        )
        env = gym.wrappers.RescaleAction(
            physical_env,
            min_action=np.full(n_action, -1.0, dtype=np.float32),
            max_action=np.full(n_action, 1.0, dtype=np.float32),
        )
        observation, info = env.reset(seed=seed + case_index)
        recurrent_state: Any = None
        episode_start = np.array([True], dtype=bool)
        episode_reward = 0.0
        reward_components = {
            "progress": 0.0,
            "effort": 0.0,
            "terminal": 0.0,
        }
        control_effort = 0.0
        commanded_energy = 0.0
        achieved_energy = 0.0
        along_track_energy = 0.0
        n_accel_samples = 0
        while True:
            action, recurrent_state = model.predict(
                observation,
                state=recurrent_state,
                episode_start=episode_start,
                deterministic=True,
            )
            action = np.asarray(action, dtype=float).reshape(-1, n_action)[0]
            # Velocity at command issue (before the step advances the entity).
            pursuer_velocity = np.asarray(
                physical_env.pursuer.state.velocity, dtype=float
            )
            observation, reward, terminated, truncated, info = env.step(action)
            episode_reward += float(reward)
            for name in reward_components:
                reward_components[name] += float(info["reward_terms"][name])
            commanded = np.asarray(info["action_commanded_m_s2"], dtype=float)
            achieved = np.asarray(info["action_achieved_m_s2"], dtype=float)
            control_effort += float(np.dot(commanded, commanded) * config.dt)
            commanded_energy += float(np.dot(commanded, commanded))
            achieved_energy += float(np.dot(achieved, achieved))
            speed = float(np.linalg.norm(pursuer_velocity))
            if speed > 1e-9:
                v_hat = pursuer_velocity / speed
                along = float(np.dot(commanded, v_hat))
                along_track_energy += along * along
            n_accel_samples += 1
            episode_start[:] = False
            if terminated or truncated:
                break
        commanded_rms = float(np.sqrt(commanded_energy / max(n_accel_samples, 1)))
        achieved_rms = float(np.sqrt(achieved_energy / max(n_accel_samples, 1)))
        along_fraction = float(
            along_track_energy / commanded_energy if commanded_energy > 1e-18 else 0.0
        )
        results.append(
            CaseEvaluation(
                name=case.name,
                maneuver=case.maneuver,
                hit=bool(info["hit"]),
                outcome=str(info["outcome"]),
                miss_distance_m=float(info["min_range_m"]),
                episode_reward=episode_reward,
                progress_reward=reward_components["progress"],
                effort_penalty=reward_components["effort"],
                terminal_reward=reward_components["terminal"],
                legacy_episode_reward=float(info.get("legacy_episode_reward", 0.0)),
                final_time_s=float(info["time_s"]),
                control_effort_m2_s3=control_effort,
                commanded_rms_m_s2=commanded_rms,
                achieved_rms_m_s2=achieved_rms,
                commanded_along_track_fraction=along_fraction,
            )
        )
        env.close()

    miss_distances = np.array([result.miss_distance_m for result in results])
    rewards = np.array([result.episode_reward for result in results])
    progress_rewards = np.array([result.progress_reward for result in results])
    effort_penalties = np.array([result.effort_penalty for result in results])
    terminal_rewards = np.array([result.terminal_reward for result in results])
    legacy_rewards = np.array([result.legacy_episode_reward for result in results])
    efforts = np.array([result.control_effort_m2_s3 for result in results])
    commanded_rms = np.array([result.commanded_rms_m_s2 for result in results])
    achieved_rms = np.array([result.achieved_rms_m_s2 for result in results])
    along_frac = np.array(
        [result.commanded_along_track_fraction for result in results]
    )
    n_hits = sum(result.hit for result in results)
    n_ground_impacts = sum(result.outcome == "miss" for result in results)
    n_timeouts = sum(result.outcome == "timeout" for result in results)
    group_a_cases = tuple(
        result for result in results if result.maneuver in GROUP_A_MANEUVERS
    )
    group_b_cases = tuple(
        result for result in results if result.maneuver in GROUP_B_MANEUVERS
    )
    return EvaluationSummary(
        n_cases=len(results),
        n_hits=n_hits,
        n_ground_impacts=n_ground_impacts,
        n_timeouts=n_timeouts,
        hit_rate=float(n_hits / len(results)),
        mean_miss_distance_m=float(np.mean(miss_distances)),
        median_miss_distance_m=float(np.median(miss_distances)),
        mean_episode_reward=float(np.mean(rewards)),
        mean_progress_reward=float(np.mean(progress_rewards)),
        mean_effort_penalty=float(np.mean(effort_penalties)),
        mean_terminal_reward=float(np.mean(terminal_rewards)),
        mean_legacy_episode_reward=float(np.mean(legacy_rewards)),
        mean_control_effort_m2_s3=float(np.mean(efforts)),
        mean_commanded_rms_m_s2=float(np.mean(commanded_rms)),
        mean_achieved_rms_m_s2=float(np.mean(achieved_rms)),
        mean_commanded_along_track_fraction=float(np.mean(along_frac)),
        group_a=_summarize_eval_group("group_a_feasible", group_a_cases),
        group_b=_summarize_eval_group("group_b_budget_constrained", group_b_cases),
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


def _group_metrics_from_evaluation_payload(
    evaluation: dict[str, object],
) -> tuple[float, float, int] | None:
    """Return (mean_reward, mean_miss, n_hits) for Group A, including CP1–3 JSON."""

    group_a = evaluation.get("group_a")
    if isinstance(group_a, dict):
        return (
            float(group_a["mean_episode_reward"]),
            float(group_a["mean_miss_distance_m"]),
            int(group_a["n_hits"]),
        )
    cases = evaluation.get("cases")
    if not isinstance(cases, list):
        return None
    summary = group_summary_from_case_dicts(
        "group_a_feasible",
        cases,
        maneuvers=GROUP_A_MANEUVERS,
    )
    if summary.n_cases == 0:
        return None
    return (
        summary.mean_episode_reward,
        summary.mean_miss_distance_m,
        summary.n_hits,
    )


def _previous_no_improvement_streak(
    output_dir: Path,
    checkpoint_index: int,
    evaluation: EvaluationSummary,
) -> int:
    """Count consecutive checkpoints with no Group-A joint improvement.

    Stop condition uses only Group A (NoManeuver + Weave). Group B
    (ConstantTurn) is reported but does not drive the flag, because under the
    frozen 25 s budget it is expected to plateau near the classical ceiling.
    Improvement requires at least one of: higher Group-A eval return, lower
    Group-A mean miss, or higher Group-A hit count (beyond small tolerances).
    """

    if checkpoint_index <= 1:
        return 0
    previous_path = output_dir / f"rl_checkpoint_{checkpoint_index - 1:02d}.json"
    if not previous_path.exists():
        return 0
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    prev_eval = previous.get("evaluation", {})
    if not isinstance(prev_eval, dict):
        return 0
    previous_group_a = _group_metrics_from_evaluation_payload(prev_eval)
    if previous_group_a is None:
        return 0
    prev_reward, prev_miss, prev_hits = previous_group_a

    if "group_a" in prev_eval:
        previous_streak = int(previous.get("no_improvement_streak", 0))
    else:
        # Legacy CP1–3 metadata stored a pooled streak. Rebuild the Group-A
        # streak from the prior transition when available.
        previous_streak = 0
        if checkpoint_index >= 3:
            older_path = output_dir / f"rl_checkpoint_{checkpoint_index - 2:02d}.json"
            if older_path.exists():
                older = json.loads(older_path.read_text(encoding="utf-8"))
                older_eval = older.get("evaluation", {})
                if isinstance(older_eval, dict):
                    older_group_a = _group_metrics_from_evaluation_payload(older_eval)
                    if older_group_a is not None:
                        o_reward, o_miss, o_hits = older_group_a
                        rw_th = max(1.0, 0.02 * abs(float(o_reward)))
                        ms_th = max(1.0, 0.02 * abs(float(o_miss)))
                        older_to_prev_improved = (
                            float(prev_reward) > float(o_reward) + rw_th
                            or float(prev_miss) < float(o_miss) - ms_th
                            or int(prev_hits) > int(o_hits)
                        )
                        previous_streak = 0 if older_to_prev_improved else 1

    current = evaluation.group_a
    reward_threshold = max(1.0, 0.02 * abs(float(prev_reward)))
    miss_threshold = max(1.0, 0.02 * abs(float(prev_miss)))
    reward_improved = current.mean_episode_reward > float(prev_reward) + reward_threshold
    miss_improved = current.mean_miss_distance_m < float(prev_miss) - miss_threshold
    hit_improved = current.n_hits > int(prev_hits)
    improved = reward_improved or miss_improved or hit_improved
    return 0 if improved else previous_streak + 1


def _validate_previous_observation_contract(
    output_dir: Path,
    checkpoint_index: int,
    config: PPOTrainingConfig,
) -> None:
    metadata_path = output_dir / f"rl_checkpoint_{checkpoint_index - 1:02d}.json"
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"required preceding checkpoint metadata is missing: {metadata_path}"
        )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    previous_names = tuple(metadata.get("observation_names", ()))
    if previous_names != config.observation_names:
        raise ValueError(
            "preceding checkpoint uses an incompatible observation contract; "
            "restart from checkpoint 1"
        )
    previous_layout = metadata.get("action_layout")
    if previous_layout is not None and previous_layout != config.action_layout:
        raise ValueError(
            "preceding checkpoint uses an incompatible action layout; "
            "restart from checkpoint 1"
        )
    # Metadata written before pursuer_plant was introduced necessarily came
    # from the point-mass environment.  Never silently continue that lineage
    # on the rigid-body plant (or vice versa): the observation/action shapes
    # match, so SB3 would otherwise load successfully and create a mixed,
    # irreproducible experiment.
    previous_plant = metadata.get("pursuer_plant", "pointmass")
    if previous_plant != config.pursuer_plant:
        raise ValueError(
            "preceding checkpoint uses an incompatible pursuer plant; "
            "restart from checkpoint 1"
        )


def _append_progress(
    path: Path,
    *,
    config: PPOTrainingConfig,
    report: CheckpointReport,
) -> None:
    new_file = not path.exists()
    if new_file:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Phase 2 training progress\n\n"
            f"- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)\n"
            f"- Observation: {len(config.observation_names)} values "
            f"(`{', '.join(config.observation_names)}`)\n"
            f"- use_target_turn_rate_obs: {config.use_target_turn_rate_obs}\n"
            "- Policy action: normalized "
            f"`[-1, 1]^{action_dimension(config.action_layout)}`, rescaled to "
            "the physical 25 g environment action before dynamics\n"
            f"- Action layout: `{config.action_layout}`\n"
            f"- Domain randomization: {config.domain_randomization} "
            "(must remain false for this retrain)\n"
            f"- Pursuer plant: {config.pursuer_plant}\n"
            "- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal "
            "+ achieved-effort; legacy Phase-1 reward logged in parallel\n"
            f"- Fixed budget: {config.total_timesteps:,} timesteps in "
            f"{config.total_checkpoints} checkpoints of "
            f"{config.timesteps_per_checkpoint:,}\n"
            f"- Training seed: {config.seed}\n"
            f"- Fixed evaluation set: {len(FIXED_EVALUATION_CASES)} engagements "
            "(3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)\n"
            "- Reporting split: Group A = NoManeuver+Weave (stop condition); "
            "Group B = ConstantTurn (tracked only; budget-constrained)\n\n",
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
        "- Fixed-eval mean reward components "
        f"(shaping/effort/terminal): {evaluation.mean_progress_reward:.6f} / "
        f"{evaluation.mean_effort_penalty:.6f} / "
        f"{evaluation.mean_terminal_reward:.6f}",
        f"- Fixed-eval mean legacy episode reward: "
        f"{evaluation.mean_legacy_episode_reward:.6f}",
        "- Fixed-eval mean control effort: "
        f"{evaluation.mean_control_effort_m2_s3:.6f} m²/s³",
        "- Fixed-eval mean commanded/achieved RMS accel: "
        f"{evaluation.mean_commanded_rms_m_s2:.3f} / "
        f"{evaluation.mean_achieved_rms_m_s2:.3f} m/s²",
        "- Fixed-eval mean commanded along-track energy fraction: "
        f"{evaluation.mean_commanded_along_track_fraction:.6f}",
        "- Fixed-eval outcomes (ground impact/timeout/hit): "
        f"{evaluation.n_ground_impacts}/{evaluation.n_timeouts}/"
        f"{evaluation.n_hits}",
        (
            "- Group A (NoManeuver+Weave) hit rate / mean/median miss / "
            f"mean reward / mean effort: "
            f"{evaluation.group_a.n_hits}/{evaluation.group_a.n_cases} / "
            f"{evaluation.group_a.mean_miss_distance_m:.3f} / "
            f"{evaluation.group_a.median_miss_distance_m:.3f} m / "
            f"{evaluation.group_a.mean_episode_reward:.6f} / "
            f"{evaluation.group_a.mean_control_effort_m2_s3:.6f} m²/s³"
        ),
        (
            "- Group B (ConstantTurn) hit rate / mean/median miss / "
            f"mean reward / mean effort: "
            f"{evaluation.group_b.n_hits}/{evaluation.group_b.n_cases} / "
            f"{evaluation.group_b.mean_miss_distance_m:.3f} / "
            f"{evaluation.group_b.median_miss_distance_m:.3f} m / "
            f"{evaluation.group_b.mean_episode_reward:.6f} / "
            f"{evaluation.group_b.mean_control_effort_m2_s3:.6f} m²/s³"
        ),
        f"- Possible convergence warning (Group A stop): {report.convergence_warning}",
        f"- Model: `{report.checkpoint_path.relative_to(path.parent.parent)}`",
        f"- Evaluation details: "
        f"`{report.evaluation_path.relative_to(path.parent.parent)}`",
        f"- Training curve: `{report.curve_path.relative_to(path.parent.parent)}`",
    ]
    if not new_file:
        lines.insert(0, "")
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
    # No upper bound against config.total_checkpoints: that field is pinned
    # to exactly 5 for the frozen Phase-2 budget (PPOTrainingConfig.__post_init__),
    # but an experiment lineage that is still visibly climbing at CP5 (see
    # NOTES.md 2026-09-14) legitimately needs a CP6+, which this function
    # already supports end to end -- every helper it calls keys off
    # checkpoint_index, not total_checkpoints.
    if checkpoint_index < 1:
        raise ValueError("checkpoint_index must be >= 1")

    output_dir = Path(output_dir)
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_path = checkpoint_dir / f"rl_checkpoint_{checkpoint_index:02d}.zip"
    previous_path = checkpoint_dir / f"rl_checkpoint_{checkpoint_index - 1:02d}.zip"
    if checkpoint_path.exists():
        raise FileExistsError(f"refusing to overwrite {checkpoint_path}")
    if checkpoint_index > 1 and not previous_path.exists():
        raise FileNotFoundError(f"required preceding checkpoint is missing: {previous_path}")
    if checkpoint_index > 1:
        _validate_previous_observation_contract(output_dir, checkpoint_index, config)

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
        custom_objects = None
        if config.finetune_log_std is not None:
            lr = config.learning_rate
            custom_objects = {
                "learning_rate": lr,
                "lr_schedule": lambda _progress: lr,
                "ent_coef": config.ent_coef,
            }
        model = RecurrentPPO.load(
            previous_path, env=vec_env, device="cpu", custom_objects=custom_objects
        )
        if config.finetune_log_std is not None:
            with torch.no_grad():
                model.policy.log_std.fill_(config.finetune_log_std)
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

    # The evasive lineage is graded on a held-out set drawn from a disjoint
    # seed stream, so a pass is evidence of generalization rather than a
    # resample of the training distribution.
    evaluation_cases = (
        build_held_out_cases()
        if config.use_evasive_maneuvers
        else FIXED_EVALUATION_CASES
    )
    evaluation = evaluate_policy(
        model,
        cases=evaluation_cases,
        simulation_config=config.simulation_config(),
        action_layout=config.action_layout,
        use_target_turn_rate_obs=config.use_target_turn_rate_obs,
        tracking=config.tracking,
        reward_config=config.reward_config(),
        pursuer_plant=config.pursuer_plant,
    )
    total_episodes = _count_csv_rows(episode_csv_path)
    curve = _curve_summary(callback.rows, total_episodes)
    no_improvement_streak = _previous_no_improvement_streak(
        output_dir,
        checkpoint_index,
        evaluation,
    )
    # At checkpoint 2, one non-improving Group-A transition already represents
    # two consecutive Group-A summaries with no joint improvement.
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
            "observation_names": list(config.observation_names),
            "use_target_turn_rate_obs": config.use_target_turn_rate_obs,
            "action_layout": config.action_layout,
            "domain_randomization": config.domain_randomization,
            "pursuer_plant": config.pursuer_plant,
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
