"""
Abstract guidance-law interface.

Both the classical Proportional Navigation law and the future
learned (LSTM-augmented or RL) approach implement this interface,
so the simulation engine can swap between them without caring
which one it's driving.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from guidance_sim.physics.entities import State


class GuidanceLaw(ABC):
    """Given pursuer and target state, compute a 3D lateral accel command."""

    @abstractmethod
    def compute_command(self, pursuer_state: State, target_state: State, dt: float) -> np.ndarray:
        """
        Returns the commanded acceleration vector (m/s^2, world frame,
        shape (3,)) for the pursuer at this instant. PointMassEntity.step
        projects this onto the plane perpendicular to velocity and
        clamps it to what the airframe can actually achieve -- the
        guidance law itself doesn't need to worry about achievability.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Optional hook for stateful guidance laws (e.g. filters)."""
        pass
