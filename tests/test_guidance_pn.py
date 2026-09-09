"""
Baseline correctness test: 3D Proportional Navigation must reliably
intercept a non-maneuvering target under real gravity + drag + a
g-limited airframe, from a range of 3D initial geometries. This is
the first sanity check on top of the realistic dynamics core, before
layering in the ML component.
"""

import numpy as np
import pytest

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import ConstantTurn, NoManeuver
from guidance_sim.simulation.engine import Simulation, SimulationConfig

# Generic, illustrative vehicle parameters (not derived from any real
# airframe). Structural g-limit dominates at these speeds/altitudes,
# which keeps intercept geometry tractable for a baseline test.
PURSUER_VEHICLE = VehicleParams(
    mass=50.0, reference_area=0.05, drag_coefficient=0.3,
    max_normal_force_coefficient=15.0, max_load_factor=25.0,
)
TARGET_VEHICLE = VehicleParams(
    mass=40.0, reference_area=0.06, drag_coefficient=0.35,
    max_normal_force_coefficient=10.0, max_load_factor=9.0,
)


def make_scenario(pursuer_pos, pursuer_vel, target_pos, target_vel):
    pursuer = PointMassEntity(
        name="pursuer", state=State(position=pursuer_pos, velocity=pursuer_vel),
        vehicle=PURSUER_VEHICLE,
    )
    target = PointMassEntity(
        name="target", state=State(position=target_pos, velocity=target_vel),
        vehicle=TARGET_VEHICLE,
    )
    return pursuer, target


def test_pn_intercepts_non_maneuvering_target_in_3d():
    pursuer, target = make_scenario(
        pursuer_pos=[0.0, 0.0, 3000.0], pursuer_vel=[350.0, 0.0, 0.0],
        target_pos=[6000.0, 800.0, 3400.0], target_vel=[-200.0, 0.0, 0.0],
    )
    guidance = ProportionalNavigation(navigation_constant=4.0)
    sim = Simulation(
        pursuer=pursuer, target=target, guidance_law=guidance,
        target_maneuver=NoManeuver(),
        config=SimulationConfig(
            dt=0.01, max_time=40.0, intercept_radius=5.0, autopilot_tau=0.0
        ),
    )
    result = sim.run()

    assert result.hit, f"Expected intercept, got miss_distance={result.miss_distance:.2f} m"
    assert result.time_to_intercept is not None
    assert result.miss_distance <= 5.0


def test_pn_intercepts_from_multiple_3d_offset_geometries():
    """Lateral AND vertical offsets, to actually exercise the 3D cross-product math."""
    offsets = [(200.0, 0.0), (-200.0, 0.0), (0.0, 500.0), (0.0, -500.0), (400.0, 300.0)]
    for lateral_offset, vertical_offset in offsets:
        pursuer, target = make_scenario(
            pursuer_pos=[0.0, 0.0, 2500.0], pursuer_vel=[350.0, 0.0, 0.0],
            target_pos=[7000.0, lateral_offset, 2500.0 + vertical_offset],
            target_vel=[-180.0, 0.0, 0.0],
        )
        guidance = ProportionalNavigation(navigation_constant=4.0)
        sim = Simulation(
            pursuer=pursuer, target=target, guidance_law=guidance,
            target_maneuver=NoManeuver(),
            config=SimulationConfig(
                dt=0.01, max_time=45.0, intercept_radius=5.0, autopilot_tau=0.0
            ),
        )
        result = sim.run()
        assert result.hit, (
            f"offset=({lateral_offset},{vertical_offset}): "
            f"expected intercept, miss={result.miss_distance:.2f} m"
        )


def test_pn_navigation_constant_must_be_positive():
    with pytest.raises(ValueError):
        ProportionalNavigation(navigation_constant=0.0)


def test_pn_struggles_more_as_target_maneuverability_increases():
    """
    Qualitative sanity check: a target pulling a hard constant turn
    should produce a larger (or equal) miss distance than a
    non-maneuvering target, all else equal.
    """
    def run_with_maneuver(maneuver):
        pursuer, target = make_scenario(
            pursuer_pos=[0.0, 0.0, 3000.0], pursuer_vel=[350.0, 0.0, 0.0],
            target_pos=[6000.0, 500.0, 3200.0], target_vel=[-160.0, 50.0, 0.0],
        )
        guidance = ProportionalNavigation(navigation_constant=3.0)
        sim = Simulation(
            pursuer=pursuer, target=target, guidance_law=guidance,
            target_maneuver=maneuver,
            config=SimulationConfig(
                dt=0.01, max_time=40.0, intercept_radius=5.0, autopilot_tau=0.0
            ),
        )
        return sim.run()

    result_straight = run_with_maneuver(NoManeuver())
    result_maneuvering = run_with_maneuver(ConstantTurn(accel=60.0))

    assert result_maneuvering.miss_distance >= result_straight.miss_distance - 1e-6
