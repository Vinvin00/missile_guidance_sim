"""Gymnasium environment for the existing 3D point-mass engagement.

The observation is a ten-element, ``float32`` vector in this exact order:

``[r_hat_x, r_hat_y, r_hat_z, omega_x_s, omega_y_s, omega_z_s,
range_s, closing_s, height_agl_s, altitude_rate_s]``.

``r_hat`` is the world-frame target-from-pursuer LOS unit vector.  A unit
vector is used instead of azimuth/elevation so the 3D representation has no
angle wrap or pole singularity.  The remaining values are bounded,
dimensionless transforms of physical quantities:

* ``omega_s = tanh(omega_los / 0.1 rad/s)``, where
  ``omega_los = cross(r_rel, v_rel) / range**2``;
* ``range_s = range / (range + 10_000 m)``;
* ``closing_s = tanh(closing_velocity / 1_000 m/s)``, where positive means
  closing;
* ``height_agl_s = max(height_above_ground, 0) /
  (max(height_above_ground, 0) + 5_000 m)``;
* ``altitude_rate_s = tanh(pursuer_vz / 200 m/s)``.

Height above the environment's configurable ground plane is more useful than
raw world ``z`` when ``ground_altitude_m`` is nonzero.  It and pursuer vertical
speed make ground proximity observable without changing the physics model.

The action is a world-frame acceleration request in m/s^2 with shape ``(3,)``.
Its Euclidean norm is radially projected to the pursuer structural limit
(``max_load_factor * g0``).  The resulting command is then passed unchanged
to :meth:`PointMassEntity.step`, which applies the existing first-order
autopilot lag, velocity-normal projection, aerodynamic limit, structural
limit, and configured integrator.

Reward per step is:

``(R_before - R_after) / 100 m
  - 1.0 * dt * (||a_commanded|| / a_structural_max)**2
  + terminal_term``

where ``terminal_term`` is ``+100`` for intercept and ``-100`` for either a
physical miss (ground impact) or timeout.  Effort uses the norm-bounded
command before lag/clamp so a policy cannot avoid cost by demanding control
that the actuator cannot achieve.  Multiplication by ``dt`` makes this an
integrated effort cost rather than a control-rate-dependent per-step cost.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import ManeuverProfile, NoManeuver
from guidance_sim.simulation.engine import SimulationConfig

LOS_RATE_SCALE_RAD_S = 0.1
RANGE_SCALE_M = 10_000.0
CLOSING_SPEED_SCALE_M_S = 1_000.0
ALTITUDE_SCALE_M = 5_000.0
ALTITUDE_RATE_SCALE_M_S = 200.0
_KINEMATIC_EPS = 1e-9

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

InitialConditionSampler = Callable[[np.random.Generator], tuple[State, State]]
ManeuverFactory = Callable[[np.random.Generator], ManeuverProfile]


@dataclass(frozen=True)
class RewardConfig:
    """Numerically conservative Phase-1 reward scales."""

    progress_scale_m: float = 100.0
    effort_weight: float = 1.0
    intercept_bonus: float = 100.0
    miss_penalty: float = 100.0
    timeout_penalty: float = 100.0

    def __post_init__(self) -> None:
        values = (
            self.progress_scale_m,
            self.effort_weight,
            self.intercept_bonus,
            self.miss_penalty,
            self.timeout_penalty,
        )
        if not all(np.isfinite(value) and value > 0.0 for value in values):
            raise ValueError("reward scales and weights must be finite and positive")


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
    ) -> None:
        super().__init__()
        self.config = replace(config) if config is not None else SimulationConfig()
        self.reward_config = reward_config or RewardConfig()
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

        action_bound = np.full(3, self.action_limit_m_s2, dtype=np.float32)
        self.action_space = spaces.Box(
            low=-action_bound,
            high=action_bound,
            dtype=np.float32,
        )
        self.observation_space = spaces.Box(
            low=np.array(
                [-1.0] * 6 + [0.0, -1.0, 0.0, -1.0],
                dtype=np.float32,
            ),
            high=np.ones(10, dtype=np.float32),
            dtype=np.float32,
        )

        self.pursuer: PointMassEntity | None = None
        self.target: PointMassEntity | None = None
        self.target_maneuver: ManeuverProfile | None = None
        self.time_s = 0.0
        self.min_range_m = np.inf
        self._episode_done = True

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

        self.time_s = 0.0
        self.min_range_m = self._range()
        if self.min_range_m <= self.config.intercept_radius:
            raise ValueError("initial range must exceed config.intercept_radius")
        if self._ground_impact_reason() is not None:
            raise ValueError("initial states must be above ground_altitude_m")
        self._episode_done = False

        observation, physical = self._observation()
        return observation, self._info(
            physical=physical,
            outcome="ongoing",
            termination_reason=None,
            requested=np.zeros(3),
            commanded=np.zeros(3),
            achieved=np.zeros(3),
            action_was_clipped=False,
            reward_terms={"progress": 0.0, "effort": 0.0, "terminal": 0.0},
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

        requested = np.asarray(action, dtype=float)
        if requested.shape != (3,):
            raise ValueError(f"action must have shape (3,), got {requested.shape}")
        if not np.all(np.isfinite(requested)):
            raise ValueError("action must contain only finite values")
        commanded, action_was_clipped = self._project_action(requested)

        previous_range = self._range()
        cfg = self.config

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

        current_range = self._range()
        self.min_range_m = min(self.min_range_m, current_range)
        hit = current_range <= cfg.intercept_radius
        ground_reason = self._ground_impact_reason()

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

        reward, reward_terms = self._reward(
            previous_range=previous_range,
            current_range=current_range,
            commanded=commanded,
            outcome=outcome,
        )
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
        info["target_action_commanded_m_s2"] = np.asarray(
            target_command, dtype=float
        ).reshape(3).copy()
        info["target_action_achieved_m_s2"] = (
            self.target.last_achieved_lateral_accel.copy()
        )
        return observation, reward, terminated, truncated, info

    def _project_action(self, requested: np.ndarray) -> tuple[np.ndarray, bool]:
        magnitude = float(np.linalg.norm(requested))
        if magnitude <= self.action_limit_m_s2:
            return requested.copy(), False
        return requested * (self.action_limit_m_s2 / magnitude), True

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
        relative_position = (
            self.target.state.position - self.pursuer.state.position
        )
        relative_velocity = (
            self.target.state.velocity - self.pursuer.state.velocity
        )
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
        if self.pursuer is None:
            raise RuntimeError("environment has not been reset")
        los_unit, los_rate, range_m, closing_velocity = self._kinematics()
        height_above_ground_m = (
            self.pursuer.state.altitude() - self.ground_altitude_m
        )
        nonnegative_height_m = max(height_above_ground_m, 0.0)
        altitude_rate_m_s = float(self.pursuer.state.velocity[2])
        observation = np.concatenate(
            (
                los_unit,
                np.tanh(los_rate / LOS_RATE_SCALE_RAD_S),
                np.array(
                    [
                        range_m / (range_m + RANGE_SCALE_M),
                        np.tanh(
                            closing_velocity / CLOSING_SPEED_SCALE_M_S
                        ),
                        nonnegative_height_m
                        / (nonnegative_height_m + ALTITUDE_SCALE_M),
                        np.tanh(
                            altitude_rate_m_s / ALTITUDE_RATE_SCALE_M_S
                        ),
                    ]
                ),
            )
        )
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
            "range_m": range_m,
            "closing_velocity_m_s": closing_velocity,
            "height_above_ground_m": height_above_ground_m,
            "altitude_rate_m_s": altitude_rate_m_s,
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

    def _reward(
        self,
        *,
        previous_range: float,
        current_range: float,
        commanded: np.ndarray,
        outcome: str,
    ) -> tuple[float, dict[str, float]]:
        reward_cfg = self.reward_config
        progress = (previous_range - current_range) / reward_cfg.progress_scale_m
        normalized_effort = (
            float(np.linalg.norm(commanded)) / self.action_limit_m_s2
        ) ** 2
        effort = -reward_cfg.effort_weight * self.config.dt * normalized_effort
        terminal = 0.0
        if outcome == "hit":
            terminal = reward_cfg.intercept_bonus
        elif outcome == "miss":
            terminal = -reward_cfg.miss_penalty
        elif outcome == "timeout":
            terminal = -reward_cfg.timeout_penalty
        terms = {
            "progress": float(progress),
            "effort": float(effort),
            "terminal": float(terminal),
        }
        return float(sum(terms.values())), terms

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
            "outcome": outcome,
            "termination_reason": termination_reason,
            "hit": outcome == "hit",
            "miss": outcome == "miss",
            "timeout": outcome == "timeout",
            "action_requested_m_s2": requested.copy(),
            "action_commanded_m_s2": commanded.copy(),
            "action_achieved_m_s2": achieved.copy(),
            "action_was_clipped": action_was_clipped,
            "reward_terms": reward_terms.copy(),
        }
