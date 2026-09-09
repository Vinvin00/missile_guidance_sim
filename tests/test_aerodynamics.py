import numpy as np

from guidance_sim.physics.aerodynamics import (
    available_lateral_accel,
    drag_deceleration,
    dynamic_pressure,
)
from guidance_sim.physics.atmosphere import RHO0


def test_dynamic_pressure_scales_with_speed_squared():
    q_100 = dynamic_pressure(RHO0, 100.0)
    q_200 = dynamic_pressure(RHO0, 200.0)
    assert np.isclose(q_200, 4 * q_100)


def test_drag_deceleration_increases_with_speed():
    slow = drag_deceleration(RHO0, 100.0, drag_coefficient=0.3, reference_area=0.05, mass=50.0)
    fast = drag_deceleration(RHO0, 300.0, drag_coefficient=0.3, reference_area=0.05, mass=50.0)
    assert fast > slow


def test_drag_deceleration_zero_at_zero_speed():
    assert drag_deceleration(RHO0, 0.0, 0.3, 0.05, 50.0) == 0.0


def test_available_lateral_accel_is_structurally_limited_at_high_speed():
    """At high dynamic pressure, the aero limit should exceed the
    structural g-limit, so the structural limit binds."""
    a_max = available_lateral_accel(
        rho=RHO0, speed=400.0, reference_area=0.05,
        max_normal_force_coefficient=15.0, mass=50.0, max_load_factor=25.0,
    )
    assert np.isclose(a_max, 25.0 * 9.80665)


def test_available_lateral_accel_is_aero_limited_at_low_speed():
    """At very low dynamic pressure (low speed, thin air), the
    aerodynamic limit should be the binding constraint, well below
    the structural limit."""
    a_max = available_lateral_accel(
        rho=RHO0, speed=20.0, reference_area=0.05,
        max_normal_force_coefficient=15.0, mass=50.0, max_load_factor=25.0,
    )
    assert a_max < 25.0 * 9.80665


def test_available_lateral_accel_increases_with_speed_until_structural_cap():
    speeds = [10, 50, 100, 200, 400, 800]
    accels = [
        available_lateral_accel(RHO0, s, 0.05, 15.0, 50.0, 25.0) for s in speeds
    ]
    # Non-decreasing (aero limit grows with q, then structural cap flattens it).
    assert all(accels[i] <= accels[i + 1] + 1e-9 for i in range(len(accels) - 1))
