import numpy as np

from guidance_sim.physics.aerodynamics import (
    AeroDerivatives,
    MachAeroSchedule,
    available_lateral_accel,
    body_aero_force,
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


def test_mach_schedule_interpolates_and_clamps_to_its_envelope():
    schedule = MachAeroSchedule(
        mach=(0.5, 1.0, 2.0),
        cd0_multiplier=(1.0, 2.0, 1.5),
        normal_force_slope_multiplier=(1.0, 0.8, 0.6),
    )
    assert schedule.coefficients(0.0) == (1.0, 1.0)
    assert np.allclose(schedule.coefficients(0.75), (1.5, 0.9))
    assert schedule.coefficients(3.0) == (1.5, 0.6)


def test_mach_schedule_rejects_malformed_tables():
    import pytest

    with pytest.raises(ValueError, match="same length"):
        MachAeroSchedule((0.0, 1.0), (1.0,), (1.0, 1.0))
    with pytest.raises(ValueError, match="strictly increasing"):
        MachAeroSchedule((0.0, 1.0, 1.0), (1.0, 2.0, 2.0), (1.0, 1.0, 1.0))


def test_transonic_schedule_raises_drag_and_reduces_normal_force():
    schedule = MachAeroSchedule(
        mach=(0.0, 1.0, 2.0),
        cd0_multiplier=(1.0, 2.0, 1.5),
        normal_force_slope_multiplier=(1.0, 0.8, 0.7),
    )
    aero = AeroDerivatives(
        span=1.0, chord=1.0, cl_alpha=4.0, alpha_stall=np.deg2rad(30.0), k_induced=0.0,
        cy_beta=0.0, cy_dr=0.0, c_pitch_alpha=0.0, c_pitch_q=0.0, c_pitch_de=0.0,
        c_roll_beta=0.0, c_roll_p=0.0, c_roll_da=0.0, c_roll_dr=0.0,
        c_yaw_beta=0.0, c_yaw_r=0.0, c_yaw_dr=0.0, mach_schedule=schedule,
    )
    alpha = np.deg2rad(5.0)
    velocity = 200.0 * np.array([np.cos(alpha), 0.0, np.sin(alpha)])
    subsonic = body_aero_force(velocity, 1.0, 1.0, 0.1, aero, mach=0.0)
    transonic = body_aero_force(velocity, 1.0, 1.0, 0.1, aero, mach=1.0)
    v_hat = velocity / np.linalg.norm(velocity)
    drag_sub = -float(np.dot(subsonic, v_hat))
    drag_transonic = -float(np.dot(transonic, v_hat))
    normal_sub = np.linalg.norm(subsonic + drag_sub * v_hat)
    normal_transonic = np.linalg.norm(transonic + drag_transonic * v_hat)
    assert np.isclose(drag_transonic, 2.0 * drag_sub)
    assert np.isclose(normal_transonic, 0.8 * normal_sub)
