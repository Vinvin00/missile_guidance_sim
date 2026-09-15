"""
Combines gravity, aerodynamic drag, and a guidance-commanded lateral
acceleration into the single net acceleration vector the integrator
needs. Kept separate from entities.py so the "what forces act on this
body" question is answered in one obvious place.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.aerodynamics import (
    available_lateral_accel,
    drag_deceleration,
    dynamic_pressure,
    post_stall_coefficients,
)
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


# Idealized attitude-rate autopilot bounds (AttitudeAugmentedEntity only).
# ponytail: generic illustrative values, NOT a sourced airframe figure --
# AGENTS.md §3 keeps vehicle parameters generic, and no verifiable open-
# literature max pitch rate was pinned down. Candidate source to check before
# replacing: NASA TM-104322 (X-31A high-AoA handling qualities, 1996).
MAX_PITCH_RATE_RAD_S = np.deg2rad(60.0)
MAX_ROLL_RATE_RAD_S = np.deg2rad(90.0)
_V_EPS = 1.0  # m/s; below this the velocity direction is undefined


def clamp_rate(rate_cmd: float, max_rate: float) -> float:
    """Rate-achieving autopilot: commanded rate is achieved, up to +-max_rate."""
    return float(np.clip(rate_cmd, -max_rate, max_rate))


def flight_path_angle(velocity: np.ndarray, psi: float) -> float:
    """
    gamma = atan2(vz, horizontal speed), with horizontal speed signed
    along the nose heading `psi` so a tail slide gives |gamma| > 90 deg
    instead of silently flipping the nose.
    """
    u_h = velocity[0] * np.cos(psi) + velocity[1] * np.sin(psi)
    return float(np.arctan2(velocity[2], u_h))


def attitude_net_acceleration(
    position: np.ndarray,
    velocity: np.ndarray,
    theta: float,
    phi: float,
    psi: float,
    thrust: float,
    reference_area: float,
    drag_coefficient: float,
    mass: float,
    max_load_factor: float,
) -> np.ndarray:
    """
    3-DOF + attitude force balance (point-mass aircraft EOM, e.g. Miele,
    *Flight Mechanics*; Vinh, *Flight Mechanics of High-Performance Aircraft*):

    - drag along -v_hat, lift perpendicular to v, both from
      post_stall_coefficients(alpha = theta - gamma) and q = 1/2 rho V^2;
    - lift plane rotated about v_hat by bank phi;
    - thrust along the body axis, cos(a) v_hat + sin(a) l_hat -- i.e. NOT
      along velocity. At high alpha q -> 0 kills aero while thrust and
      gravity remain; that is the whole hang/fall mechanism.

    Aero accel magnitude capped at max_load_factor * g (structural limit).
    """
    body_from_attitude = np.array(
        [np.cos(theta) * np.cos(psi), np.cos(theta) * np.sin(psi), np.sin(theta)]
    )
    speed = float(np.linalg.norm(velocity))
    if speed < _V_EPS:
        return GRAVITY_VECTOR + (thrust / mass) * body_from_attitude

    v_hat = velocity / speed
    side_ref = np.array([np.sin(psi), -np.cos(psi), 0.0])  # right wing, level
    n0 = np.cross(side_ref, v_hat)  # "up" perpendicular to v in the nose plane
    n_norm = float(np.linalg.norm(n0))
    if n_norm < 1e-6:  # velocity purely sideways to the nose plane
        return GRAVITY_VECTOR + (thrust / mass) * body_from_attitude
    n0 /= n_norm
    lift_hat = np.cos(phi) * n0 + np.sin(phi) * np.cross(v_hat, n0)

    alpha = theta - flight_path_angle(velocity, psi)
    cl, cd = post_stall_coefficients(alpha, drag_coefficient)
    q = dynamic_pressure(isa_density(position[2]), speed)
    aero = (q * reference_area / mass) * (cl * lift_hat - cd * v_hat)
    aero_mag = float(np.linalg.norm(aero))
    aero_cap = max_load_factor * G0
    if aero_mag > aero_cap:
        aero *= aero_cap / aero_mag

    body_hat = np.cos(alpha) * v_hat + np.sin(alpha) * lift_hat
    return GRAVITY_VECTOR + aero + (thrust / mass) * body_hat
