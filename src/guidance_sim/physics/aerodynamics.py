"""
Aerodynamic force and maneuver-limit calculations.

These functions turn airspeed + local air density into physical
quantities: dynamic pressure, drag deceleration, and -- critically --
how much lateral ("normal") acceleration the airframe can actually
generate at a given flight condition. Real vehicles can't pull
constant g regardless of speed and altitude; maneuverability is a
function of dynamic pressure and airframe design, capped by
structural g-limits. Modeling that (even in simplified form) is what
separates "realistic" from the earlier kinematic turn-model scaffold.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Default post-stall coefficient model. RigidBodyEntity vehicles override
# slope/stall/induced drag per airframe via AeroDerivatives. The point-mass
# path (drag_deceleration / available_lateral_accel) is untouched.
CL_ALPHA_PER_RAD = 4.0  # linear lift-curve slope
K_INDUCED = 0.1  # CD = CD0 + K * CL^2 in the linear regime
CD_90 = 1.2  # flat plate normal to flow (Hoerner, Fluid-Dynamic Drag, ~1.17)
ALPHA_STALL_RAD = np.deg2rad(15.0)
STALL_BLEND_WIDTH_RAD = np.deg2rad(2.0)


@dataclass(frozen=True)
class MachAeroSchedule:
    """Piecewise-linear Mach corrections for the attached airframe.

    The schedule scales the vehicle's low-speed zero-lift drag and normal-
    force slope.  Values outside the tabulated range use the nearest endpoint;
    silent extrapolation is deliberately avoided because these reduced-order
    tables are not valid outside their stated envelope.
    """

    mach: tuple[float, ...]
    cd0_multiplier: tuple[float, ...]
    normal_force_slope_multiplier: tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.mach)
        if (
            n < 2
            or len(self.cd0_multiplier) != n
            or len(self.normal_force_slope_multiplier) != n
        ):
            raise ValueError("Mach schedule arrays must have the same length (at least two points)")
        if not np.all(np.diff(self.mach) > 0.0):
            raise ValueError("Mach breakpoints must be strictly increasing")
        if min(self.mach) < 0.0:
            raise ValueError("Mach breakpoints cannot be negative")
        if min(self.cd0_multiplier) <= 0.0 or min(self.normal_force_slope_multiplier) <= 0.0:
            raise ValueError("Mach coefficient multipliers must be positive")

    def coefficients(self, mach: float) -> tuple[float, float]:
        """Return ``(CD0 scale, normal-force-slope scale)`` at ``mach``."""
        m = max(float(mach), 0.0)
        cd_scale = np.interp(m, self.mach, self.cd0_multiplier)
        cn_scale = np.interp(m, self.mach, self.normal_force_slope_multiplier)
        return float(cd_scale), float(cn_scale)


def dynamic_pressure(rho: float, speed: float) -> float:
    """q = 1/2 * rho * V^2 (Pa)."""
    return 0.5 * rho * speed ** 2


def drag_deceleration(rho: float, speed: float, drag_coefficient: float,
                       reference_area: float, mass: float) -> float:
    """
    Magnitude of the deceleration (m/s^2) due to aerodynamic drag,
    directed opposite the velocity vector. F_drag = q * Cd * A.
    """
    q = dynamic_pressure(rho, speed)
    drag_force = q * drag_coefficient * reference_area
    return drag_force / mass


def available_lateral_accel(
    rho: float,
    speed: float,
    reference_area: float,
    max_normal_force_coefficient: float,
    mass: float,
    max_load_factor: float,
    g0: float = 9.80665,
) -> float:
    """
    Maximum lateral ("normal") acceleration the airframe can generate
    right now, in m/s^2. Two independent limits are combined:

    1. Aerodynamic limit: the airframe can only generate as much
       normal force as dynamic pressure and its max normal-force
       coefficient allow -- this is why maneuverability collapses at
       low speed/altitude (low q) even for an airframe rated for
       high g.
    2. Structural limit: a flat g-limit (`max_load_factor`) the
       airframe must never exceed regardless of how much q is
       available, representing structural/pilot-system limits.

    The binding (smaller) constraint wins, which is exactly how real
    aircraft/missile "g-available" envelopes are usually reasoned
    about in simplified 3-DOF simulations.
    """
    q = dynamic_pressure(rho, speed)
    aero_limit = (q * reference_area * max_normal_force_coefficient) / mass
    structural_limit = max_load_factor * g0
    return min(aero_limit, structural_limit)


def post_stall_coefficients(
    alpha: float,
    cd0: float,
    cl_alpha: float = CL_ALPHA_PER_RAD,
    alpha_stall: float = ALPHA_STALL_RAD,
    k_induced: float = K_INDUCED,
    mach: float = 0.0,
    mach_schedule: MachAeroSchedule | None = None,
) -> tuple[float, float]:
    """
    (CL, CD) at any angle of attack (rad, wrapped to [-pi, pi]).

    Linear regime (CL = CLa*alpha, CD = CD0 + K*CL^2) sigmoid-blended
    into flat-plate post-stall behaviour (CL = CD90 sin a cos a,
    CD = CD0 + CD90 sin^2 a) around |alpha| = alpha_stall (default 15 deg). The sigmoid keeps
    both curves C-infinity through stall: CL collapses, CD rises toward
    flat-plate drag at 90 deg.
    """
    a = float(np.arctan2(np.sin(alpha), np.cos(alpha)))
    w = 1.0 / (1.0 + np.exp(-(abs(a) - alpha_stall) / STALL_BLEND_WIDTH_RAD))
    cd_scale, cn_scale = (1.0, 1.0)
    if mach_schedule is not None:
        cd_scale, cn_scale = mach_schedule.coefficients(mach)
    cl_lin = cl_alpha * cn_scale * a
    cd_lin = cd0 * cd_scale + k_induced * cl_lin ** 2
    cl_fp = CD_90 * np.sin(a) * np.cos(a)
    cd_fp = cd0 + CD_90 * np.sin(a) ** 2
    return float((1.0 - w) * cl_lin + w * cl_fp), float((1.0 - w) * cd_lin + w * cd_fp)


@dataclass(frozen=True)
class AeroDerivatives:
    """
    Stability and control derivatives for a 6-DOF airframe, per radian.

    Rate derivatives use the Stevens & Lewis non-dimensionalisation:
    p, r scaled by span/(2V) and q by chord/(2V). Missiles use body
    diameter for both reference lengths. Rolling-moment terms are
    `c_roll_*` so they can't be confused with lift CL.

    Sign conventions: positive elevator gives nose-down (c_pitch_de < 0).
    Positive rudder gives nose-left (c_yaw_dr < 0) and a right side force.
    Positive aileron gives right-wing-down (c_roll_da > 0).
    """

    span: float  # m, lateral reference length
    chord: float  # m, longitudinal reference length
    cl_alpha: float
    alpha_stall: float  # rad
    k_induced: float
    cy_beta: float
    cy_dr: float
    c_pitch_alpha: float  # applied as c_pitch_alpha * sin(alpha): linear near 0, bounded post-stall
    c_pitch_q: float
    c_pitch_de: float
    c_roll_beta: float
    c_roll_p: float
    c_roll_da: float
    c_roll_dr: float
    c_yaw_beta: float
    c_yaw_r: float
    c_yaw_dr: float
    mach_schedule: MachAeroSchedule | None = None


def wind_angles(v_body: np.ndarray) -> tuple[float, float, float]:
    """(V, alpha, beta) from body FRD velocity. alpha in (-pi, pi], so tail slides are representable."""
    speed = float(np.linalg.norm(v_body))
    if speed < 1e-9:
        return 0.0, 0.0, 0.0
    alpha = float(np.arctan2(v_body[2], v_body[0]))
    beta = float(np.arcsin(np.clip(v_body[1] / speed, -1.0, 1.0)))
    return speed, alpha, beta


def body_aero_force(
    v_body: np.ndarray,
    rho: float,
    reference_area: float,
    cd0: float,
    aero: AeroDerivatives,
    rudder: float = 0.0,
    mach: float = 0.0,
) -> np.ndarray:
    """
    Aerodynamic force (N) in body FRD axes.

    Drag acts along -v. Lift is perpendicular to v in the body x-z plane.
    Side force is perpendicular to both. CL/CD come from
    `post_stall_coefficients` at any alpha. Induced drag also charges the
    side force, K*CY^2, so a skid-to-turn missile pays for yaw-plane g too.
    """
    speed, alpha, beta = wind_angles(v_body)
    if speed < 1e-6:
        return np.zeros(3)
    v_hat = v_body / speed
    lift_dir = np.cross([0.0, 1.0, 0.0], v_hat)
    norm = float(np.linalg.norm(lift_dir))
    lift_dir = lift_dir / norm if norm > 1e-6 else np.array([0.0, 0.0, -1.0])
    side_dir = np.cross(v_hat, lift_dir)

    cl, cd = post_stall_coefficients(
        alpha,
        cd0,
        aero.cl_alpha,
        aero.alpha_stall,
        aero.k_induced,
        mach,
        aero.mach_schedule,
    )
    cy = aero.cy_beta * beta + aero.cy_dr * rudder
    cd += aero.k_induced * cy ** 2
    qs = dynamic_pressure(rho, speed) * reference_area
    return qs * (-cd * v_hat + cl * lift_dir + cy * side_dir)
