"""Post-stall departure susceptibility: yaw stability and roll damping
degrade past alpha_stall, so a sideslip/roll disturbance during a deep-stall
maneuver (e.g. the Cobra hang) is no longer guaranteed to self-correct.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.aero_moments import body_aero_moment
from guidance_sim.physics.entities import F16_6DOF

_AERO = F16_6DOF.aero
_S = F16_6DOF.vehicle.reference_area
_RHO = 1.0


def _yaw_moment(alpha_deg: float, beta_deg: float, speed: float = 150.0) -> float:
    alpha, beta = np.deg2rad(alpha_deg), np.deg2rad(beta_deg)
    v_body = speed * np.array([np.cos(alpha) * np.cos(beta), np.sin(beta), np.sin(alpha) * np.cos(beta)])
    moment = body_aero_moment(v_body, np.zeros(3), _RHO, _S, _AERO, np.zeros(5))
    return float(moment[2])


def test_yaw_stability_restores_below_stall_but_collapses_deep_post_stall():
    # Below stall: positive sideslip should generate a restoring (same-sign,
    # nose-right-for-nose-left-slip) yaw moment -- textbook weathercock
    # stability (F16_6DOF.c_yaw_beta > 0 in this file's sign convention).
    assert _yaw_moment(alpha_deg=5.0, beta_deg=5.0) > 0.0
    # Deep post-stall (Cobra hang territory): the same sideslip should no
    # longer be restoring -- this is the departure mechanism.
    assert _yaw_moment(alpha_deg=85.0, beta_deg=5.0) < 0.0


def test_roll_damping_weakens_deep_post_stall():
    p = 0.5  # rad/s roll rate
    roll_below = body_aero_moment(
        150.0 * np.array([1.0, 0.0, 0.0]), [p, 0.0, 0.0], _RHO, _S, _AERO, np.zeros(5)
    )[0]
    alpha = np.deg2rad(85.0)
    v_body = 150.0 * np.array([np.cos(alpha), 0.0, np.sin(alpha)])
    roll_deep = body_aero_moment(v_body, [p, 0.0, 0.0], _RHO, _S, _AERO, np.zeros(5))[0]
    # Both oppose the roll rate (damping, not autorotation), but the deep
    # post-stall restoring moment is markedly weaker.
    assert roll_below < 0.0 and roll_deep < 0.0
    assert abs(roll_deep) < 0.5 * abs(roll_below)
