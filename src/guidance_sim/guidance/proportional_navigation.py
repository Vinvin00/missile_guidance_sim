"""
Proportional Navigation (PN) guidance law, in full 3D vector form.

Classical PN command:

    a_cmd = N * Vc * lambda_dot

The 2D version treats lambda_dot as a scalar (LOS rotating one way or
the other in a single plane). In 3D the line of sight can rotate
about any axis, so lambda_dot becomes the LOS angular-rate *vector*:

    omega_LOS = (R x Vr) / |R|^2

where R is the relative position (target - pursuer) and Vr is the
relative velocity. The full 3D vector command is then:

    a_cmd = N * Vc * (omega_LOS x R_hat)

which points perpendicular to the line of sight, in the plane that
nulls out the LOS rotation -- the direct 3D generalization of the
classical formula (magnitude reduces to N * Vc * lambda_dot; the
cross product supplies the correct direction in 3D instead of an
implicit single perpendicular).

Reference: Zarchan, "Tactical and Strategic Missile Guidance", ch. 2;
the vector form is standard in any GNC text covering 3D engagements
(e.g. Shneydor, "Missile Guidance and Pursuit"). Nothing here is
specific to a real weapon system.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.physics.entities import State


class ProportionalNavigation(GuidanceLaw):
    def __init__(self, navigation_constant: float = 4.0):
        if navigation_constant <= 0:
            raise ValueError("navigation_constant (N) must be positive")
        self.N = navigation_constant

    def compute_command(self, pursuer_state: State, target_state: State, dt: float) -> np.ndarray:
        relative_position = target_state.position - pursuer_state.position
        relative_velocity = target_state.velocity - pursuer_state.velocity

        range_ = float(np.linalg.norm(relative_position))
        if range_ < 1e-6:
            return np.zeros(3)

        range_unit = relative_position / range_

        # LOS angular rate vector: omega = (R x Vr) / |R|^2
        omega_los = np.cross(relative_position, relative_velocity) / (range_ ** 2)

        # Closing velocity: positive when range is shrinking.
        closing_velocity = -float(np.dot(relative_position, relative_velocity)) / range_

        # a_cmd perpendicular to the LOS, magnitude N * Vc * |omega_los|.
        a_cmd = self.N * closing_velocity * np.cross(omega_los, range_unit)
        return a_cmd
