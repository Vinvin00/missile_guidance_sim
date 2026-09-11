"""
Seeker/sensor measurement model.

Guidance laws must not read perfect target state. This module converts
true relative geometry into noisy azimuth / elevation / range (and
optional rate) measurements, with configurable update rate, detection
probability, and delivery latency.

Noise defaults are illustrative order-of-magnitude values typical of
abstract angle-tracking seekers in the open literature (~1 mrad angle
noise; see REFERENCES.md when Priority 4 lands). They are not tied to
any real weapon seeker.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional, Tuple

import numpy as np

from guidance_sim.physics.entities import State


@dataclass
class SeekerNoiseConfig:
    """Per-channel Gaussian noise standard deviations (zero = perfect)."""

    azimuth_std: float = 1e-3  # rad (~1 mrad)
    elevation_std: float = 1e-3  # rad
    azimuth_rate_std: float = 1e-3  # rad/s
    elevation_rate_std: float = 1e-3  # rad/s
    range_std: float = 5.0  # m
    range_rate_std: float = 1.0  # m/s

    def scaled(self, scale: float) -> "SeekerNoiseConfig":
        """Return a copy with every std multiplied by ``scale`` (0 = noiseless)."""
        if scale < 0.0:
            raise ValueError("noise scale must be non-negative")
        return SeekerNoiseConfig(
            azimuth_std=self.azimuth_std * scale,
            elevation_std=self.elevation_std * scale,
            azimuth_rate_std=self.azimuth_rate_std * scale,
            elevation_rate_std=self.elevation_rate_std * scale,
            range_std=self.range_std * scale,
            range_rate_std=self.range_rate_std * scale,
        )


@dataclass
class SensorConfig:
    """Sensor scheduling + noise. AGENTS Step 5a interface."""

    angle_noise_std: float = 1e-3  # rad; used when ``noise`` is None
    range_available: bool = True
    update_rate_hz: float = 100.0
    detection_probability: float = 1.0
    latency_s: float = 0.0
    noise: Optional[SeekerNoiseConfig] = None

    def __post_init__(self) -> None:
        if self.update_rate_hz <= 0.0:
            raise ValueError("update_rate_hz must be positive")
        if not (0.0 <= self.detection_probability <= 1.0):
            raise ValueError("detection_probability must be in [0, 1]")
        if self.latency_s < 0.0:
            raise ValueError("latency_s must be non-negative")
        if self.noise is None:
            self.noise = SeekerNoiseConfig(
                azimuth_std=self.angle_noise_std,
                elevation_std=self.angle_noise_std,
            )


@dataclass
class Measurement:
    t: float
    azimuth: float  # rad, atan2(y, x) in world frame
    elevation: float  # rad, asin(z / range)
    range_: Optional[float]
    valid: bool
    azimuth_rate: Optional[float] = None  # rad/s
    elevation_rate: Optional[float] = None  # rad/s
    range_rate: Optional[float] = None  # m/s


def los_angles(relative_position: np.ndarray) -> Tuple[float, float, float]:
    """Return (azimuth, elevation, range) from relative position target-pursuer."""
    r = np.asarray(relative_position, dtype=float).reshape(3)
    range_ = float(np.linalg.norm(r))
    if range_ < 1e-12:
        return 0.0, 0.0, 0.0
    azimuth = float(np.arctan2(r[1], r[0]))
    elevation = float(np.arcsin(np.clip(r[2] / range_, -1.0, 1.0)))
    return azimuth, elevation, range_


def los_rates(
    relative_position: np.ndarray, relative_velocity: np.ndarray
) -> Tuple[float, float, float]:
    """
    Analytic LOS azimuth/elevation rates and range-rate from relative kinematics.

    Uses the standard spherical-coordinate rate formulas (z-up world frame).
    """
    r = np.asarray(relative_position, dtype=float).reshape(3)
    v = np.asarray(relative_velocity, dtype=float).reshape(3)
    range_ = float(np.linalg.norm(r))
    if range_ < 1e-9:
        return 0.0, 0.0, 0.0

    range_rate = float(np.dot(r, v) / range_)
    # Horizontal range in xy-plane
    rho = float(np.hypot(r[0], r[1]))
    if rho < 1e-9:
        az_rate = 0.0
    else:
        az_rate = float((r[0] * v[1] - r[1] * v[0]) / (rho * rho))

    # elevation = asin(z/R) => el_dot from d/dt (z/R)
    z_over_r = r[2] / range_
    d_z_over_r = (v[2] * range_ - r[2] * range_rate) / (range_ * range_)
    denom = max(1e-12, float(np.sqrt(max(0.0, 1.0 - z_over_r * z_over_r))))
    el_rate = d_z_over_r / denom
    return az_rate, el_rate, range_rate


def spherical_to_relative(
    azimuth: float, elevation: float, range_: float
) -> np.ndarray:
    """Convert az/el/range back to a relative position vector (world frame)."""
    ce = np.cos(elevation)
    return np.array(
        [
            range_ * ce * np.cos(azimuth),
            range_ * ce * np.sin(azimuth),
            range_ * np.sin(elevation),
        ],
        dtype=float,
    )


class Sensor:
    """
    Samples true geometry into a (possibly delayed, intermittent, noisy)
    ``Measurement``. Returns ``None`` between updates or on missed detection.
    """

    def __init__(self, config: Optional[SensorConfig] = None):
        self.config = config if config is not None else SensorConfig()
        self._last_sample_t: Optional[float] = None
        self._pending: Deque[Tuple[float, Measurement]] = deque()

    def reset(self) -> None:
        self._last_sample_t = None
        self._pending.clear()

    def _due_for_sample(self, t: float) -> bool:
        if self._last_sample_t is None:
            return True
        period = 1.0 / self.config.update_rate_hz
        return (t - self._last_sample_t) >= period - 1e-12

    def _truth_measurement(
        self,
        t: float,
        pursuer: State,
        target: State,
        rng: np.random.Generator,
    ) -> Measurement:
        r_rel = target.position - pursuer.position
        v_rel = target.velocity - pursuer.velocity
        az, el, range_ = los_angles(r_rel)
        az_rate, el_rate, range_rate = los_rates(r_rel, v_rel)

        noise = self.config.noise
        assert noise is not None

        def n(std: float) -> float:
            return 0.0 if std <= 0.0 else float(rng.normal(0.0, std))

        az_m = az + n(noise.azimuth_std)
        el_m = el + n(noise.elevation_std)
        az_rate_m = az_rate + n(noise.azimuth_rate_std)
        el_rate_m = el_rate + n(noise.elevation_rate_std)

        range_m: Optional[float]
        range_rate_m: Optional[float]
        if self.config.range_available:
            range_m = max(0.0, range_ + n(noise.range_std))
            range_rate_m = range_rate + n(noise.range_rate_std)
        else:
            range_m = None
            range_rate_m = None

        return Measurement(
            t=t,
            azimuth=az_m,
            elevation=el_m,
            range_=range_m,
            valid=True,
            azimuth_rate=az_rate_m,
            elevation_rate=el_rate_m,
            range_rate=range_rate_m,
        )

    def measure(
        self,
        t: float,
        pursuer_state: State,
        target_state: State,
        rng: np.random.Generator,
    ) -> Optional[Measurement]:
        cfg = self.config

        # Sample new truth+noise at the seeker update rate.
        if self._due_for_sample(t):
            self._last_sample_t = t
            detected = float(rng.random()) <= cfg.detection_probability
            if detected:
                meas = self._truth_measurement(t, pursuer_state, target_state, rng)
                deliver_at = t + cfg.latency_s
                self._pending.append((deliver_at, meas))
            # else: missed detection — nothing enqueued

        # Deliver the oldest pending measurement whose latency has elapsed.
        ready: Optional[Measurement] = None
        while self._pending and self._pending[0][0] <= t + 1e-12:
            _, ready = self._pending.popleft()
            # Keep draining only one per call so downstream sees update cadence.
            break
        return ready
