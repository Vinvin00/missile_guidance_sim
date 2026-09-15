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

import numpy as np

# Post-stall coefficient model -- used ONLY by AttitudeAugmentedEntity
# (CobraManeuver). The point-mass path (drag_deceleration /
# available_lateral_accel) is untouched. Generic illustrative values.
CL_ALPHA_PER_RAD = 4.0  # linear lift-curve slope
K_INDUCED = 0.1  # CD = CD0 + K * CL^2 in the linear regime
CD_90 = 1.2  # flat plate normal to flow (Hoerner, Fluid-Dynamic Drag, ~1.17)
ALPHA_STALL_RAD = np.deg2rad(15.0)
STALL_BLEND_WIDTH_RAD = np.deg2rad(2.0)

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


def post_stall_coefficients(alpha: float, cd0: float) -> tuple[float, float]:
    """
    (CL, CD) at any angle of attack (rad, wrapped to [-pi, pi]).

    Linear regime (CL = CLa*alpha, CD = CD0 + K*CL^2) sigmoid-blended
    into flat-plate post-stall behaviour (CL = CD90 sin a cos a,
    CD = CD0 + CD90 sin^2 a) around |alpha| = 15 deg. The sigmoid keeps
    both curves C-infinity through stall: CL collapses, CD rises toward
    flat-plate drag at 90 deg.
    """
    a = float(np.arctan2(np.sin(alpha), np.cos(alpha)))
    w = 1.0 / (1.0 + np.exp(-(abs(a) - ALPHA_STALL_RAD) / STALL_BLEND_WIDTH_RAD))
    cl_lin = CL_ALPHA_PER_RAD * a
    cd_lin = cd0 + K_INDUCED * cl_lin ** 2
    cl_fp = CD_90 * np.sin(a) * np.cos(a)
    cd_fp = cd0 + CD_90 * np.sin(a) ** 2
    return float((1.0 - w) * cl_lin + w * cl_fp), float((1.0 - w) * cd_lin + w * cd_fp)
