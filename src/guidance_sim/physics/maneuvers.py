"""
Target maneuver profiles, generalized to 3D.

In 2D there's exactly one "perpendicular to velocity" direction, so a
maneuver could be a scalar. In 3D there's a whole plane of directions
perpendicular to velocity, so a maneuver needs to say *which* one --
these profiles do that by picking a reference axis (e.g. "up") and
turning/weaving in the plane that axis defines relative to the
vehicle's current velocity. Because of that, `lateral_accel` now
takes the current `State`, not just time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from guidance_sim.physics.entities import State

UP = np.array([0.0, 0.0, 1.0])


def _turn_direction(velocity: np.ndarray, reference_axis: np.ndarray) -> np.ndarray:
    """
    Unit vector perpendicular to velocity, in the plane defined by
    `reference_axis` and velocity -- e.g. reference_axis=UP gives a
    horizontal turn direction; reference_axis pointing sideways gives
    a vertical pull-up/push-over direction.
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-6:
        return np.zeros(3)
    v_hat = velocity / speed
    raw = np.cross(reference_axis, v_hat)
    norm = np.linalg.norm(raw)
    if norm < 1e-9:
        # velocity is parallel to reference_axis; pick an arbitrary
        # perpendicular direction so the maneuver is still defined
        fallback = np.array([1.0, 0.0, 0.0]) if abs(v_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        raw = np.cross(fallback, v_hat)
        norm = np.linalg.norm(raw)
    return raw / norm


class ManeuverProfile(ABC):
    """Base interface: given time t and current state, return a 3D lateral accel command (m/s^2, world frame)."""

    @abstractmethod
    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        raise NotImplementedError


class NoManeuver(ManeuverProfile):
    """Non-maneuvering target: ballistic/straight, no commanded turn."""

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        return np.zeros(3)


class ConstantTurn(ManeuverProfile):
    """
    Holds a constant-magnitude lateral acceleration in the turn
    direction defined by `reference_axis` (default: a horizontal
    turn). Produces a roughly constant-radius turn once the entity's
    speed settles.
    """

    def __init__(self, accel: float, reference_axis: np.ndarray = UP):
        self.accel = accel
        self.reference_axis = np.asarray(reference_axis, dtype=float)

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        direction = _turn_direction(state.velocity, self.reference_axis)
        return self.accel * direction


class SinusoidalWeave(ManeuverProfile):
    """
    Oscillates lateral acceleration sinusoidally in the plane defined
    by `reference_axis` -- a classic "jinking" evasive profile,
    generalized to weave horizontally, vertically, or anywhere in
    between depending on the chosen axis.
    """

    def __init__(self, amplitude: float, frequency_hz: float, phase: float = 0.0,
                 reference_axis: np.ndarray = UP):
        self.amplitude = amplitude
        self.frequency_hz = frequency_hz
        self.phase = phase
        self.reference_axis = np.asarray(reference_axis, dtype=float)

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        direction = _turn_direction(state.velocity, self.reference_axis)
        magnitude = self.amplitude * np.sin(2 * np.pi * self.frequency_hz * t + self.phase)
        return magnitude * direction
