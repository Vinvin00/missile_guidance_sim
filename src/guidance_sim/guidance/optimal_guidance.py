"""
Optimal Guidance Law (OGL) / zero-effort-miss guidance.

Formulation (constant target accel, perfect knowledge upper bound):

    t_go = |r_rel| / Vc ,   Vc = -dot(r_rel, v_rel) / |r_rel|
    ZEM  = r_rel + v_rel * t_go + 0.5 * a_target_est * t_go^2
    a_cmd = N * ZEM / t_go^2

Assumptions / limits:
  - Point-mass, 3D; no seeker lag in the law itself (autopilot lag is
    applied downstream in PointMassEntity.step).
  - Target acceleration treated as constant over t_go.
  - t_go from range/closing-speed (singular when Vc ≤ 0 or near
    intercept — guarded with a floor).
  - Command is not pre-projected onto the LOS-normal plane; the
    entity clamp removes the along-track component.

At N=3 with constant a_target, OGL is classically equivalent to APN.
Reference: Nesline & Zarchan JGCD 4(1) 1981; Zarchan ch. 8.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import State


class OptimalGuidance(GuidanceLaw):
    def __init__(
        self,
        navigation_constant: float = 3.0,
        a_target_est: Optional[Callable[[], np.ndarray]] = None,
        t_go_min: float = 1e-3,
    ):
        if navigation_constant <= 0:
            raise ValueError("navigation_constant (N) must be positive")
        self.N = navigation_constant
        self.a_target_est = a_target_est or (lambda: np.zeros(3))
        self.t_go_min = float(t_go_min)
        # Fallback when not closing: classical PN with same N.
        self._pn_fallback = ProportionalNavigation(navigation_constant=navigation_constant)

    def compute_command(
        self, pursuer_state: State, target_state: State, dt: float
    ) -> np.ndarray:
        r_rel = target_state.position - pursuer_state.position
        v_rel = target_state.velocity - pursuer_state.velocity
        range_ = float(np.linalg.norm(r_rel))
        if range_ < 1e-6:
            return np.zeros(3)

        closing_velocity = -float(np.dot(r_rel, v_rel)) / range_
        if closing_velocity <= 1e-6:
            return self._pn_fallback.compute_command(pursuer_state, target_state, dt)

        t_go = max(range_ / closing_velocity, self.t_go_min)
        a_t = np.asarray(self.a_target_est(), dtype=float).reshape(3)
        zem = r_rel + v_rel * t_go + 0.5 * a_t * (t_go ** 2)
        return self.N * zem / (t_go ** 2)

    def reset(self) -> None:
        self._pn_fallback.reset()
