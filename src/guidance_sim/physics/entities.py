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

from guidance_sim.physics.dynamics import clamp_lateral_command, net_acceleration
from guidance_sim.physics.integrator import IntegratorType, integrate

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
