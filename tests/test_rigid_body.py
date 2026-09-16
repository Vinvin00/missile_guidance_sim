"""6-DOF rigid-body core: rotational EOM, quaternion hygiene, damping, and
the regression proving the 6-DOF model is a superset of the point mass."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.atmosphere import speed_of_sound
from guidance_sim.physics.controls import ActuatorLimits, actuator_step
from guidance_sim.physics.dynamics import rigid_body_derivative
from guidance_sim.physics.entities import (
    F16_6DOF,
    INTERCEPTOR_6DOF,
    PointMassEntity,
    RigidBodyEntity,
    State,
    VehicleParams,
)
from guidance_sim.physics.integrator import integrate_state
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.physics.rotational_dynamics import (
    angular_acceleration,
    body_to_world_matrix,
    quat_derivative,
    quat_from_euler,
    quat_to_euler,
    quat_to_rotation_matrix,
)
from guidance_sim.simulation.engine import Simulation, SimulationConfig


def test_quaternion_euler_round_trip_and_frame_convention():
    for angles in [(0.3, -0.7, 2.0), (-1.2, 1.4, -2.9), (0.0, 0.0, 0.0)]:
        assert np.allclose(quat_to_euler(quat_from_euler(*angles)), angles)
    # Identity attitude: nose +x_W, right wing -y_W, belly -z_W (world is z-up).
    assert np.allclose(body_to_world_matrix(np.array([1.0, 0.0, 0.0, 0.0])), np.diag([1.0, -1.0, -1.0]))
    # Positive pitch raises the nose in world z.
    assert body_to_world_matrix(quat_from_euler(0.0, 0.5, 0.0))[2, 0] > 0.0


def test_hamilton_quaternion_kinematics_match_rotation_about_body_axis():
    """q_dot = 1/2 q ⊗ ω: integrating a constant body pitch rate gives exactly that pitch angle."""
    q = quat_from_euler(0.2, 0.0, 0.0)  # rolled, so body pitch axis != world axis
    omega = np.array([0.0, 0.5, 0.0])
    for _ in range(1000):
        q = integrate_state(q, lambda y: quat_derivative(y, omega), 0.001)
    expected = quat_to_rotation_matrix(quat_from_euler(0.2, 0.0, 0.0)) @ quat_to_rotation_matrix(
        quat_from_euler(0.0, 0.5, 0.0)
    )
    assert np.allclose(quat_to_rotation_matrix(q), expected, atol=1e-9)


def test_quaternion_norm_stays_unit_over_long_integration():
    """Tumbling, unpowered vehicle for 200 s of sim time (10k RK4 steps) at a coarse step."""
    entity = RigidBodyEntity.from_state(State([0.0, 0.0, 9_000.0], [250.0, 0.0, 0.0]), F16_6DOF)
    entity.x[10:13] = [2.0, -0.7, 1.3]  # violent tumble
    entity.rate_cmd = np.zeros(3)  # autopilot fights it, actuators saturate: worst case for drift
    worst = 0.0
    for _ in range(10_000):  # 200 s at dt = 0.02
        entity.step(0.02, np.zeros(3))
        worst = max(worst, abs(np.linalg.norm(entity.x[6:10]) - 1.0))
        if entity.state.altitude() < 500.0:
            entity.x[2] = 9_000.0  # keep it in the atmosphere table; attitude is what we test
    assert worst < 1e-12


def test_renormalisation_is_what_keeps_the_norm():
    """Control: without the explicit renormalise, the same RK4 drifts measurably."""
    q = quat_from_euler(0.1, 0.2, 0.3)
    omega = np.array([3.0, -2.0, 4.0])
    for _ in range(20_000):
        q = integrate_state(q, lambda y: quat_derivative(y, omega), 0.02)
    assert abs(np.linalg.norm(q) - 1.0) > 1e-6


def test_zero_moment_keeps_angular_velocity_constant_about_principal_axes():
    # Missile: diagonal inertia, all three body axes principal. F-16: only y (Ixz couples x-z).
    for inertia, omega0 in ((INTERCEPTOR_6DOF.inertia, [0.8, 0.0, 0.0]),
                            (INTERCEPTOR_6DOF.inertia, [0.0, 0.0, -1.1]),
                            (F16_6DOF.inertia, [0.0, 0.8, 0.0])):
        omega = np.array(omega0)
        for _ in range(5_000):
            omega = integrate_state(omega, lambda w: angular_acceleration(inertia, w, np.zeros(3)), 0.01)
        assert np.allclose(omega, omega0, atol=1e-12)


def test_zero_moment_conserves_angular_momentum_and_energy_for_general_spin():
    """Torque-free, off-principal spin: w itself precesses, but |H| and rotational KE are invariant."""
    inertia = F16_6DOF.inertia
    omega = np.array([0.5, 0.3, -0.4])
    h0, e0 = np.linalg.norm(inertia @ omega), omega @ inertia @ omega
    for _ in range(5_000):
        omega = integrate_state(omega, lambda w: angular_acceleration(inertia, w, np.zeros(3)), 0.002)
    assert np.isclose(np.linalg.norm(inertia @ omega), h0, rtol=1e-9)
    assert np.isclose(omega @ inertia @ omega, e0, rtol=1e-9)


def _free_response(params, omega0, seconds, speed=250.0):
    """Controls frozen at zero, no thrust: only aero stability + damping act on the rates."""
    entity = RigidBodyEntity.from_state(State([0.0, 0.0, 3_000.0], [speed, 0.0, 0.0]), params)
    x = entity.x.copy()
    x[10:13] = omega0
    zero = np.zeros(5)
    dt = 0.002 if params is INTERCEPTOR_6DOF else 0.01
    rates = []
    for _ in range(int(seconds / dt)):
        x = integrate_state(x, lambda y: rigid_body_derivative(y, params, zero, 0.0), dt)
        x[6:10] /= np.linalg.norm(x[6:10])
        rates.append(x[10:13].copy())
    return np.array(rates)


def test_damping_derivatives_damp_an_initial_rate_perturbation():
    for params, seconds in ((F16_6DOF, 8.0), (INTERCEPTOR_6DOF, 2.0)):
        rates = _free_response(params, [0.5, 0.3, 0.2], seconds)
        start = np.abs(rates[:10]).max(axis=0)
        end = np.abs(rates[-len(rates) // 10 :]).max(axis=0)
        # Floor: an unpowered, untrimmed body keeps rotating at roughly the gravity
        # turn rate of its flight path (g/V ≈ 0.04 rad/s here). That is kinematics, not ringing.
        assert np.all(end < 0.1 * start + 9.80665 / 250.0), (start, end)
        assert np.all(end < 0.25 * start)


def test_damping_derivatives_are_what_damps_it():
    """Control: roll-rate perturbation with Clp zeroed doesn't decay (F-16 has no other roll damping here)."""
    from dataclasses import replace

    undamped = replace(F16_6DOF, aero=replace(F16_6DOF.aero, c_roll_p=0.0, c_roll_beta=0.0))
    damped = _free_response(F16_6DOF, [0.5, 0.0, 0.0], 4.0)[:, 0]
    free = _free_response(undamped, [0.5, 0.0, 0.0], 4.0)[:, 0]
    assert abs(damped[-1]) < 0.05
    assert abs(free[-1]) > 0.3


def test_actuator_respects_rate_and_position_limits():
    limits = ActuatorLimits(
        max_deflection=(0.4, 0.4, 0.4, 0.0, 0.0), max_rate=(1.0,) * 5, time_constant=(0.0,) * 5
    )
    delta = np.zeros(5)
    history = []
    for _ in range(100):
        delta = actuator_step(delta, np.array([5.0, -5.0, 0.1, 1.0, 1.0]), 0.01, limits)
        history.append(delta.copy())
    history = np.array(history)
    assert np.all(np.abs(np.diff(history, axis=0)) <= 0.01 + 1e-12)
    assert np.allclose(history[-1], [0.4, -0.4, 0.1, 0.0, 0.0])


# --- Regression: 6-DOF is a superset of the old point-mass behaviour ----------

_PM_PURSUER = INTERCEPTOR_6DOF.vehicle
_CONSTANT_AERO_INTERCEPTOR = replace(
    INTERCEPTOR_6DOF,
    aero=replace(INTERCEPTOR_6DOF.aero, mach_schedule=None),
)
_PM_TARGET = VehicleParams(mass=40.0, reference_area=0.06, drag_coefficient=0.35,
                           max_normal_force_coefficient=10.0, max_load_factor=9.0)


def test_regression_zero_command_flight_matches_point_mass_ballistic():
    """Trimmed (alpha = beta = 0, zero rates/deflections), no command: the old ballistic arc."""
    start = State([0.0, 0.0, 3_000.0], [350.0, 0.0, 0.0])
    rigid = RigidBodyEntity.from_state(start, _CONSTANT_AERO_INTERCEPTOR)
    point = PointMassEntity("pm", start.copy(), _PM_PURSUER)
    for _ in range(1_000):  # 10 s, ~490 m of gravity drop
        rigid.step(0.01, np.zeros(3))
        point.step(0.01, np.zeros(3))
    assert np.max(np.abs(np.degrees(rigid.deflection))) < 0.5
    assert np.linalg.norm(rigid.state.position - point.state.position) < 3.0
    assert np.linalg.norm(rigid.state.velocity - point.state.velocity) < 1.0


def test_regression_pn_intercept_matches_point_mass_demo_case():
    """Same demo intercept at the sim step (0.01 s) and the RL training step (0.02 s)."""
    for dt in (0.01, 0.02):
        def run(pursuer_entity):
            return Simulation(
                pursuer=pursuer_entity,
                target=PointMassEntity("t", State([7_000.0, 400.0, 3_300.0], [-200.0, 0.0, 0.0]), _PM_TARGET),
                guidance_law=ProportionalNavigation(navigation_constant=4.0),
                target_maneuver=NoManeuver(),
                config=SimulationConfig(dt=dt, max_time=30.0),
            ).run()

        start = State([0.0, 0.0, 3_000.0], [350.0, 0.0, 0.0])
        old = run(PointMassEntity("p", start.copy(), _PM_PURSUER))
        new = run(RigidBodyEntity.from_state(start, _CONSTANT_AERO_INTERCEPTOR, "p"))

        assert old.hit and new.hit, dt
        assert abs(new.time_to_intercept - old.time_to_intercept) < 0.1
        n = min(len(old.times), len(new.times))
        deviation = np.linalg.norm(old.pursuer_trajectory[:n] - new.pursuer_trajectory[:n], axis=1)
        assert deviation.max() < 10.0, dt  # metres, over a ~7 km engagement


def test_production_rigid_body_applies_transonic_drag_schedule():
    altitude = 3_000.0
    speed = 1.05 * speed_of_sound(altitude)
    state = State([0.0, 0.0, altitude], [speed, 0.0, 0.0])
    scheduled = RigidBodyEntity.from_state(state, INTERCEPTOR_6DOF)
    constant = RigidBodyEntity.from_state(state, _CONSTANT_AERO_INTERCEPTOR)
    zero = np.zeros(5)
    scheduled_dx = rigid_body_derivative(scheduled.x, scheduled.params, zero, 0.0)
    constant_dx = rigid_body_derivative(constant.x, constant.params, zero, 0.0)
    assert scheduled_dx[3] < constant_dx[3]


def test_rigid_body_telemetry_world_velocity_is_body_velocity_rotated():
    entity = RigidBodyEntity.from_state(State([0.0, 0.0, 3_000.0], [200.0, -50.0, 30.0]), F16_6DOF)
    assert np.allclose(entity.state.velocity, [200.0, -50.0, 30.0])
    assert np.allclose(entity.x[3:6], [np.linalg.norm([200.0, -50.0, 30.0]), 0.0, 0.0])  # alpha = beta = 0
    for _ in range(50):
        entity.step(0.01, np.array([0.0, 20.0, 0.0]))
    assert np.allclose(entity.state.velocity, entity.rotation_matrix_world() @ entity.x[3:6])
    assert np.any(np.abs(entity.deflection) > 1e-4)  # the turn was flown on the surfaces
