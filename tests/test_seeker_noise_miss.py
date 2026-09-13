"""Alpha-beta filter + closed-loop miss vs seeker noise level."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from guidance_sim.estimation.alpha_beta import AlphaBetaFilter
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.sensors.measurement import SeekerNoiseConfig, Sensor, SensorConfig
from guidance_sim.simulation.engine import Simulation, SimulationConfig

PURSUER_VEHICLE = VehicleParams(
    mass=50.0,
    reference_area=0.05,
    drag_coefficient=0.3,
    max_normal_force_coefficient=15.0,
    max_load_factor=25.0,
)
TARGET_VEHICLE = VehicleParams(
    mass=40.0,
    reference_area=0.06,
    drag_coefficient=0.35,
    max_normal_force_coefficient=10.0,
    max_load_factor=9.0,
)

# Noise scales for the near-monotonicity sweep. Base SeekerNoiseConfig is
# ~1 mrad / 5 m range; scale multiplies every channel. Spaced so high noise
# clearly breaks the engagement while low noise stays near the filter floor.
NOISE_SCALES = (0.0, 2.0, 5.0, 12.0)
FILTER_ALPHA = 0.75


def _entities():
    # Harder geometry than the baseline PN unit test so seeker noise has
    # room to move miss distance (larger offset + crossing component).
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(
            position=np.array([0.0, 0.0, 3000.0]),
            velocity=np.array([350.0, 0.0, 0.0]),
        ),
        vehicle=PURSUER_VEHICLE,
    )
    target = PointMassEntity(
        name="target",
        state=State(
            position=np.array([5500.0, 1500.0, 3200.0]),
            velocity=np.array([-180.0, 40.0, 0.0]),
        ),
        vehicle=TARGET_VEHICLE,
    )
    return pursuer, target


def test_alpha_beta_beta_relation():
    filt = AlphaBetaFilter(alpha=0.5)
    assert filt.beta == pytest.approx((0.5**2) / (2.0 - 0.5))


def test_alpha_beta_tracks_constant_velocity_target():
    pursuer = State(position=[0.0, 0.0, 0.0], velocity=[0.0, 0.0, 0.0])
    true_pos = np.array([1000.0, 0.0, 0.0])
    true_vel = np.array([10.0, 0.0, 0.0])
    filt = AlphaBetaFilter(alpha=0.4)
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
        )
    )
    rng = np.random.default_rng(0)
    dt = 0.01
    for k in range(200):
        t = k * dt
        target = State(position=true_pos + true_vel * t, velocity=true_vel)
        meas = sensor.measure(t, pursuer, target, rng)
        filt.update(meas, pursuer, dt)

    est, _ = filt.estimate()
    final_truth = true_pos + true_vel * (199 * dt)
    np.testing.assert_allclose(est.position, final_truth, atol=1.0)
    np.testing.assert_allclose(est.velocity, true_vel, atol=1.0)


def _run_noisy_engagement(noise_scale: float, seed: int) -> float:
    pursuer, target = _entities()
    noise = SeekerNoiseConfig().scaled(noise_scale)
    sensor = Sensor(
        SensorConfig(
            noise=noise,
            update_rate_hz=100.0,
            latency_s=0.0,
            detection_probability=1.0,
        )
    )
    estimator = AlphaBetaFilter(alpha=FILTER_ALPHA, initial_target=target.state.copy())
    sim = Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=ProportionalNavigation(navigation_constant=3.0),
        target_maneuver=NoManeuver(),
        config=SimulationConfig(
            dt=0.01, max_time=45.0, intercept_radius=5.0, autopilot_tau=0.2
        ),
        sensor=sensor,
        estimator=estimator,
        rng=np.random.default_rng(seed),
    )
    return float(sim.run().miss_distance)


def _spearman_rho(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation without a scipy dependency."""
    n = len(xs)
    rx = np.argsort(np.argsort(np.asarray(xs, dtype=float))).astype(float)
    ry = np.argsort(np.argsort(np.asarray(ys, dtype=float))).astype(float)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = float(np.sqrt(np.sum(rx * rx) * np.sum(ry * ry)))
    if denom < 1e-15:
        return 0.0
    return float(np.sum(rx * ry) / denom)


def test_estimator_velocity_degrades_with_seeker_noise():
    """
    Replaces the original Priority-1 gate, which asserted that *miss distance*
    degrades by >50 m with seeker noise.

    That result did not survive a properly-tuned estimator. It was largely an
    artifact of deriving target velocity by differencing noisy positions with
    a beta/dt gain: at these rates that turned seeker noise into 69-416 m/s of
    velocity error across the sweep's scales, which is what actually wrecked
    the intercepts. Taking velocity from the seeker's own az/el/range rate
    channels instead cuts that ~10x, and PN's miss then stays ~3-5 m across
    the whole sweep (see NOTES 2026-09-13).

    What remains true, and is the honest invariant to gate on, is that the
    *estimate* still degrades monotonically with noise. Miss robustness is
    now a property of the guidance loop, not evidence that noise is harmless.
    """

    truth_velocity = np.array([-200.0, 0.0, 0.0])
    pursuer = State(position=[0.0, 0.0, 3_000.0], velocity=[350.0, 0.0, 0.0])
    target_position = np.array([7_000.0, 300.0, 3_300.0])
    dt = 0.01

    errors = []
    for scale in NOISE_SCALES:
        rng = np.random.default_rng(3)
        sensor = Sensor(
            SensorConfig(update_rate_hz=100.0, noise=SeekerNoiseConfig().scaled(scale))
        )
        filt = AlphaBetaFilter(alpha=0.2)
        samples = []
        for step in range(400):
            t = step * dt
            target = State(
                position=target_position + truth_velocity * t,
                velocity=truth_velocity,
            )
            filt.update(sensor.measure(t, pursuer, target, rng), pursuer, dt)
            if step > 150 and filt._initialized:
                samples.append(
                    float(np.linalg.norm(filt.estimate()[0].velocity - truth_velocity))
                )
        errors.append(float(np.mean(samples)))
        print(f"noise_scale={scale}: mean velocity error={errors[-1]:.2f} m/s")

    rho = _spearman_rho(list(NOISE_SCALES), errors)
    assert errors[0] < 1e-6, f"zero-noise estimate must be exact: {errors}"
    assert errors[-1] > errors[0] + 5.0, (
        f"expected high noise to worsen the velocity estimate: {errors}"
    )
    assert rho >= 0.6, (
        f"velocity error vs noise not monotonic (Spearman={rho:.3f}): {errors}"
    )


def test_miss_distance_stays_bounded_across_the_noise_sweep(tmp_path: Path):
    """With the rate-based estimator, PN holds intercept across the sweep."""

    n_seeds = 7
    medians = []
    rows = []
    for scale in NOISE_SCALES:
        misses = [_run_noisy_engagement(scale, seed=10_000 + i) for i in range(n_seeds)]
        med = float(np.median(misses))
        medians.append(med)
        for i, m in enumerate(misses):
            rows.append((scale, i, m))
        print(f"noise_scale={scale}: median_miss={med:.3f} m  misses={misses}")

    assert max(medians) < 50.0, (
        f"miss should stay near-intercept across the sweep now: {medians}"
    )

    csv_path = tmp_path / "miss_vs_noise.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("noise_scale,seed_index,miss_distance_m\n")
        for scale, idx, miss in rows:
            f.write(f"{scale},{idx},{miss:.6f}\n")
    assert csv_path.stat().st_size > 0


def test_perfect_info_still_intercepts_without_sensor():
    pursuer, target = _entities()
    sim = Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=ProportionalNavigation(navigation_constant=4.0),
        target_maneuver=NoManeuver(),
        config=SimulationConfig(
            dt=0.01, max_time=40.0, intercept_radius=5.0, autopilot_tau=0.0
        ),
    )
    result = sim.run()
    assert result.hit


def test_sensor_estimator_must_be_paired():
    pursuer, target = _entities()
    with pytest.raises(ValueError, match="sensor and estimator"):
        Simulation(
            pursuer=pursuer,
            target=target,
            guidance_law=ProportionalNavigation(),
            target_maneuver=NoManeuver(),
            sensor=Sensor(),
            estimator=None,
        )
