"""Gymnasium environment for the existing 3D point-mass engagement.

The default observation is a ten-element, ``float32`` vector in this exact
order (CP1–CP4 lineage; ``use_target_turn_rate_obs=False``):

``[r_hat_x, r_hat_y, r_hat_z, omega_x_s, omega_y_s, omega_z_s,
range_s, closing_s, height_agl_s, altitude_rate_s]``.

``r_hat`` is the world-frame target-from-pursuer LOS unit vector.  A unit
vector is used instead of azimuth/elevation so the 3D representation has no
angle wrap or pole singularity.  The remaining values are bounded,
dimensionless transforms of physical quantities:

* ``omega_s = tanh(omega_los / 0.1 rad/s)``, where
  ``omega_los = cross(r_rel, v_rel) / range**2`` (already present — this is
  relative LOS rate, not target body turn rate);
* ``range_s = range / (range + 10_000 m)``;
* ``closing_s = tanh(closing_velocity / 1_000 m/s)``, where positive means
  closing;
* ``height_agl_s = max(height_above_ground, 0) /
  (max(height_above_ground, 0) + 5_000 m)``;
* ``altitude_rate_s = tanh(pursuer_vz / 200 m/s)``.

With ``use_target_turn_rate_obs=True``, three more channels are appended:

``[omega_t_x_s, omega_t_y_s, omega_t_z_s]`` where
``omega_t = cross(v_target, a_lat_achieved) / |v_target|**2`` and
``omega_t_s = tanh(omega_t / 0.2 rad/s)``.  This is the analytic angular
rate of the target velocity vector from achieved lateral accel (no finite
difference, so no smoothing filter).  Before the first ``step``, achieved
accel is zero and the feature falls back to ``[0, 0, 0]``.

Height above the environment's configurable ground plane is more useful than
raw world ``z`` when ``ground_altitude_m`` is nonzero.  It and pursuer vertical
speed make ground proximity observable without changing the physics model.

The default action (``lateral2``) is a two-component coefficient vector on an
orthonormal basis of the velocity-normal plane, in m/s^2.  Each component is
boxed at the pursuer structural limit; the reconstructed world-frame command
is then radially clipped to that same limit.  The along-track null space of
``clamp_lateral_command`` is therefore not representable.  This mapping lives
only in the RL wrapper: ``GuidanceLaw.compute_command`` is still a world-frame
``(3,)`` vector, and ``PointMassEntity.step`` is unchanged.

``action_layout="world3"`` restores the Phase-1/2 three-component world-frame
action so archived 3D policies can be replayed.  The world command is still
passed to ``PointMassEntity.step``, which applies lag, velocity-normal
projection, aerodynamic/structural clamps, and the configured integrator.

Reward per step is potential-based ZEM shaping plus closest-approach terminal
plus a small cost on **achieved** (post-clamp) lateral acceleration.  The
Phase-1 range-progress / commanded-effort / ±100 terminal reward is attached
as ``legacy_*`` diagnostics and is not part of the env return.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from guidance_sim.estimation.alpha_beta import AlphaBetaFilter
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import ManeuverProfile, NoManeuver
from guidance_sim.sensors.measurement import SeekerNoiseConfig, Sensor, SensorConfig
from guidance_sim.rl.actions import (
    ACTION_LAYOUT_LATERAL2,
    ACTION_LAYOUT_WORLD3,
    ActionLayout,
    action_dimension,
    lateral_to_world,
)
from guidance_sim.rl.reward import RewardConfig, compute_reward
from guidance_sim.rl.zem import potential_from_zem, predicted_miss_m
from guidance_sim.simulation.engine import SimulationConfig

LOS_RATE_SCALE_RAD_S = 0.1
TARGET_TURN_RATE_SCALE_RAD_S = 0.2
RANGE_SCALE_M = 10_000.0
CLOSING_SPEED_SCALE_M_S = 1_000.0
ALTITUDE_SCALE_M = 5_000.0
ALTITUDE_RATE_SCALE_M_S = 200.0
_KINEMATIC_EPS = 1e-9

# Default / frozen CP1–CP4 observation contract (flag off).
OBSERVATION_NAMES = (
    "los_unit_x",
    "los_unit_y",
    "los_unit_z",
    "los_rate_x_scaled",
    "los_rate_y_scaled",
    "los_rate_z_scaled",
    "range_scaled",
    "closing_velocity_scaled",
    "height_above_ground_scaled",
    "altitude_rate_scaled",
)

TARGET_TURN_RATE_OBSERVATION_NAMES = (
    "target_turn_rate_x_scaled",
    "target_turn_rate_y_scaled",
    "target_turn_rate_z_scaled",
)

# Appended when the seeker/estimator chain is active. Without these, a policy
# fed a delayed estimate cannot tell "the target has not moved" from "my
# estimate has not updated recently".
TRACKING_OBSERVATION_NAMES = (
    "time_since_update_scaled",
    "estimate_uncertainty_scaled",
)

STALENESS_SCALE = 2.0
ESTIMATE_UNCERTAINTY_SCALE_M = 50.0


def observation_names(
    *,
    use_target_turn_rate_obs: bool = False,
    use_tracking_obs: bool = False,
) -> tuple[str, ...]:
    """Return the observation name tuple for the given feature flags."""

    names = OBSERVATION_NAMES
    if use_target_turn_rate_obs:
        names = names + TARGET_TURN_RATE_OBSERVATION_NAMES
    if use_tracking_obs:
        names = names + TRACKING_OBSERVATION_NAMES
    return names


@dataclass(frozen=True)
class TrackingConfig:
    """Seeker/estimator chain feeding the policy's view of the target.

    Defaults are the literature-anchored seeker configuration the existing
    ``SensorConfig`` / ``AlphaBetaFilter`` already encode (100 Hz sampling,
    alpha=0.5 with the Benedict-Bordner beta relation, ~1 mrad angle noise).
    Latency is the piece that was previously defaulted to zero and never
    exercised: it is sampled per episode, as is the update rate, because a
    real tracker's effective data rate varies with target dynamics within a
    single engagement rather than sitting at one fixed value.
    """

    # Off at the raw-env level so the frozen CP1-CP5 observation contract (and
    # every consumer of it: rollout capture, shadow compare, the live-inference
    # endpoint) keeps working untouched. New training opts in explicitly via
    # PPOTrainingConfig, which defaults it on.
    enabled: bool = False
    # CP1 finding: alpha=0.5 is Zarchan's figure for a 100 Hz tracker. At the
    # 25-50 Hz rates this codebase runs, the beta/dt velocity gain (~4.2)
    # multiplies ~18 m of position residual into ~75 m/s of velocity noise --
    # against a ~200 m/s target, and it corrupts LOS rate by ~0.66x its own
    # magnitude. Sweeping alpha puts the optimum near 0.2 (velocity error
    # 18 m/s, LOS-rate error 0.16x); 0.05 over-smooths and gets worse again.
    alpha: float = 0.2
    latency_range_s: tuple[float, float] = (0.02, 0.08)
    # CP0 finding: the spec's {50, 100} Hz assumed a 100 Hz control loop, but
    # training runs at dt=0.02 (50 Hz). A seeker at or above the control rate
    # delivers every step, so the update-gap half of staleness carries no
    # information. These bracket the control rate instead.
    update_rate_choices_hz: tuple[float, ...] = (25.0, 50.0)
    detection_probability: float = 1.0
    noise: SeekerNoiseConfig | None = None

    def __post_init__(self) -> None:
        low, high = self.latency_range_s
        if low < 0.0 or high < low:
            raise ValueError("latency_range_s must be a non-negative (low, high)")
        if not self.update_rate_choices_hz:
            raise ValueError("update_rate_choices_hz must not be empty")
        if any(rate <= 0.0 for rate in self.update_rate_choices_hz):
            raise ValueError("update_rate_choices_hz must be positive")

    def sample_sensor_config(self, rng: np.random.Generator) -> SensorConfig:
        low, high = self.latency_range_s
        latency_s = float(rng.uniform(low, high)) if high > low else float(low)
        rate_hz = float(rng.choice(np.asarray(self.update_rate_choices_hz)))
        return SensorConfig(
            update_rate_hz=rate_hz,
            latency_s=latency_s,
            detection_probability=self.detection_probability,
            noise=self.noise,
        )


def compute_target_turn_rate_rad_s(
    velocity_m_s: np.ndarray,
    lateral_accel_m_s2: np.ndarray,
) -> np.ndarray:
    """Angular rate of the velocity vector from lateral acceleration.

    ``omega = cross(v, a) / |v|**2``.  For pure lateral ``a`` this has
    magnitude ``|a|/|v|``.  Returns zeros when speed is near zero.
    """

    velocity = np.asarray(velocity_m_s, dtype=float).reshape(3)
    accel = np.asarray(lateral_accel_m_s2, dtype=float).reshape(3)
    speed_sq = float(np.dot(velocity, velocity))
    if speed_sq <= _KINEMATIC_EPS**2:
        return np.zeros(3)
    return np.cross(velocity, accel) / speed_sq

InitialConditionSampler = Callable[[np.random.Generator], tuple[State, State]]
ManeuverFactory = Callable[[np.random.Generator], ManeuverProfile]


def demo_initial_conditions(
    _rng: np.random.Generator,
) -> tuple[State, State]:
    """Fresh copies of the initial conditions used by ``scripts/run_demo.py``."""

    return (
        State(
            position=[0.0, 0.0, 3000.0],
            velocity=[350.0, 0.0, 0.0],
        ),
        State(
            position=[7000.0, 400.0, 3300.0],
            velocity=[-200.0, 0.0, 0.0],
        ),
    )


def _default_pursuer_vehicle() -> VehicleParams:
    """Fresh copy of the illustrative pursuer used by the demo."""

    return VehicleParams(
        mass=50.0,
        reference_area=0.05,
        drag_coefficient=0.3,
        max_normal_force_coefficient=15.0,
        max_load_factor=25.0,
    )


def _default_target_vehicle() -> VehicleParams:
    """Fresh copy of the illustrative target used by the demo."""

    return VehicleParams(
        mass=40.0,
        reference_area=0.06,
        drag_coefficient=0.35,
        max_normal_force_coefficient=10.0,
        max_load_factor=9.0,
    )


def _no_maneuver_factory(_rng: np.random.Generator) -> ManeuverProfile:
    return NoManeuver()


def _empty_reward_terms() -> dict[str, float]:
    return {
        "progress": 0.0,
        "shaping": 0.0,
        "effort": 0.0,
        "terminal": 0.0,
        "legacy_progress": 0.0,
        "legacy_effort": 0.0,
        "legacy_terminal": 0.0,
        "legacy_total": 0.0,
        "zem_m": 0.0,
        "potential": 0.0,
    }


class InterceptionEnv(gym.Env[np.ndarray, np.ndarray]):
    """Step-wise RL wrapper around the established point-mass dynamics.

    ``initial_condition_sampler`` and ``maneuver_factory`` receive Gymnasium's
    seeded ``np_random`` generator.  The default sampler is deterministic and
    exactly matches the demo geometry.  Future training can inject seeded
    sampling and fresh ``NoManeuver``, ``ConstantTurn``, or
    ``SinusoidalWeave`` instances without changing the state/action contract.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        *,
        config: SimulationConfig | None = None,
        reward_config: RewardConfig | None = None,
        initial_condition_sampler: InitialConditionSampler = demo_initial_conditions,
        maneuver_factory: ManeuverFactory = _no_maneuver_factory,
        pursuer_vehicle: VehicleParams | None = None,
        target_vehicle: VehicleParams | None = None,
        ground_altitude_m: float = 0.0,
        action_layout: ActionLayout = ACTION_LAYOUT_LATERAL2,
        use_target_turn_rate_obs: bool = False,
        tracking: TrackingConfig | None = None,
    ) -> None:
        super().__init__()
        self.config = replace(config) if config is not None else SimulationConfig()
        self.reward_config = reward_config or RewardConfig()
        if action_layout not in (ACTION_LAYOUT_LATERAL2, ACTION_LAYOUT_WORLD3):
            raise ValueError(f"unsupported action_layout: {action_layout}")
        self.action_layout: ActionLayout = action_layout
        self.use_target_turn_rate_obs = bool(use_target_turn_rate_obs)
        self.tracking = tracking if tracking is not None else TrackingConfig()
        if self.tracking.enabled and self.use_target_turn_rate_obs:
            # The turn-rate channels are computed from the target's post-clamp
            # achieved acceleration -- privileged information no real seeker
            # can observe. Serving them alongside a delayed, noisy position
            # estimate would make "the policy only sees what it can measure"
            # false for that one channel.
            raise ValueError(
                "use_target_turn_rate_obs reads privileged ground-truth target "
                "acceleration and cannot be combined with tracking.enabled; "
                "pass TrackingConfig(enabled=False) for the legacy contract"
            )
        self._validate_config()

        self._initial_condition_sampler = initial_condition_sampler
        self._maneuver_factory = maneuver_factory
        self._pursuer_vehicle = replace(
            pursuer_vehicle or _default_pursuer_vehicle()
        )
        self._target_vehicle = replace(target_vehicle or _default_target_vehicle())
        self.ground_altitude_m = float(ground_altitude_m)
        if not np.isfinite(self.ground_altitude_m):
            raise ValueError("ground_altitude_m must be finite")

        self.action_limit_m_s2 = self._pursuer_vehicle.max_load_factor * G0
        if not np.isfinite(self.action_limit_m_s2) or self.action_limit_m_s2 <= 0.0:
            raise ValueError("pursuer structural acceleration limit must be positive")

        n_action = action_dimension(self.action_layout)
        action_bound = np.full(n_action, self.action_limit_m_s2, dtype=np.float32)
        self.action_space = spaces.Box(
            low=-action_bound,
            high=action_bound,
            dtype=np.float32,
        )
        self.observation_names = observation_names(
            use_target_turn_rate_obs=self.use_target_turn_rate_obs,
            use_tracking_obs=self.tracking.enabled,
        )
        obs_dim = len(self.observation_names)
        # Base bounds: 6 LOS channels in [-1,1], range/height in [0,1],
        # closing and altitude rate in [-1,1]. Extra turn-rate channels [-1,1].
        low = np.array(
            [-1.0] * 6 + [0.0, -1.0, 0.0, -1.0],
            dtype=np.float32,
        )
        high = np.ones(10, dtype=np.float32)
        if self.use_target_turn_rate_obs:
            low = np.concatenate((low, np.full(3, -1.0, dtype=np.float32)))
            high = np.concatenate((high, np.ones(3, dtype=np.float32)))
        if self.tracking.enabled:
            # Staleness and uncertainty are non-negative tanh features.
            low = np.concatenate((low, np.zeros(2, dtype=np.float32)))
            high = np.concatenate((high, np.ones(2, dtype=np.float32)))
        assert low.shape == (obs_dim,) and high.shape == (obs_dim,)
        self.observation_space = spaces.Box(
            low=low,
            high=high,
            dtype=np.float32,
        )

        self.pursuer: PointMassEntity | None = None
        self.target: PointMassEntity | None = None
        self.target_maneuver: ManeuverProfile | None = None
        self.time_s = 0.0
        self.min_range_m = np.inf
        self.closest_approach_m = np.inf
        self._episode_done = True
        self._phi = 0.0
        self._episode_legacy_reward = 0.0
        self.sensor: Sensor | None = None
        self.estimator: AlphaBetaFilter | None = None
        self._sensor_config: SensorConfig | None = None
        self._estimator_ready = False
        self._last_update_time_s = 0.0

    def _validate_config(self) -> None:
        cfg = self.config
        if not np.isfinite(cfg.dt) or cfg.dt <= 0.0:
            raise ValueError("config.dt must be finite and positive")
        if not np.isfinite(cfg.max_time) or cfg.max_time <= 0.0:
            raise ValueError("config.max_time must be finite and positive")
        if not np.isfinite(cfg.intercept_radius) or cfg.intercept_radius <= 0.0:
            raise ValueError("config.intercept_radius must be finite and positive")
        if not np.isfinite(cfg.autopilot_tau) or cfg.autopilot_tau < 0.0:
            raise ValueError("config.autopilot_tau must be finite and non-negative")

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict[str, object]]:
        """Start a fresh, seeded episode and return ``(observation, info)``."""

        super().reset(seed=seed)
        del options  # Reserved for later scenario selection; no Phase-1 options.

        pursuer_state, target_state = self._initial_condition_sampler(self.np_random)
        if not isinstance(pursuer_state, State) or not isinstance(target_state, State):
            raise TypeError("initial_condition_sampler must return two State objects")

        self.pursuer = PointMassEntity(
            name="pursuer",
            state=pursuer_state.copy(),
            vehicle=replace(self._pursuer_vehicle),
        )
        self.target = PointMassEntity(
            name="target",
            state=target_state.copy(),
            vehicle=replace(self._target_vehicle),
        )
        self.target_maneuver = self._maneuver_factory(self.np_random)
        if not isinstance(self.target_maneuver, ManeuverProfile):
            raise TypeError("maneuver_factory must return a ManeuverProfile")

        if self.tracking.enabled:
            self._sensor_config = self.tracking.sample_sensor_config(self.np_random)
            self.sensor = Sensor(self._sensor_config)
            self.estimator = AlphaBetaFilter(alpha=self.tracking.alpha)
        else:
            self._sensor_config = None
            self.sensor = None
            self.estimator = None
        self._estimator_ready = False
        self._last_update_time_s = 0.0

        self.time_s = 0.0
        self.min_range_m = self._range()
        self.closest_approach_m = self.min_range_m
        if self.min_range_m <= self.config.intercept_radius:
            raise ValueError("initial range must exceed config.intercept_radius")
        if self._ground_impact_reason() is not None:
            raise ValueError("initial states must be above ground_altitude_m")
        self._episode_done = False
        self._episode_legacy_reward = 0.0
        zem_m = self._predicted_miss(self._remaining_time_s())
        self._phi = potential_from_zem(
            zem_m, self.reward_config.zem_scale_m, terminal=False
        )

        observation, physical = self._observation()
        n_action = action_dimension(self.action_layout)
        return observation, self._info(
            physical=physical,
            outcome="ongoing",
            termination_reason=None,
            requested=np.zeros(n_action),
            commanded=np.zeros(3),
            achieved=np.zeros(3),
            action_was_clipped=False,
            reward_terms=_empty_reward_terms(),
        )

    def step(
        self,
        action: np.ndarray,
    ) -> tuple[np.ndarray, float, bool, bool, dict[str, object]]:
        """Advance target and pursuer once using modern Gymnasium semantics."""

        if self._episode_done or self.pursuer is None or self.target is None:
            raise RuntimeError("reset() is required before step() or after episode end")
        if self.target_maneuver is None:
            raise RuntimeError("target maneuver is unavailable; call reset()")

        requested = np.asarray(action, dtype=float).reshape(-1)
        expected = action_dimension(self.action_layout)
        if requested.shape != (expected,):
            raise ValueError(
                f"action must have shape ({expected},), got {requested.shape}"
            )
        if not np.all(np.isfinite(requested)):
            raise ValueError("action must contain only finite values")
        commanded, action_was_clipped = self._project_action(requested)

        previous_range = self._range()
        previous_relative = self.target.state.position - self.pursuer.state.position
        cfg = self.config

        self.target_maneuver.update_engagement(
            self.time_s, self.target.state, self.pursuer.state
        )
        target_command = self.target_maneuver.lateral_accel(
            self.time_s, self.target.state
        )
        self.target.step(
            cfg.dt,
            target_command,
            integrator=cfg.integrator,
            autopilot_tau=cfg.autopilot_tau,
        )
        self.pursuer.step(
            cfg.dt,
            commanded,
            integrator=cfg.integrator,
            autopilot_tau=cfg.autopilot_tau,
        )
        achieved = self.pursuer.last_achieved_lateral_accel.copy()
        self.time_s += cfg.dt
        self._advance_tracking()

        current_range = self._range()
        self.min_range_m = min(self.min_range_m, current_range)
        hit = current_range <= cfg.intercept_radius
        ground_reason = self._ground_impact_reason()
        self.closest_approach_m = min(
            self.closest_approach_m,
            self._segment_closest_approach(previous_relative, hit),
        )

        terminated = bool(hit or ground_reason is not None)
        truncated = bool(
            not terminated and self.time_s >= cfg.max_time - 1e-12
        )
        if hit:
            outcome = "hit"
            termination_reason = "intercept"
        elif ground_reason is not None:
            outcome = "miss"
            termination_reason = ground_reason
        elif truncated:
            outcome = "timeout"
            termination_reason = "time_limit"
        else:
            outcome = "ongoing"
            termination_reason = None
        self._episode_done = terminated or truncated

        zem_m = self._predicted_miss(self._remaining_time_s())
        breakdown = compute_reward(
            previous_potential=self._phi,
            zem_m=zem_m,
            previous_range_m=previous_range,
            current_range_m=current_range,
            min_range_m=self.min_range_m,
            achieved_lateral_m_s2=achieved,
            legacy_commanded_m_s2=commanded,
            action_limit_m_s2=self.action_limit_m_s2,
            dt=cfg.dt,
            outcome=outcome,
            config=self.reward_config,
            closest_approach_m=self.closest_approach_m,
        )
        self._phi = breakdown.potential
        self._episode_legacy_reward += breakdown.legacy_total
        reward_terms = breakdown.env_terms()

        observation, physical = self._observation()
        info = self._info(
            physical=physical,
            outcome=outcome,
            termination_reason=termination_reason,
            requested=requested,
            commanded=commanded,
            achieved=achieved,
            action_was_clipped=action_was_clipped,
            reward_terms=reward_terms,
        )
        info["legacy_reward"] = breakdown.legacy_total
        info["legacy_episode_reward"] = self._episode_legacy_reward
        info["target_action_commanded_m_s2"] = np.asarray(
            target_command, dtype=float
        ).reshape(3).copy()
        info["target_action_achieved_m_s2"] = (
            self.target.last_achieved_lateral_accel.copy()
        )
        return observation, breakdown.total, terminated, truncated, info

    def _segment_closest_approach(
        self, previous_relative: np.ndarray, hit: bool
    ) -> float:
        """True closest approach inside the step just taken (linear relative motion).

        ``min_range_m`` samples range only at step ends, so at ~350 m/s closing
        and dt=0.02 a dead-centre pass can read as several metres. On a hit the
        episode stops at the first sample inside the radius, so the rest of the
        pass is extrapolated along the current true relative velocity.
        """

        assert self.pursuer is not None and self.target is not None
        current = self.target.state.position - self.pursuer.state.position
        delta = current - previous_relative
        denom = float(np.dot(delta, delta))
        s = 0.0 if denom <= 1e-12 else float(
            np.clip(-np.dot(previous_relative, delta) / denom, 0.0, 1.0)
        )
        best = float(np.linalg.norm(previous_relative + s * delta))
        if hit:
            velocity = self.target.state.velocity - self.pursuer.state.velocity
            speed_sq = float(np.dot(velocity, velocity))
            if speed_sq > 1e-12:
                t_star = max(-float(np.dot(current, velocity)) / speed_sq, 0.0)
                best = min(best, float(np.linalg.norm(current + t_star * velocity)))
        return best

    def _advance_tracking(self) -> None:
        """Sample the seeker and run the estimator one step, if tracking is on."""

        if not self.tracking.enabled:
            return
        assert self.sensor is not None and self.estimator is not None
        assert self.pursuer is not None and self.target is not None
        measurement = self.sensor.measure(
            self.time_s,
            self.pursuer.state,
            self.target.state,
            self.np_random,
        )
        self.estimator.update(measurement, self.pursuer.state, self.config.dt)
        if measurement is not None and measurement.valid:
            # Stamp when the delivered data was *sampled*, not when it landed.
            # CP0 finding: timing from the delivery instant makes the channel
            # identically zero whenever the seeker runs at or above the control
            # rate, which hides the latency the policy actually has to cover.
            self._last_update_time_s = float(measurement.t)
            # The filter needs a range-bearing fix before it can hand back a
            # Cartesian state; until then callers fall back to truth.
            try:
                self.estimator.estimate()
            except RuntimeError:
                self._estimator_ready = False
            else:
                self._estimator_ready = True

    def _tracked_target_state(self) -> State:
        """Target state as the interceptor sees it: estimated, or truth pre-lock."""

        if self.target is None:
            raise RuntimeError("environment has not been reset")
        if not self.tracking.enabled or not self._estimator_ready:
            return self.target.state
        assert self.estimator is not None
        estimated, _accel = self.estimator.estimate()
        return estimated

    def _tracking_features(self) -> tuple[float, float]:
        """(staleness, uncertainty) observation channels, both in [0, 1]."""

        if not self.tracking.enabled:
            return 0.0, 0.0
        if not self._estimator_ready:
            # No fix yet: maximally stale and maximally uncertain.
            return 1.0, 1.0
        assert self.estimator is not None and self._sensor_config is not None
        reference_s = max(
            self._sensor_config.latency_s,
            1.0 / self._sensor_config.update_rate_hz,
        )
        since_update_s = max(self.time_s - self._last_update_time_s, 0.0)
        staleness = float(
            np.tanh(since_update_s / (STALENESS_SCALE * max(reference_s, 1e-6)))
        )
        position_variance = float(np.mean(np.diag(self.estimator.covariance())[:3]))
        uncertainty = float(
            np.tanh(
                np.sqrt(max(position_variance, 0.0)) / ESTIMATE_UNCERTAINTY_SCALE_M
            )
        )
        return staleness, uncertainty

    def _remaining_time_s(self) -> float:
        return max(self.config.max_time - self.time_s, 0.0)

    def _predicted_miss(self, remaining_time_s: float) -> float:
        if self.pursuer is None or self.target is None:
            raise RuntimeError("environment has not been reset")
        # Shaping may use the same imperfect information the policy acts on;
        # potential-based shaping's policy-invariance guarantee does not
        # require a ground-truth potential. Terminal reward and hit detection
        # stay on truth (see step()/_range()).
        target_state = self._tracked_target_state()
        relative_position = target_state.position - self.pursuer.state.position
        relative_velocity = target_state.velocity - self.pursuer.state.velocity
        return predicted_miss_m(
            relative_position,
            relative_velocity,
            remaining_time_s,
            self.config.intercept_radius,
            self.reward_config.zem_safeguards(),
        )

    def _project_action(self, requested: np.ndarray) -> tuple[np.ndarray, bool]:
        if self.pursuer is None:
            raise RuntimeError("environment has not been reset")
        if self.action_layout == ACTION_LAYOUT_LATERAL2:
            world = lateral_to_world(requested, self.pursuer.state.velocity)
        else:
            world = requested.copy()
        magnitude = float(np.linalg.norm(world))
        if magnitude <= self.action_limit_m_s2:
            return world, False
        return world * (self.action_limit_m_s2 / magnitude), True

    def _range(self) -> float:
        if self.pursuer is None or self.target is None:
            raise RuntimeError("environment has not been reset")
        return float(
            np.linalg.norm(
                self.target.state.position - self.pursuer.state.position
            )
        )

    def _kinematics(
        self,
    ) -> tuple[np.ndarray, np.ndarray, float, float]:
        if self.pursuer is None or self.target is None:
            raise RuntimeError("environment has not been reset")
        # Observed geometry, not true geometry: with tracking enabled these
        # LOS/range/closing channels carry the estimator's delayed, noisy fix.
        target_state = self._tracked_target_state()
        relative_position = target_state.position - self.pursuer.state.position
        relative_velocity = target_state.velocity - self.pursuer.state.velocity
        range_m = float(np.linalg.norm(relative_position))
        if range_m <= _KINEMATIC_EPS:
            return np.zeros(3), np.zeros(3), range_m, 0.0
        los_unit = relative_position / range_m
        los_rate = np.cross(relative_position, relative_velocity) / range_m**2
        closing_velocity = -float(
            np.dot(relative_position, relative_velocity) / range_m
        )
        return los_unit, los_rate, range_m, closing_velocity

    def _observation(
        self,
    ) -> tuple[np.ndarray, dict[str, np.ndarray | float]]:
        if self.pursuer is None or self.target is None:
            raise RuntimeError("environment has not been reset")
        los_unit, los_rate, range_m, closing_velocity = self._kinematics()
        height_above_ground_m = (
            self.pursuer.state.altitude() - self.ground_altitude_m
        )
        nonnegative_height_m = max(height_above_ground_m, 0.0)
        altitude_rate_m_s = float(self.pursuer.state.velocity[2])
        # Decision: use post-clamp achieved lateral accel. Before the first
        # step this is identically zero (entity default) — not maneuver command.
        target_turn_rate = compute_target_turn_rate_rad_s(
            self.target.state.velocity,
            self.target.last_achieved_lateral_accel,
        )
        parts: list[np.ndarray] = [
            los_unit,
            np.tanh(los_rate / LOS_RATE_SCALE_RAD_S),
            np.array(
                [
                    range_m / (range_m + RANGE_SCALE_M),
                    np.tanh(closing_velocity / CLOSING_SPEED_SCALE_M_S),
                    nonnegative_height_m
                    / (nonnegative_height_m + ALTITUDE_SCALE_M),
                    np.tanh(altitude_rate_m_s / ALTITUDE_RATE_SCALE_M_S),
                ]
            ),
        ]
        if self.use_target_turn_rate_obs:
            parts.append(
                np.tanh(target_turn_rate / TARGET_TURN_RATE_SCALE_RAD_S)
            )
        staleness, uncertainty = self._tracking_features()
        if self.tracking.enabled:
            parts.append(np.array([staleness, uncertainty]))
        observation = np.concatenate(parts)
        observation = np.clip(
            observation,
            self.observation_space.low,
            self.observation_space.high,
        ).astype(np.float32)
        if not np.all(np.isfinite(observation)):
            raise RuntimeError("non-finite observation from simulation state")
        physical: dict[str, np.ndarray | float] = {
            "los_unit": los_unit.copy(),
            "los_rate_rad_s": los_rate.copy(),
            # `range_m` stays TRUE range: downstream metrics, rollout capture
            # and the viz all read it as ground truth. The observed (possibly
            # stale) range the policy actually saw is reported separately.
            "range_m": self._range(),
            "observed_range_m": range_m,
            "closing_velocity_m_s": closing_velocity,
            "height_above_ground_m": height_above_ground_m,
            "altitude_rate_m_s": altitude_rate_m_s,
            "target_turn_rate_rad_s": target_turn_rate.copy(),
            "tracking_staleness": staleness,
            "tracking_uncertainty": uncertainty,
        }
        return observation, physical

    def _ground_impact_reason(self) -> str | None:
        if self.pursuer is None or self.target is None:
            return None
        if self.pursuer.state.altitude() <= self.ground_altitude_m:
            return "pursuer_ground_impact"
        if self.target.state.altitude() <= self.ground_altitude_m:
            return "target_ground_impact"
        return None

    def _info(
        self,
        *,
        physical: dict[str, np.ndarray | float],
        outcome: str,
        termination_reason: str | None,
        requested: np.ndarray,
        commanded: np.ndarray,
        achieved: np.ndarray,
        action_was_clipped: bool,
        reward_terms: dict[str, float],
    ) -> dict[str, object]:
        return {
            **physical,
            "time_s": self.time_s,
            "min_range_m": self.min_range_m,
            "closest_approach_m": self.closest_approach_m,
            "outcome": outcome,
            "termination_reason": termination_reason,
            "hit": outcome == "hit",
            "miss": outcome == "miss",
            "timeout": outcome == "timeout",
            "action_requested_m_s2": requested.copy(),
            "action_commanded_m_s2": commanded.copy(),
            "action_achieved_m_s2": achieved.copy(),
            "action_was_clipped": action_was_clipped,
            "action_layout": self.action_layout,
            "reward_terms": reward_terms.copy(),
            "legacy_reward": reward_terms.get("legacy_total", 0.0),
            "legacy_episode_reward": self._episode_legacy_reward,
        }
