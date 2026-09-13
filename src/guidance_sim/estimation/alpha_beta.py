"""
Fixed-gain alpha-beta tracker on Cartesian target position.

Gains satisfy the Benedict–Bordner relation

    beta = alpha**2 / (2 - alpha)

so a single ``alpha`` parameter sets the filter. Measurements are
converted from noisy seeker az/el/range into an absolute target
position; the filter never feeds raw LOS rates into the guidance law.

When range is unavailable the filter holds the last range estimate
(bearings-only cold-start is deferred to the EKF polar estimator).
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from guidance_sim.estimation.base import Estimator
from guidance_sim.physics.entities import State
from guidance_sim.sensors.measurement import Measurement, spherical_to_relative


class AlphaBetaFilter(Estimator):
    def __init__(
        self,
        alpha: float = 0.5,
        initial_target: Optional[State] = None,
        *,
        use_measured_rates: bool = True,
        velocity_gain: float = 0.3,
    ):
        if not (0.0 < alpha < 1.0):
            raise ValueError("alpha must be in (0, 1)")
        if not (0.0 < velocity_gain <= 1.0):
            raise ValueError("velocity_gain must be in (0, 1]")
        self.alpha = float(alpha)
        self.beta = (alpha * alpha) / (2.0 - alpha)
        # When the seeker reports az/el/range rates, deriving velocity from
        # them beats differencing noisy positions: the beta/dt term amplifies
        # position residual by beta/dt (order 4 at these rates), turning ~18 m
        # of position noise into ~75 m/s of velocity error, whereas 1 mrad/s
        # of angle-rate noise at 7 km is only ~7 m/s of tangential error.
        self.use_measured_rates = bool(use_measured_rates)
        self.velocity_gain = float(velocity_gain)
        self._pos: Optional[np.ndarray] = None
        self._vel: Optional[np.ndarray] = None
        self._accel = np.zeros(3)
        self._initialized = False
        self._last_range: Optional[float] = None
        # Diagonal covariance proxy (not a true KF P); used for interface.
        self._cov = np.eye(6)
        if initial_target is not None:
            self._pos = np.asarray(initial_target.position, dtype=float).reshape(3).copy()
            self._vel = np.asarray(initial_target.velocity, dtype=float).reshape(3).copy()
            self._initialized = True
            self._last_range = float(np.linalg.norm(self._pos))

    def reset(self) -> None:
        self._pos = None
        self._vel = None
        self._accel = np.zeros(3)
        self._initialized = False
        self._last_range = None
        self._cov = np.eye(6)

    def update(
        self,
        measurement: Optional[Measurement],
        pursuer_state: State,
        dt: float,
    ) -> None:
        if dt < 0.0:
            raise ValueError("dt must be non-negative")

        # Time update (constant-velocity prediction) even without a measurement.
        if self._initialized and dt > 0.0:
            assert self._pos is not None and self._vel is not None
            self._pos = self._pos + self._vel * dt

        if measurement is None or not measurement.valid:
            return

        range_ = measurement.range_
        if range_ is None:
            if self._last_range is None:
                # Cannot form a Cartesian fix without range on the first hit.
                return
            range_ = self._last_range
        else:
            self._last_range = float(range_)

        measured_rel = spherical_to_relative(
            measurement.azimuth, measurement.elevation, float(range_)
        )
        measured_pos = pursuer_state.position + measured_rel

        if not self._initialized:
            self._pos = measured_pos.copy()
            # Prefer rate-derived velocity when seeker supplies rates + range-rate.
            if (
                measurement.azimuth_rate is not None
                and measurement.elevation_rate is not None
                and measurement.range_rate is not None
            ):
                self._vel = _spherical_rates_to_velocity(
                    measurement.azimuth,
                    measurement.elevation,
                    float(range_),
                    measurement.azimuth_rate,
                    measurement.elevation_rate,
                    measurement.range_rate,
                ) + pursuer_state.velocity
            else:
                self._vel = pursuer_state.velocity.copy()
            self._initialized = True
            return

        assert self._pos is not None and self._vel is not None
        residual = measured_pos - self._pos
        self._pos = self._pos + self.alpha * residual

        measured_velocity = self._velocity_from_rates(measurement, pursuer_state, range_)
        if measured_velocity is not None:
            self._vel = self._vel + self.velocity_gain * (measured_velocity - self._vel)
        elif dt > 1e-12:
            self._vel = self._vel + (self.beta / dt) * residual

        # Inflate a simple diagonal proxy when residual is large.
        r_norm = float(np.linalg.norm(residual))
        self._cov = np.diag(
            np.concatenate(
                [
                    np.full(3, max(1.0, r_norm)),
                    np.full(3, max(1.0, r_norm / max(dt, 1e-3))),
                ]
            )
        )

    def _velocity_from_rates(
        self,
        measurement: Measurement,
        pursuer_state: State,
        range_: float,
    ) -> Optional[np.ndarray]:
        """Absolute target velocity from the seeker's own rate channels."""

        if not self.use_measured_rates:
            return None
        if (
            measurement.azimuth_rate is None
            or measurement.elevation_rate is None
            or measurement.range_rate is None
        ):
            return None
        relative_velocity = _spherical_rates_to_velocity(
            measurement.azimuth,
            measurement.elevation,
            float(range_),
            measurement.azimuth_rate,
            measurement.elevation_rate,
            measurement.range_rate,
        )
        return relative_velocity + pursuer_state.velocity

    def estimate(self) -> Tuple[State, np.ndarray]:
        if not self._initialized or self._pos is None or self._vel is None:
            raise RuntimeError("AlphaBetaFilter has no estimate yet; wait for a measurement")
        return State(position=self._pos.copy(), velocity=self._vel.copy()), self._accel.copy()

    def covariance(self) -> np.ndarray:
        return self._cov.copy()


def _spherical_rates_to_velocity(
    az: float,
    el: float,
    range_: float,
    az_rate: float,
    el_rate: float,
    range_rate: float,
) -> np.ndarray:
    """Relative velocity from spherical coordinates and their rates."""
    ce, se = np.cos(el), np.sin(el)
    ca, sa = np.cos(az), np.sin(az)
    # r = R * [ce*ca, ce*sa, se]
    # Differentiate.
    dr_dR = np.array([ce * ca, ce * sa, se])
    dr_del = range_ * np.array([-se * ca, -se * sa, ce])
    dr_daz = range_ * np.array([-ce * sa, ce * ca, 0.0])
    return range_rate * dr_dR + el_rate * dr_del + az_rate * dr_daz
