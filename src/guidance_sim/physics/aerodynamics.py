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
