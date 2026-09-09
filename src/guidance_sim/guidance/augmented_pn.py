"""
Augmented Proportional Navigation (APN).

    a_cmd = PN(N) + (N/2) * a_target_est

where PN is the classical 3D vector law. Target acceleration is injected
via a callable so later steps can swap perfect knowledge for an
estimator without changing this class.

Reference: Nesline & Zarchan, JGCD 4(1) 1981; Zarchan ch. 8–9.
"""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import State


class AugmentedProportionalNavigation(GuidanceLaw):
    def __init__(
        self,
        navigation_constant: float = 4.0,
        a_target_est: Optional[Callable[[], np.ndarray]] = None,
    ):
        self._pn = ProportionalNavigation(navigation_constant=navigation_constant)
        self.N = navigation_constant
        self.a_target_est = a_target_est or (lambda: np.zeros(3))

    def compute_command(
        self, pursuer_state: State, target_state: State, dt: float
    ) -> np.ndarray:
        pn_term = self._pn.compute_command(pursuer_state, target_state, dt)
        a_t = np.asarray(self.a_target_est(), dtype=float).reshape(3)
        return pn_term + 0.5 * self.N * a_t

    def reset(self) -> None:
        self._pn.reset()
