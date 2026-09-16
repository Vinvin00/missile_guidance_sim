"""
Combines gravity, aerodynamic drag, and a guidance-commanded lateral
acceleration into the single net acceleration vector the integrator
needs. Kept separate from entities.py so the "what forces act on this
body" question is answered in one obvious place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import numpy as np

from guidance_sim.physics.aero_moments import body_aero_moment, control_effectiveness, thrust_force_moment
from guidance_sim.physics.aerodynamics import (
    available_lateral_accel,
    body_aero_force,
    drag_deceleration,
    wind_angles,
)
from guidance_sim.physics.atmosphere import G0, isa_density
from guidance_sim.physics.controls import RUDDER
from guidance_sim.physics.rotational_dynamics import (
    C_WN,
    angular_acceleration,
    quat_derivative,
    quat_to_rotation_matrix,
)

if TYPE_CHECKING:
    from guidance_sim.physics.entities import RigidBodyParams

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


# Pilot/FCS body-rate command limits for scripted attitude maneuvers (Cobra).
# These bound the *command*; achieved rates come from moments and inertia.
# ponytail: generic illustrative values, NOT a sourced airframe figure --
# no verifiable open-literature FCS rate limit was pinned down. Candidate
# source to check: NASA TM-104322 (X-31A high-AoA handling qualities, 1996).
MAX_PITCH_RATE_RAD_S = np.deg2rad(60.0)
MAX_ROLL_RATE_RAD_S = np.deg2rad(90.0)

GRAVITY_N = np.array([0.0, 0.0, G0])  # NED-style local frame, z down
_V_MIN_AUTOPILOT = 5.0  # m/s; below this the accel loops have no meaning


def rigid_body_derivative(
    x: np.ndarray,
    params: "RigidBodyParams",
    deflection: np.ndarray,
    thrust: float,
) -> np.ndarray:
    """
    dx/dt for the 13-state rigid body x = [p_W(3), v_B(3), q_NB(4), w_B(3)].

        p_W_dot = C_WN · R_NB · v_B                  (world z-up position)
        v_B_dot = F_B/m - w × v_B                    (body-frame velocity!)
        q_dot   = 1/2 q ⊗ [0, w]                     (Hamilton)
        w_dot   = I^-1 (M - w × I·w)                 (Euler's equations)

    F_B = aero + thrust + R_NB^T·m·g_N. Frames: see rotational_dynamics.py.
    Deflection and thrust are zero-order-held by the caller.
    """
    v_b, q, w = x[3:6], x[6:10], x[10:13]
    q = q / np.linalg.norm(q)
    r_nb = quat_to_rotation_matrix(q)
    vp = params.vehicle
    rho = isa_density(x[2])

    thrust_f, thrust_m = thrust_force_moment(thrust, params.tvc_arm_m, deflection)
    force = (
        body_aero_force(v_b, rho, vp.reference_area, vp.drag_coefficient, params.aero, deflection[RUDDER])
        + thrust_f
        + vp.mass * (r_nb.T @ GRAVITY_N)
    )
    moment = body_aero_moment(v_b, w, rho, vp.reference_area, params.aero, deflection) + thrust_m

    return np.concatenate([
        C_WN @ (r_nb @ v_b),
        force / vp.mass - np.cross(w, v_b),
        quat_derivative(q, w),
        angular_acceleration(params.inertia, w, moment, params.inertia_inv),
    ])


def autopilot_deflection_command(
    x: np.ndarray,
    params: "RigidBodyParams",
    lateral_accel_cmd: np.ndarray,
    thrust: float,
    rate_cmd: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Cascaded inner loop: outer guidance command -> body rates -> moments ->
    deflections. Runs once per control tick (ZOH), like the old lag model.

    1. Accel -> rates (skipped if `rate_cmd` is given, e.g. Cobra):
       rate feedforward = the turn rate of the velocity vector,
       v × (a_cmd + g)/V^2 in body axes, plus alpha/beta error feedback.
       The alpha/beta commands invert the linear lift slope.
       - skid-to-turn (missile): alpha from the up component, beta from
         the side component, roll rate held at 0.
       - bank-to-turn (aircraft): roll the lift vector onto the command,
         alpha from the component along the current lift axis, beta -> 0.
    2. Rates -> moment by inverse dynamics: M_req = I·k(w_cmd - w) + w × I·w.
    3. Moment -> deflection: subtract the unforced moment, then a
       limit-weighted pseudo-inverse of B. It blends aero surfaces and TVC
       by available authority, so TVC takes over as q -> 0.
    Deflection saturation is where stall and low q actually bite.
    """
    v_b, q, w = x[3:6], x[6:10], x[10:13]
    q = q / np.linalg.norm(q)
    r_wb = C_WN @ quat_to_rotation_matrix(q)
    vp, aero = params.vehicle, params.aero
    rho = isa_density(x[2])
    speed, alpha, beta = wind_angles(v_b)

    if rate_cmd is None:
        rate_cmd = np.zeros(3)
        if speed > _V_MIN_AUTOPILOT:
            v_w = r_wb @ v_b
            a_w = np.asarray(lateral_accel_cmd, dtype=float)
            a_b = r_wb.T @ a_w
            # Path turn rate from command AND gravity. Without g the alpha loop
            # needs a standing error to follow the gravity arc, and that error is lift.
            rate_ff = r_wb.T @ np.cross(v_w, a_w + GRAVITY_VECTOR) / speed ** 2
            accel_per_rad = 0.5 * rho * speed ** 2 * vp.reference_area * aero.cl_alpha / vp.mass
            alpha_lim = vp.max_normal_force_coefficient / aero.cl_alpha
            if params.bank_to_turn:
                a_yz = float(np.hypot(a_b[1], a_b[2]))
                bank_err = float(np.arctan2(a_b[1], -a_b[2])) if a_yz > 1e-3 else 0.0
                # Fade roll authority in for small commands so noise doesn't spin the jet.
                rate_cmd[0] = params.k_bank * bank_err * min(1.0, a_yz / G0)
                alpha_cmd, beta_cmd = -a_b[2] / accel_per_rad, 0.0
            else:
                side_per_rad = 0.5 * rho * speed ** 2 * vp.reference_area * aero.cy_beta / vp.mass
                alpha_cmd, beta_cmd = -a_b[2] / accel_per_rad, a_b[1] / side_per_rad
            alpha_cmd = float(np.clip(alpha_cmd, -alpha_lim, alpha_lim))
            beta_cmd = float(np.clip(beta_cmd, -alpha_lim, alpha_lim))
            rate_cmd[1] = rate_ff[1] + params.k_alpha * (alpha_cmd - alpha)
            rate_cmd[2] = rate_ff[2] - params.k_alpha * (beta_cmd - beta)

    inertia = params.inertia
    moment_req = inertia @ (params.k_rate * (np.asarray(rate_cmd) - w)) + np.cross(w, inertia @ w)
    zero = np.zeros_like(params.actuators.max_deflection, dtype=float)
    moment_free = body_aero_moment(v_b, w, rho, vp.reference_area, aero, zero)
    moment_free = moment_free + thrust_force_moment(thrust, params.tvc_arm_m, zero)[1]

    scale = np.asarray(params.actuators.max_deflection)
    b_mat = control_effectiveness(speed, rho, vp.reference_area, aero, thrust, params.tvc_arm_m)
    deflection = scale * (np.linalg.pinv(b_mat * scale, rcond=1e-9) @ (moment_req - moment_free))
    return params.actuators.clip(deflection)


def specific_force_lateral_world(
    x: np.ndarray,
    params: "RigidBodyParams",
    deflection: np.ndarray,
    thrust: float,
) -> np.ndarray:
    """Achieved aero+thrust specific force perpendicular to velocity, world frame (diagnostics/reward)."""
    v_b, q = x[3:6], x[6:10] / np.linalg.norm(x[6:10])
    speed = float(np.linalg.norm(v_b))
    if speed < 1e-6:
        return np.zeros(3)
    vp = params.vehicle
    rho = isa_density(x[2])
    force = body_aero_force(v_b, rho, vp.reference_area, vp.drag_coefficient, params.aero, deflection[RUDDER])
    force = force + thrust_force_moment(thrust, params.tvc_arm_m, deflection)[0]
    v_hat = v_b / speed
    lateral = (force - np.dot(force, v_hat) * v_hat) / vp.mass
    return C_WN @ (quat_to_rotation_matrix(q) @ lateral)
