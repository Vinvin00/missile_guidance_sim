"""
Combines gravity, aerodynamic drag, and a guidance-commanded lateral
acceleration into the single net acceleration vector the integrator
needs. Kept separate from entities.py so the "what forces act on this
body" question is answered in one obvious place.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.aerodynamics import available_lateral_accel, drag_deceleration
from guidance_sim.physics.atmosphere import G0, isa_density

GRAVITY_VECTOR = np.array([0.0, 0.0, -G0])


def clamp_lateral_command(
    velocity: np.ndarray,
    lateral_accel_cmd: np.ndarray,
    altitude_m: float,
    reference_area: float,
    drag_coefficient: float,
    max_normal_force_coefficient: float,
    mass: float,
    max_load_factor: float,
) -> np.ndarray:
    """
    Project the commanded acceleration onto the plane perpendicular to
    velocity (control surfaces steer, they don't add/remove speed
    directly -- that's what drag/thrust do), then clamp its magnitude
    to what the airframe can actually generate at the current speed
    and altitude.
    """
    speed = float(np.linalg.norm(velocity))
    if speed < 1e-6:
        return np.zeros(3)

    v_hat = velocity / speed
    perpendicular_cmd = lateral_accel_cmd - np.dot(lateral_accel_cmd, v_hat) * v_hat

    magnitude = float(np.linalg.norm(perpendicular_cmd))
    if magnitude < 1e-9:
        return perpendicular_cmd

    rho = isa_density(altitude_m)
    a_max = available_lateral_accel(
        rho=rho,
        speed=speed,
        reference_area=reference_area,
        max_normal_force_coefficient=max_normal_force_coefficient,
        mass=mass,
        max_load_factor=max_load_factor,
    )
    if magnitude > a_max:
        perpendicular_cmd = perpendicular_cmd * (a_max / magnitude)
    return perpendicular_cmd


def net_acceleration(
    position: np.ndarray,
    velocity: np.ndarray,
    frozen_lateral_cmd: np.ndarray,
    reference_area: float,
    drag_coefficient: float,
    mass: float,
) -> np.ndarray:
    """
    Total acceleration = gravity + drag (opposing velocity) + the
    already-clamped, already-perpendicular lateral command (frozen
    for this integration step by the caller).
    """
    speed = float(np.linalg.norm(velocity))
    if speed > 1e-6:
        rho = isa_density(position[2])
        drag_decel = drag_deceleration(rho, speed, drag_coefficient, reference_area, mass)
        drag_accel = -drag_decel * (velocity / speed)
    else:
        drag_accel = np.zeros(3)

    return GRAVITY_VECTOR + drag_accel + frozen_lateral_cmd
