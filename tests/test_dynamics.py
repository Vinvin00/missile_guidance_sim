import numpy as np

from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.integrator import IntegratorType


def make_entity(position, velocity, drag_coefficient=0.3, reference_area=0.05, mass=50.0):
    return PointMassEntity(
        name="test-body",
        state=State(position=position, velocity=velocity),
        vehicle=VehicleParams(
            mass=mass,
            reference_area=reference_area,
            drag_coefficient=drag_coefficient,
            max_normal_force_coefficient=15.0,
            max_load_factor=25.0,
        ),
    )


def test_ballistic_fall_matches_projectile_motion_when_drag_negligible():
    """
    With negligible drag (tiny reference area) and no lateral command,
    a horizontally-launched body should fall close to the classical
    projectile-motion prediction z(t) = z0 - 1/2 * g * t^2.
    """
    entity = make_entity(
        position=[0.0, 0.0, 1000.0],
        velocity=[100.0, 0.0, 0.0],
        reference_area=1e-6,  # effectively drag-free
    )
    dt = 0.001
    duration = 5.0
    steps = int(duration / dt)
    for _ in range(steps):
        entity.step(dt, lateral_accel_cmd=np.zeros(3), integrator=IntegratorType.RK4)

    g = 9.80665
    expected_z = 1000.0 - 0.5 * g * duration ** 2
    assert np.isclose(entity.state.position[2], expected_z, atol=1.0)
    # Horizontal speed should be essentially unchanged with negligible drag.
    assert np.isclose(entity.state.velocity[0], 100.0, atol=0.5)


def test_body_falls_downward_over_time():
    entity = make_entity(position=[0.0, 0.0, 500.0], velocity=[50.0, 0.0, 0.0])
    initial_altitude = entity.state.altitude()
    for _ in range(500):
        entity.step(0.01, lateral_accel_cmd=np.zeros(3))
    assert entity.state.altitude() < initial_altitude


def test_drag_decelerates_a_coasting_body_in_level_flight():
    """
    A body moving horizontally loses forward speed to drag over time
    (isolating drag's effect on speed magnitude; some vertical
    velocity will appear from gravity, which is expected and fine --
    we're checking that the horizontal component bleeds off).
    """
    entity = make_entity(
        position=[0.0, 0.0, 1000.0],
        velocity=[300.0, 0.0, 0.0],
        drag_coefficient=1.0,
        reference_area=0.5,  # deliberately draggy body
    )
    initial_vx = entity.state.velocity[0]
    for _ in range(200):
        entity.step(0.01, lateral_accel_cmd=np.zeros(3))
    assert entity.state.velocity[0] < initial_vx


def test_lateral_command_is_clamped_and_perpendicular_to_velocity():
    """
    An absurdly large commanded acceleration should be clamped down
    to the airframe's available lateral accel, and the applied
    command should not have a component along the velocity vector
    (control surfaces steer, they don't directly change speed).
    """
    from guidance_sim.physics.dynamics import clamp_lateral_command

    velocity = np.array([300.0, 0.0, 0.0])
    huge_cmd = np.array([0.0, 100000.0, 5000.0])  # includes an along-track-ish component too
    clamped = clamp_lateral_command(
        velocity=velocity,
        lateral_accel_cmd=huge_cmd,
        altitude_m=1000.0,
        reference_area=0.05,
        drag_coefficient=0.3,
        max_normal_force_coefficient=15.0,
        mass=50.0,
        max_load_factor=25.0,
    )
    # No component along velocity direction.
    assert np.isclose(np.dot(clamped, velocity / np.linalg.norm(velocity)), 0.0, atol=1e-6)
    # Clamped to the structural limit (since this is high-q, structural-limited flight).
    assert np.linalg.norm(clamped) <= 25.0 * 9.80665 + 1e-6
