"""Optional wider training distribution.  Default training does not use this.

The first retrain after the reward redesign must keep the existing
``training_initial_conditions`` / ``training_maneuver_factory`` distribution.
Enable these samplers only via ``PPOTrainingConfig.domain_randomization``.
The nine-case evaluation set is independent and must stay frozen.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import (
    ConstantTurn,
    ManeuverProfile,
    NoManeuver,
    SinusoidalWeave,
)


def randomized_initial_conditions(
    rng: np.random.Generator,
) -> tuple[State, State]:
    """Wider speed / geometry sampling than the frozen training distribution."""

    target_range_m = float(rng.uniform(4_000.0, 12_000.0))
    lateral_offset_m = float(rng.uniform(-2_000.0, 2_000.0))
    target_altitude_m = float(rng.uniform(2_500.0, 4_500.0))
    pursuer_altitude_m = float(rng.uniform(2_500.0, 3_500.0))
    target_speed_m_s = float(rng.uniform(120.0, 280.0))
    pursuer_speed_m_s = float(rng.uniform(300.0, 420.0))
    heading_error_rad = float(np.deg2rad(rng.uniform(-15.0, 15.0)))
    return (
        State(
            position=[0.0, 0.0, pursuer_altitude_m],
            velocity=[
                pursuer_speed_m_s * np.cos(heading_error_rad),
                pursuer_speed_m_s * np.sin(heading_error_rad),
                0.0,
            ],
        ),
        State(
            position=[target_range_m, lateral_offset_m, target_altitude_m],
            velocity=[-target_speed_m_s, 0.0, 0.0],
        ),
    )


def randomized_maneuver_factory(rng: np.random.Generator) -> ManeuverProfile:
    """Wider maneuver-type mix: still NoManeuver / ConstantTurn / Weave."""

    profile_index = int(rng.integers(0, 3))
    if profile_index == 0:
        return NoManeuver()

    magnitude_m_s2 = float(rng.uniform(1.0, 10.0) * G0)
    if profile_index == 1:
        turn_sign = -1.0 if float(rng.random()) < 0.5 else 1.0
        return ConstantTurn(accel=turn_sign * magnitude_m_s2)

    return SinusoidalWeave(
        amplitude=magnitude_m_s2,
        frequency_hz=float(rng.uniform(0.2, 1.5)),
        phase=float(rng.uniform(0.0, 2.0 * np.pi)),
    )
