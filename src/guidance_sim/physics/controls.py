"""
Control effectors: deflection vector layout, and the actuator model that
turns an autopilot deflection *command* into the deflection the airframe
actually sees.

Deflection vector (rad), fixed order everywhere:
    [elevator, aileron, rudder, tv_pitch, tv_yaw]
A channel whose `max_deflection` is 0 is not fitted on that vehicle (e.g.
a missile has no thrust vectoring, and a stock F-16 has none either).

Actuator = first-order lag, then rate limit, then position limit. That is
the same clamp-after-dynamics philosophy as `clamp_lateral_command`. The
lag and limit numbers per vehicle live with the vehicle in `entities.py`,
with their sources.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ELEVATOR, AILERON, RUDDER, TV_PITCH, TV_YAW = range(5)
N_CONTROLS = 5


@dataclass(frozen=True)
class ActuatorLimits:
    max_deflection: tuple[float, float, float, float, float]  # rad
    max_rate: tuple[float, float, float, float, float]  # rad/s
    time_constant: tuple[float, float, float, float, float]  # s

    def clip(self, deflection: np.ndarray) -> np.ndarray:
        limit = np.asarray(self.max_deflection)
        return np.clip(deflection, -limit, limit)


def actuator_step(
    current: np.ndarray,
    command: np.ndarray,
    dt: float,
    limits: ActuatorLimits,
) -> np.ndarray:
    """One control tick: exact-ZOH first-order lag, rate-limited, position-clamped."""
    tau = np.asarray(limits.time_constant)
    gain = np.where(tau > 0.0, 1.0 - np.exp(-dt / np.maximum(tau, 1e-12)), 1.0)
    max_step = np.asarray(limits.max_rate) * dt
    step = np.clip(gain * (limits.clip(command) - current), -max_step, max_step)
    return limits.clip(current + step)
