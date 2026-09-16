"""
Body-axis moments: aerodynamic (static stability, rate damping, control
surfaces) plus thrust, including thrust vectoring.

Moments are rolling L, pitching M, yawing N about body FRD x, y, z,
positive by the right-hand rule (right wing down, nose up, nose right).

Rate damping is written in dimensional form:
    qbar*S*b * C_lp * p*b/(2V)  ==  1/4 * rho * V * S * b^2 * C_lp * p
It is identical to the textbook form but stays finite as V -> 0 (the
Cobra hang), where the non-dimensional rate would divide by zero.
Without these terms the rigid body is under-damped and rings
(tests/test_rigid_body.py checks that they actually damp).
"""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.aerodynamics import AeroDerivatives, wind_angles
from guidance_sim.physics.controls import AILERON, ELEVATOR, N_CONTROLS, RUDDER, TV_PITCH, TV_YAW


def body_aero_moment(
    v_body: np.ndarray,
    omega_body: np.ndarray,
    rho: float,
    reference_area: float,
    aero: AeroDerivatives,
    deflection: np.ndarray,
) -> np.ndarray:
    """Aerodynamic moment (N·m) in body axes."""
    speed, alpha, beta = wind_angles(v_body)
    p, q, r = omega_body
    b, c, s = aero.span, aero.chord, reference_area
    qbar_s = 0.5 * rho * speed ** 2 * s
    damp = 0.25 * rho * speed * s
    de, da, dr = deflection[ELEVATOR], deflection[AILERON], deflection[RUDDER]

    roll = qbar_s * b * (aero.c_roll_beta * beta + aero.c_roll_da * da + aero.c_roll_dr * dr) \
        + damp * b * b * aero.c_roll_p * p
    pitch = qbar_s * c * (aero.c_pitch_alpha * np.sin(alpha) + aero.c_pitch_de * de) \
        + damp * c * c * aero.c_pitch_q * q
    yaw = qbar_s * b * (aero.c_yaw_beta * beta + aero.c_yaw_dr * dr) \
        + damp * b * b * aero.c_yaw_r * r
    return np.array([roll, pitch, yaw])


def thrust_force_moment(
    thrust: float,
    tvc_arm_m: float,
    deflection: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Thrust applied at the nozzle, `tvc_arm_m` aft of the CG on the body
    x-axis. Positive tv_pitch tilts the jet so its force pushes the tail
    down, giving nose-up moment. Positive tv_yaw pushes the tail left,
    giving nose-right moment. With zero deflection the line of thrust
    passes through the CG, so there is no moment.
    """
    dp, dy = deflection[TV_PITCH], deflection[TV_YAW]
    force = thrust * np.array([np.cos(dp) * np.cos(dy), -np.sin(dy), np.sin(dp)])
    moment = np.cross([-tvc_arm_m, 0.0, 0.0], force)
    return force, moment


def control_effectiveness(
    speed: float,
    rho: float,
    reference_area: float,
    aero: AeroDerivatives,
    thrust: float,
    tvc_arm_m: float,
) -> np.ndarray:
    """
    B (3 x N_CONTROLS): d(moment)/d(deflection) at zero deflection, so that
    M ≈ M(δ=0) + B·δ. The autopilot inverts this. Note the aero columns
    scale with V^2 and vanish in the hang, while the TVC columns don't.
    """
    qbar_s = 0.5 * rho * speed ** 2 * reference_area
    b, c = aero.span, aero.chord
    B = np.zeros((3, N_CONTROLS))
    B[1, ELEVATOR] = qbar_s * c * aero.c_pitch_de
    B[0, AILERON] = qbar_s * b * aero.c_roll_da
    B[0, RUDDER] = qbar_s * b * aero.c_roll_dr
    B[2, RUDDER] = qbar_s * b * aero.c_yaw_dr
    B[1, TV_PITCH] = thrust * tvc_arm_m
    B[2, TV_YAW] = thrust * tvc_arm_m
    return B
