"""Estimator interface (AGENTS Step 5b)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

from guidance_sim.physics.entities import State
from guidance_sim.sensors.measurement import Measurement


class Estimator(ABC):
    """Consume seeker measurements; produce a filtered target state + accel estimate."""

    @abstractmethod
    def update(
        self,
        measurement: Optional[Measurement],
        pursuer_state: State,
        dt: float,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def estimate(self) -> Tuple[State, np.ndarray]:
        """Return ``(target_state, accel_est)`` in the world frame."""
        raise NotImplementedError

    @abstractmethod
    def covariance(self) -> np.ndarray:
        raise NotImplementedError

    def reset(self) -> None:
        """Optional: clear filter state between Monte Carlo trials."""
        pass
