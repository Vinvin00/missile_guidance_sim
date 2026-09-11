"""Unit tests for seeker measurement geometry and noise injection."""

import numpy as np
import pytest

from guidance_sim.physics.entities import State
from guidance_sim.sensors.measurement import (
    SeekerNoiseConfig,
    Sensor,
    SensorConfig,
    los_angles,
    los_rates,
    spherical_to_relative,
)


def test_los_angles_round_trip():
    r = np.array([3000.0, 400.0, 200.0])
    az, el, rng = los_angles(r)
    recovered = spherical_to_relative(az, el, rng)
    np.testing.assert_allclose(recovered, r, rtol=1e-10, atol=1e-10)


def test_los_rates_closing_head_on():
    # Target directly ahead, closing: range-rate negative, angle rates ~0.
    r = np.array([1000.0, 0.0, 0.0])
    v = np.array([-200.0, 0.0, 0.0])
    az_rate, el_rate, range_rate = los_rates(r, v)
    assert range_rate == pytest.approx(-200.0)
    assert az_rate == pytest.approx(0.0, abs=1e-12)
    assert el_rate == pytest.approx(0.0, abs=1e-12)


def test_sensor_zero_noise_matches_truth():
    pursuer = State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0])
    target = State(position=[6000.0, 800.0, 3400.0], velocity=[-200.0, 0.0, 0.0])
    sensor = Sensor(
        SensorConfig(
            noise=SeekerNoiseConfig(
                azimuth_std=0.0,
                elevation_std=0.0,
                azimuth_rate_std=0.0,
                elevation_rate_std=0.0,
                range_std=0.0,
                range_rate_std=0.0,
            ),
            update_rate_hz=100.0,
            latency_s=0.0,
        )
    )
    rng = np.random.default_rng(0)
    meas = sensor.measure(0.0, pursuer, target, rng)
    assert meas is not None and meas.valid
    az, el, range_ = los_angles(target.position - pursuer.position)
    assert meas.azimuth == pytest.approx(az)
    assert meas.elevation == pytest.approx(el)
    assert meas.range_ == pytest.approx(range_)


def test_sensor_noise_increases_with_scale():
    pursuer = State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0])
    target = State(position=[6000.0, 800.0, 3400.0], velocity=[-200.0, 50.0, 10.0])
    base = SeekerNoiseConfig()
    az, el, _ = los_angles(target.position - pursuer.position)

    def rms_angle_error(scale: float, n: int = 200) -> float:
        sensor = Sensor(SensorConfig(noise=base.scaled(scale), update_rate_hz=1e6))
        errs = []
        rng = np.random.default_rng(1)
        for i in range(n):
            sensor.reset()
            m = sensor.measure(float(i), pursuer, target, rng)
            assert m is not None
            errs.append((m.azimuth - az) ** 2 + (m.elevation - el) ** 2)
        return float(np.sqrt(np.mean(errs)))

    assert rms_angle_error(0.0) == pytest.approx(0.0, abs=1e-15)
    assert rms_angle_error(1.0) < rms_angle_error(3.0)


def test_sensor_respects_update_rate():
    pursuer = State(position=[0.0, 0.0, 1000.0], velocity=[1.0, 0.0, 0.0])
    target = State(position=[100.0, 0.0, 1000.0], velocity=[0.0, 0.0, 0.0])
    sensor = Sensor(SensorConfig(update_rate_hz=10.0, latency_s=0.0))
    rng = np.random.default_rng(0)
    assert sensor.measure(0.00, pursuer, target, rng) is not None
    assert sensor.measure(0.05, pursuer, target, rng) is None  # between updates
    assert sensor.measure(0.10, pursuer, target, rng) is not None


def test_sensor_latency_delays_delivery():
    pursuer = State(position=[0.0, 0.0, 1000.0], velocity=[1.0, 0.0, 0.0])
    target = State(position=[100.0, 0.0, 1000.0], velocity=[0.0, 0.0, 0.0])
    sensor = Sensor(SensorConfig(update_rate_hz=100.0, latency_s=0.05))
    rng = np.random.default_rng(0)
    assert sensor.measure(0.00, pursuer, target, rng) is None  # sampled, not yet due
    assert sensor.measure(0.04, pursuer, target, rng) is None
    delayed = sensor.measure(0.05, pursuer, target, rng)
    assert delayed is not None
    assert delayed.t == pytest.approx(0.0)
