"""
Vehicle entities.

- `RigidBodyEntity`: the 6-DOF core. It has a 13-state rigid body driven
  by forces and moments through a cascaded autopilot and rate-limited
  actuators.
- `PointMassEntity`: the original 3-DOF model. It is kept as the
  reference the 6-DOF model is regression-tested against, and as the
  cheap plant `InterceptionEnv` on `feature/rl-training` still builds.
  See docs/rl-interface-6dof.md for the swap.

Both expose the same public surface: `state` (world-frame `State`),
`vehicle`, `last_achieved_lateral_accel`, and
`step(dt, lateral_accel_cmd, integrator, autopilot_tau)`. The engine, the
guidance laws and the maneuvers don't care which one they get.

Axis convention: z is up (altitude); gravity acts along -z.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import Optional

import numpy as np

from guidance_sim.physics.aerodynamics import AeroDerivatives, wind_angles
from guidance_sim.physics.controls import N_CONTROLS, ActuatorLimits, actuator_step
from guidance_sim.physics.dynamics import (
    autopilot_deflection_command,
    clamp_lateral_command,
    net_acceleration,
    rigid_body_derivative,
    specific_force_lateral_world,
)
from guidance_sim.physics.integrator import IntegratorType, integrate, integrate_state
from guidance_sim.physics.rotational_dynamics import (
    C_WN,
    body_to_world_matrix,
    inertia_tensor,
    quat_from_euler,
    quat_to_euler,
    quat_to_rotation_matrix,
)

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


_SLUG_FT2 = 1.3558179  # kg·m² per slug·ft²
_FT = 0.3048
_DEG = np.pi / 180.0


@dataclass(frozen=True)
class RigidBodyParams:
    """Everything a 6-DOF airframe needs beyond the point-mass `VehicleParams`."""

    vehicle: VehicleParams  # mass, S, CD0, Cn_max (alpha limit), g-limit (command clamp)
    inertia: np.ndarray  # (3, 3) body-axis, kg·m²
    aero: AeroDerivatives
    actuators: ActuatorLimits
    bank_to_turn: bool  # True: aircraft rolls lift onto the command. False: skid-to-turn missile.
    max_thrust: float = 0.0  # N, along body x
    tvc_arm_m: float = 0.0  # nozzle distance aft of CG
    # Autopilot gains (1/s): rate loop, alpha/beta loop, bank loop.
    k_rate: float = 10.0
    k_alpha: float = 4.0
    k_bank: float = 2.0

    @cached_property
    def inertia_inv(self) -> np.ndarray:
        return np.linalg.inv(self.inertia)


# --- Fighter target: F-16 class ------------------------------------------------
# Mass/geometry/inertia: Stevens & Lewis, *Aircraft Control and Simulation*
# (2nd ed., Table 3.6-3), from NASA TP-1538 (Nguyen et al., 1979):
#   W = 20,500 lb; S = 300 ft²; b = 30 ft; c̄ = 11.32 ft;
#   Ixx = 9,496, Iyy = 55,814, Izz = 63,100, Ixz = 982 slug·ft².
# Engine gyroscopic momentum (160 slug·ft²/s) is NOT modelled.
# Aero: linearised from the same NASA TP-1538 tables near alpha = 0, and
# transcribed from memory of the textbook, so check before relying on digits:
#   CY = -0.02·β(deg) + 0.086·δr/30°  -> cy_beta = -1.146, cy_dr = 0.164 /rad
#   CZ δe term -0.19·δe/25°           -> CZ_de = -0.435 /rad
#   CZ(α) slope 0-10 deg               -> cl_alpha ≈ 3.6 /rad
#   damping table at α=0: Clp -0.443, Cmq -5.23, Cnr -0.378
# Derived / PLACEHOLDER (flagged):
#   c_pitch_alpha = CZα·(0.30 - 0.35)c̄ ≈ -0.18: static margin for xcg = 0.30c̄
#       against the 0.35c̄ reference; the tabulated Cm(α) is nearly flat.
#   c_pitch_de = CZ_de × assumed 1.5c̄ tail arm ≈ -0.65 (PLACEHOLDER arm).
#   c_roll_beta -0.1, c_yaw_beta +0.2, c_roll_da 0.117, c_roll_dr 0.019,
#       c_yaw_dr -0.069: order-of-magnitude reads of the Cl/Cn and control
#       tables at α = β = 0 (PLACEHOLDER precision).
#   alpha_stall 25°, CD0 0.02, Cn_max 1.5: approximate; the F-16 table has
#       no sharp stall, and our flat-plate blend is conservative post-stall.
# Actuators, surfaces (NASA TP-1538 / Stevens & Lewis F-16 model): elevator
#   ±25° at 60°/s, aileron ±21.5° at 80°/s, rudder ±30° at 120°/s, all with
#   a 0.0495 s first-order lag.
# Thrust vectoring (not on a stock F-16; represents the F-16 MATV/VISTA-style
#   axisymmetric nozzle the Cobra needs): ±20° at 60°/s, 6 m arm are
#   PLACEHOLDERS. Max thrust 129 kN = F100-PW-229 max afterburner (published
#   static sea-level rating; no altitude/Mach lapse modelled).
_F16_MASS = 20_500 * 0.45359237
F16_6DOF = RigidBodyParams(
    vehicle=VehicleParams(
        mass=_F16_MASS,
        reference_area=300 * _FT ** 2,
        drag_coefficient=0.02,
        max_normal_force_coefficient=1.5,
        max_load_factor=9.0,
    ),
    inertia=inertia_tensor(9_496 * _SLUG_FT2, 55_814 * _SLUG_FT2, 63_100 * _SLUG_FT2, 982 * _SLUG_FT2),
    aero=AeroDerivatives(
        span=30 * _FT, chord=11.32 * _FT,
        cl_alpha=3.6, alpha_stall=25 * _DEG, k_induced=0.1,
        cy_beta=-1.146, cy_dr=0.164,
        c_pitch_alpha=-0.18, c_pitch_q=-5.23, c_pitch_de=-0.65,
        c_roll_beta=-0.1, c_roll_p=-0.443, c_roll_da=0.117, c_roll_dr=0.019,
        c_yaw_beta=0.2, c_yaw_r=-0.378, c_yaw_dr=-0.069,
    ),
    actuators=ActuatorLimits(
        max_deflection=(25 * _DEG, 21.5 * _DEG, 30 * _DEG, 20 * _DEG, 20 * _DEG),
        max_rate=(60 * _DEG, 80 * _DEG, 120 * _DEG, 60 * _DEG, 60 * _DEG),
        time_constant=(0.0495, 0.0495, 0.0495, 0.05, 0.05),
    ),
    bank_to_turn=True,
    max_thrust=129_000.0,
    tvc_arm_m=6.0,
    k_rate=6.0,
    k_alpha=3.0,
    k_bank=2.5,
)


# --- Interceptor: generic tail-controlled cruciform missile --------------------
# AGENTS.md §3 keeps interceptor data generic. No real missile's inertia or
# derivatives are used. Everything below is DERIVED from the project's
# existing illustrative 50 kg / 0.05 m² airframe with textbook formulas, or
# is a PLACEHOLDER in a typical published range:
#   d = sqrt(4S/pi) = 0.252 m; length 2.5 m (PLACEHOLDER, L/d ≈ 10).
#   Inertia: uniform solid cylinder, Ixx = m r²/2, Iyy = Izz = m(3r² + L²)/12.
#   cl_alpha (CNα, per body cross-section) 35/rad: PLACEHOLDER, typical
#       finned-missile range 20-40/rad. k_induced = 1/CNα is the normal-force
#       tilt approximation (CD_i ≈ CN·α).
#   Static margin 1 calibre -> c_pitch_alpha = -CNα = -35.
#   Tail fins: CNα_fin 8/rad at 4.5 calibres aft -> c_pitch_de ≈ -36;
#       Cmq ≈ -2·CNα_fin·(4.5)² ≈ -324 -> -350 incl. body (slender-body fin
#       damping estimate, e.g. Fleeman, *Tactical Missile Design*, ch. 2).
#   Roll: c_roll_p -20, c_roll_da 6 (PLACEHOLDER).
#   Yaw plane mirrors pitch plane (cruciform symmetry).
#   Fin actuators ±25°, 400°/s, 0.02 s lag: PLACEHOLDER inside the commonly
#       quoted 300-600°/s electromechanical fin-actuator band.
#   alpha_stall 35°: kept above the Cn_max/CNα ≈ 24.5° command limit so the
#       wing-derived flat-plate blend never engages in normal flight.
_MSL_MASS, _MSL_AREA, _MSL_LENGTH = 50.0, 0.05, 2.5
_MSL_RADIUS = float(np.sqrt(_MSL_AREA / np.pi))
INTERCEPTOR_6DOF = RigidBodyParams(
    vehicle=VehicleParams(
        mass=_MSL_MASS,
        reference_area=_MSL_AREA,
        drag_coefficient=0.3,
        max_normal_force_coefficient=15.0,
        max_load_factor=25.0,
    ),
    inertia=inertia_tensor(
        0.5 * _MSL_MASS * _MSL_RADIUS ** 2,
        _MSL_MASS * (3 * _MSL_RADIUS ** 2 + _MSL_LENGTH ** 2) / 12,
        _MSL_MASS * (3 * _MSL_RADIUS ** 2 + _MSL_LENGTH ** 2) / 12,
    ),
    aero=AeroDerivatives(
        span=2 * _MSL_RADIUS, chord=2 * _MSL_RADIUS,
        cl_alpha=35.0, alpha_stall=35 * _DEG, k_induced=1 / 35.0,
        cy_beta=-35.0, cy_dr=0.0,
        c_pitch_alpha=-35.0, c_pitch_q=-350.0, c_pitch_de=-36.0,
        c_roll_beta=0.0, c_roll_p=-20.0, c_roll_da=6.0, c_roll_dr=0.0,
        c_yaw_beta=35.0, c_yaw_r=-350.0, c_yaw_dr=-36.0,
    ),
    actuators=ActuatorLimits(
        max_deflection=(25 * _DEG, 25 * _DEG, 25 * _DEG, 0.0, 0.0),
        max_rate=(400 * _DEG,) * 3 + (0.0, 0.0),
        time_constant=(0.02,) * 3 + (0.0, 0.0),
    ),
    bank_to_turn=False,
    k_rate=25.0,
    k_alpha=12.0,
)


@dataclass
class RigidBodyEntity:
    """
    6-DOF rigid body. `x` is the integrated 13-state:

        x = [p_W (3), v_B (3), q_NB (4), omega_B (3)]

    - p_W: world z-up position, the same frame as `State.position`.
    - v_B: velocity in BODY FRD axes, NOT world. World velocity is
      `R_WB @ v_B`, where `R_WB = body_to_world_matrix(q)`.
      `self.state.velocity` is that world vector, re-synced after every step.
      Never write `state` expecting it to reach the dynamics; use
      `from_state` / `set_state`.
    - q_NB: Hamilton unit quaternion, body -> NED-style local frame
      (see rotational_dynamics.py). Renormalised after every step.
    - omega_B: body rates p, q, r (rad/s).

    `step` has the `PointMassEntity` signature. `lateral_accel_cmd` is the
    outer-loop command (world frame, gravity excluded, same clamp), which
    the autopilot tracks through the actuators. Set `rate_cmd` to bypass the
    accel loops and command body rates directly (scripted attitude
    maneuvers). `autopilot_tau` is accepted and ignored: the lag it stood in
    for now emerges from inertia, actuators and autopilot bandwidth.
    """

    name: str
    state: State
    params: RigidBodyParams
    x: np.ndarray = field(default_factory=lambda: np.zeros(13))
    deflection: np.ndarray = field(default_factory=lambda: np.zeros(N_CONTROLS))
    throttle: float = 0.0
    rate_cmd: Optional[np.ndarray] = None
    last_achieved_lateral_accel: np.ndarray = field(default_factory=lambda: _ZERO3.copy())

    @classmethod
    def from_state(
        cls,
        state: State,
        params: RigidBodyParams,
        name: str = "vehicle",
        throttle: float = 0.0,
    ) -> "RigidBodyEntity":
        entity = cls(name=name, state=state.copy(), params=params, throttle=throttle)
        entity.set_state(state)
        return entity

    def set_state(self, state: State, roll: float = 0.0) -> None:
        """Nose along velocity (alpha = beta = 0), given roll, zero body rates."""
        v = state.velocity
        theta = float(np.arctan2(v[2], np.hypot(v[0], v[1])))
        psi = float(np.arctan2(-v[1], v[0])) if np.hypot(v[0], v[1]) > 1e-9 else 0.0
        q = quat_from_euler(roll, theta, psi)
        v_b = quat_to_rotation_matrix(q).T @ (C_WN @ v)
        self.x = np.concatenate([state.position, v_b, q, np.zeros(3)])
        self._sync_state()

    @property
    def vehicle(self) -> VehicleParams:
        return self.params.vehicle

    def _sync_state(self) -> None:
        self.state.position = self.x[0:3].copy()
        self.state.velocity = body_to_world_matrix(self.x[6:10]) @ self.x[3:6]

    # --- telemetry -------------------------------------------------------------
    def euler_angles(self) -> tuple[float, float, float]:
        """(roll phi, pitch theta, heading psi), rad. psi is clockwise from +x_W seen from above."""
        return quat_to_euler(self.x[6:10])

    def rotation_matrix_world(self) -> np.ndarray:
        """R_WB (3x3): columns are nose, right wing, belly in world z-up axes (for the 3D viewer)."""
        return body_to_world_matrix(self.x[6:10])

    def body_axis(self) -> np.ndarray:
        return self.rotation_matrix_world()[:, 0]

    def body_up(self) -> np.ndarray:
        return -self.rotation_matrix_world()[:, 2]

    def wind_angles(self) -> tuple[float, float, float]:
        """(V, alpha, beta) from body velocity."""
        return wind_angles(self.x[3:6])

    # --- propagation -----------------------------------------------------------
    def step(
        self,
        dt: float,
        lateral_accel_cmd: np.ndarray,
        integrator: IntegratorType = IntegratorType.RK4,
        autopilot_tau: float = 0.0,
    ) -> None:
        del autopilot_tau  # emergent now; see class docstring
        p = self.params
        thrust = float(np.clip(self.throttle, 0.0, 1.0)) * p.max_thrust
        cmd = _ZERO3
        if self.rate_cmd is None:
            cmd = clamp_lateral_command(
                velocity=self.state.velocity,
                lateral_accel_cmd=np.asarray(lateral_accel_cmd, dtype=float).reshape(3),
                altitude_m=self.state.altitude(),
                reference_area=p.vehicle.reference_area,
                drag_coefficient=p.vehicle.drag_coefficient,
                max_normal_force_coefficient=p.vehicle.max_normal_force_coefficient,
                mass=p.vehicle.mass,
                max_load_factor=p.vehicle.max_load_factor,
            )
        deflection_cmd = autopilot_deflection_command(self.x, p, cmd, thrust, self.rate_cmd)
        self.deflection = actuator_step(self.deflection, deflection_cmd, dt, p.actuators)

        deflection = self.deflection
        x = integrate_state(
            self.x, lambda y: rigid_body_derivative(y, p, deflection, thrust), dt, method=integrator
        )
        x[6:10] /= np.linalg.norm(x[6:10])  # RK4 drifts |q| off 1; renormalise every step, explicitly
        self.x = x
        self._sync_state()
        self.last_achieved_lateral_accel = specific_force_lateral_world(x, p, deflection, thrust)
