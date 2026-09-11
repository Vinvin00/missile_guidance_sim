"""
Compatibility alias for the Priority-1 seeker layer.

Canonical implementation lives in ``guidance_sim.sensors.measurement``
(AGENTS Step 5a). This module re-exports the same types under the name
used in the credibility-improvements brief.
"""

from guidance_sim.sensors.measurement import (
    Measurement,
    SeekerNoiseConfig,
    Sensor,
    SensorConfig,
    los_angles,
    los_rates,
    spherical_to_relative,
)

__all__ = [
    "Measurement",
    "SeekerNoiseConfig",
    "Sensor",
    "SensorConfig",
    "los_angles",
    "los_rates",
    "spherical_to_relative",
]
