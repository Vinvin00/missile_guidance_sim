"""
3D point-mass entity, propagated by real forces (gravity + drag +
guidance command) rather than the earlier 2D trick of rotating a
constant-speed velocity vector. Speed now changes physically, in any
of the three axes, from day one -- there's no 2D-to-3D migration step
left to do later.

Axis convention: z is up (altitude); gravity acts along -z.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from guidance_sim.physics.dynamics import (
    MAX_PITCH_RATE_RAD_S,
    MAX_ROLL_RATE_RAD_S,
    attitude_net_acceleration,
    clamp_lateral_command,
    clamp_rate,
    flight_path_angle,
    net_acceleration,
)
from guidance_sim.physics.integrator import IntegratorType, integrate, integrate_state

_ZERO3 = np.zeros(3)


@dataclass
class State:
    """3D kinematic state of a point mass."""

    position: np.ndarray  # shape (3,) -> [x, y, z] meters, z = altitude
    velocity: np.ndarray  # shape (3,) -> [vx, vy, vz] m/s

    def __post_init__(self) -> None:
        self.position = np.asarray(self.position, dtype=float).reshape(3)
        self.velocity = np.asarray(self.velocity, dtype=float).reshape(3)

    def speed(self) -> float:
        return float(np.linalg.norm(self.velocity))

    def altitude(self) -> float:
        return float(self.position[2])

    def copy(self) -> "State":
        return State(position=self.position.copy(), velocity=self.velocity.copy())


@dataclass
class VehicleParams:
    """
    Physical/aerodynamic properties of a point-mass vehicle. These are
    generic, illustrative values (not derived from any real airframe)
    -- swap them out per vehicle to compare a nimble drone against a
    heavier, faster interceptor.
    """

    mass: float  # kg
    reference_area: float  # m^2, used for both drag and lift/normal-force calcs
    drag_coefficient: float  # Cd, dimensionless zero-lift drag coefficient
    max_normal_force_coefficient: float  # Cn_max, dimensionless; caps aero-available lateral accel
    max_load_factor: float  # structural g-limit (e.g. 20-30 for a missile, 5-9 for a drone/aircraft)


def lag_step(
    achieved: np.ndarray,
    commanded: np.ndarray,
    dt: float,
    tau: float,
) -> np.ndarray:
    """
    One discrete step of a first-order lag:
        da/dt = (a_cmd - a) / tau
    Exact ZOH map: a ← a + (1 - e^{-dt/tau}) (a_cmd - a).
    tau <= 0 bypasses the filter (a = a_cmd).
    """
    commanded = np.asarray(commanded, dtype=float).reshape(3)
    if tau <= 0.0:
        return commanded.copy()
    alpha = 1.0 - float(np.exp(-dt / tau))
    return achieved + alpha * (commanded - achieved)


@dataclass
class PointMassEntity:
    name: str
    state: State
    vehicle: VehicleParams
    # Post-clamp lateral accel applied on the most recent step (diagnostics).
    last_achieved_lateral_accel: np.ndarray = field(
        default_factory=lambda: _ZERO3.copy()
    )
    # Pre-clamp lag filter state (first-order autopilot).
    _lag_state: np.ndarray = field(default_factory=lambda: _ZERO3.copy())

    def reset_autopilot(self) -> None:
        self._lag_state = _ZERO3.copy()
        self.last_achieved_lateral_accel = _ZERO3.copy()

    def step(
        self,
        dt: float,
        lateral_accel_cmd: np.ndarray,
        integrator: IntegratorType = IntegratorType.RK4,
        autopilot_tau: float = 0.0,
    ) -> None:
        """
        Advance the entity one step under gravity + drag + the given
        guidance/maneuver command.

        Autopilot lag (if autopilot_tau > 0) is applied to the raw
        command *before* clamp; clamp then projects ⊥ velocity and
        caps to available g. The lagged+clamped vector is ZOH'd across
        RK4 stages; gravity/drag recomputed per stage.
        """
        raw_cmd = np.asarray(lateral_accel_cmd, dtype=float).reshape(3)
        lagged = lag_step(self._lag_state, raw_cmd, dt, autopilot_tau)
        self._lag_state = lagged.copy()

        clamped_cmd = clamp_lateral_command(
            velocity=self.state.velocity,
            lateral_accel_cmd=lagged,
            altitude_m=self.state.altitude(),
            reference_area=self.vehicle.reference_area,
            drag_coefficient=self.vehicle.drag_coefficient,
            max_normal_force_coefficient=self.vehicle.max_normal_force_coefficient,
            mass=self.vehicle.mass,
            max_load_factor=self.vehicle.max_load_factor,
        )
        self.last_achieved_lateral_accel = clamped_cmd.copy()

        def accel_fn(position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
            return net_acceleration(
                position=position,
                velocity=velocity,
                frozen_lateral_cmd=clamped_cmd,
                reference_area=self.vehicle.reference_area,
                drag_coefficient=self.vehicle.drag_coefficient,
                mass=self.vehicle.mass,
            )

        new_position, new_velocity = integrate(
            self.state.position, self.state.velocity, accel_fn, dt, method=integrator
        )
        self.state.position = new_position
        self.state.velocity = new_velocity


@dataclass
class AttitudeAugmentedEntity(PointMassEntity):
    """
    3-DOF + attitude (NOT 6-DOF): pitch `theta` and bank `phi` are extra
    integrated states driven by commanded rates through an idealized
    rate autopilot -- no moments, inertia, or control surfaces. Thrust
    acts along the body axis, so it can diverge from velocity.

    While `attitude_active` is False, `step` is exactly the point-mass
    step (no thrust, same drag/clamp path) and attitude just tracks the
    velocity vector. Only `CobraManeuver` flips it on.
    """

    theta: float = 0.0  # pitch, rad
    phi: float = 0.0  # bank, rad
    theta_dot: float = 0.0  # commanded pitch rate, rad/s (ZOH per step)
    phi_dot: float = 0.0  # commanded bank rate, rad/s (ZOH per step)
    # Nose heading (rad). Idealized zero-sideslip yaw autopilot: follows the
    # velocity heading, frozen per step and never flipped by a tail slide.
    psi: float = 0.0
    max_thrust: float = 0.0  # N
    throttle: float = 0.0  # 0..1
    attitude_active: bool = False

    def sync_attitude_to_velocity(self) -> None:
        v = self.state.velocity
        if float(np.hypot(v[0], v[1])) > 1.0:
            self.psi = float(np.arctan2(v[1], v[0]))
        self.theta = flight_path_angle(v, self.psi)
        self.phi = 0.0

    def state_derivative(self, y: np.ndarray) -> np.ndarray:
        """dy/dt for y = [x, y, z, vx, vy, vz, theta, phi]."""
        accel = attitude_net_acceleration(
            position=y[0:3],
            velocity=y[3:6],
            theta=y[6],
            phi=y[7],
            psi=self.psi,
            thrust=self.throttle * self.max_thrust,
            reference_area=self.vehicle.reference_area,
            drag_coefficient=self.vehicle.drag_coefficient,
            mass=self.vehicle.mass,
            max_load_factor=self.vehicle.max_load_factor,
        )
        return np.concatenate([y[3:6], accel, [self.theta_dot, self.phi_dot]])

    def step(
        self,
        dt: float,
        lateral_accel_cmd: np.ndarray,
        integrator: IntegratorType = IntegratorType.RK4,
        autopilot_tau: float = 0.0,
    ) -> None:
        if not self.attitude_active:
            super().step(dt, lateral_accel_cmd, integrator=integrator, autopilot_tau=autopilot_tau)
            self.sync_attitude_to_velocity()
            return

        # Attitude mode: lateral_accel_cmd is ignored; forces come from attitude.
        self.theta_dot = clamp_rate(self.theta_dot, MAX_PITCH_RATE_RAD_S)
        self.phi_dot = clamp_rate(self.phi_dot, MAX_ROLL_RATE_RAD_S)
        v = self.state.velocity
        heading = float(np.arctan2(v[1], v[0]))
        if float(np.hypot(v[0], v[1])) > 1.0 and np.cos(heading - self.psi) > 0.0:
            self.psi = heading
        self.last_achieved_lateral_accel = _ZERO3.copy()

        y = np.concatenate([self.state.position, self.state.velocity, [self.theta, self.phi]])
        y = integrate_state(y, self.state_derivative, dt, method=integrator)
        self.state.position = y[0:3].copy()
        self.state.velocity = y[3:6].copy()
        self.theta, self.phi = float(y[6]), float(y[7])
