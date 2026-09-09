"""Step 3b/3c: Augmented PN and Optimal Guidance Law."""

from __future__ import annotations

import numpy as np

from guidance_sim.guidance.augmented_pn import AugmentedProportionalNavigation
from guidance_sim.guidance.optimal_guidance import OptimalGuidance
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import NoManeuver, SinusoidalWeave
from guidance_sim.simulation.engine import Simulation, SimulationConfig, SimulationResult


PURSUER_VEHICLE = VehicleParams(
    mass=50.0, reference_area=0.05, drag_coefficient=0.3,
    max_normal_force_coefficient=15.0, max_load_factor=25.0,
)
TARGET_VEHICLE = VehicleParams(
    mass=40.0, reference_area=0.06, drag_coefficient=0.35,
    max_normal_force_coefficient=10.0, max_load_factor=9.0,
)


def _entities(pursuer_pos, pursuer_vel, target_pos, target_vel):
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(position=pursuer_pos, velocity=pursuer_vel),
        vehicle=PURSUER_VEHICLE,
    )
    target = PointMassEntity(
        name="target",
        state=State(position=target_pos, velocity=target_vel),
        vehicle=TARGET_VEHICLE,
    )
    return pursuer, target


def _truth_accel(target: PointMassEntity):
    return lambda: target.last_achieved_lateral_accel.copy()


def _run(guidance, maneuver, *, tau: float = 0.0, max_time: float = 40.0) -> SimulationResult:
    pursuer, target = _entities(
        [0.0, 0.0, 3000.0], [350.0, 0.0, 0.0],
        [6000.0, 800.0, 3400.0], [-180.0, 0.0, 0.0],
    )
    if hasattr(guidance, "a_target_est"):
        guidance.a_target_est = _truth_accel(target)
    return Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=guidance,
        target_maneuver=maneuver,
        config=SimulationConfig(
            dt=0.01, max_time=max_time, intercept_radius=5.0, autopilot_tau=tau
        ),
    ).run()


def test_apn_equals_pn_on_nomanuever():
    pursuer_a, target_a = _entities(
        [0.0, 0.0, 3000.0], [350.0, 0.0, 0.0],
        [6000.0, 400.0, 3300.0], [-200.0, 0.0, 0.0],
    )
    pursuer_b, target_b = _entities(
        [0.0, 0.0, 3000.0], [350.0, 0.0, 0.0],
        [6000.0, 400.0, 3300.0], [-200.0, 0.0, 0.0],
    )
    cfg = SimulationConfig(dt=0.01, max_time=40.0, intercept_radius=5.0, autopilot_tau=0.0)
    r_pn = Simulation(
        pursuer_a, target_a, ProportionalNavigation(4.0), NoManeuver(), cfg
    ).run()
    r_apn = Simulation(
        pursuer_b,
        target_b,
        AugmentedProportionalNavigation(4.0, a_target_est=lambda: np.zeros(3)),
        NoManeuver(),
        cfg,
    ).run()
    np.testing.assert_allclose(r_pn.pursuer_trajectory, r_apn.pursuer_trajectory, atol=1e-9)
    np.testing.assert_allclose(r_pn.pursuer_accel_cmd, r_apn.pursuer_accel_cmd, atol=1e-9)


def test_apn_vs_pn_maneuvering_miss_distance():
    """
    On a weave, APN with truth a_T should beat PN.
    (ConstantTurn + instantaneous rotating a_T is a known poor fit for the
    constant-accel APN assumption — reported in NOTES, not forced here.)
    """
    maneuver = SinusoidalWeave(amplitude=40.0, frequency_hz=0.25)
    r_pn = _run(ProportionalNavigation(4.0), maneuver)
    r_apn = _run(AugmentedProportionalNavigation(4.0), maneuver)
    assert r_apn.miss_distance <= r_pn.miss_distance + 1e-6, (
        f"APN did not beat PN: PN miss={r_pn.miss_distance:.3f} m, "
        f"APN miss={r_apn.miss_distance:.3f} m"
    )


def test_apn_lower_peak_g_near_intercept_than_pn():
    maneuver = SinusoidalWeave(amplitude=40.0, frequency_hz=0.25)
    r_pn = _run(ProportionalNavigation(4.0), maneuver)
    r_apn = _run(AugmentedProportionalNavigation(4.0), maneuver)

    def peak_tail(result: SimulationResult) -> float:
        n = len(result.times)
        sl = slice(max(0, int(0.8 * n)), None)
        return float(np.max(np.linalg.norm(result.pursuer_accel_cmd[sl], axis=1)))

    assert peak_tail(r_apn) <= peak_tail(r_pn) + 1.0, (
        f"APN peak-g tail {peak_tail(r_apn):.2f} > PN {peak_tail(r_pn):.2f}"
    )


def test_ogl_equals_apn_at_n3():
    """OGL(N=3) ≡ APN(N=3) with identical a_target_est (NoManeuver keeps identity)."""
    a_fixed = np.array([0.0, 25.0, 5.0])
    pursuer_a, target_a = _entities(
        [0.0, 0.0, 3000.0], [350.0, 0.0, 0.0],
        [6000.0, 500.0, 3200.0], [-160.0, 50.0, 0.0],
    )
    pursuer_b, target_b = _entities(
        [0.0, 0.0, 3000.0], [350.0, 0.0, 0.0],
        [6000.0, 500.0, 3200.0], [-160.0, 50.0, 0.0],
    )
    cfg = SimulationConfig(dt=0.01, max_time=40.0, intercept_radius=5.0, autopilot_tau=0.0)
    apn = AugmentedProportionalNavigation(3.0, a_target_est=lambda: a_fixed.copy())
    ogl = OptimalGuidance(3.0, a_target_est=lambda: a_fixed.copy())
    r_apn = Simulation(pursuer_a, target_a, apn, NoManeuver(), cfg).run()
    r_ogl = Simulation(pursuer_b, target_b, ogl, NoManeuver(), cfg).run()
    np.testing.assert_allclose(
        r_apn.pursuer_trajectory, r_ogl.pursuer_trajectory, rtol=1e-9, atol=1e-9
    )
    np.testing.assert_allclose(
        r_apn.pursuer_accel_cmd, r_ogl.pursuer_accel_cmd, rtol=1e-9, atol=1e-9
    )


def test_ogl_nomanuever_intercepts():
    r = _run(OptimalGuidance(3.0, a_target_est=lambda: np.zeros(3)), NoManeuver())
    assert r.hit, f"OGL miss={r.miss_distance:.2f} m"


def test_ogl_vs_pn_on_weave():
    maneuver = SinusoidalWeave(amplitude=40.0, frequency_hz=0.25)
    r_pn = _run(ProportionalNavigation(4.0), maneuver)
    r_ogl = _run(OptimalGuidance(4.0), maneuver)
    assert r_ogl.miss_distance <= r_pn.miss_distance + 1.0, (
        f"OGL miss={r_ogl.miss_distance:.3f} PN miss={r_pn.miss_distance:.3f}"
    )
