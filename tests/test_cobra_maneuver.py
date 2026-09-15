"""CobraManeuver / AttitudeAugmentedEntity: 3-DOF + attitude post-stall physics.

The key claim under test: the hang and the fall come out of the force
balance (thrust along body, aero collapsing with q, gravity), not from any
scripted trajectory. The only commands in these tests are throttle and
attitude rates.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.aerodynamics import ALPHA_STALL_RAD, post_stall_coefficients
from guidance_sim.physics.entities import AttitudeAugmentedEntity, PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import CobraManeuver
from guidance_sim.simulation.engine import Simulation, SimulationConfig

_DT = 0.01
# Generic fighter-class values, same airframe as test_evasive_maneuvers.
_VEHICLE = VehicleParams(
    mass=9_100.0,
    reference_area=45.0,
    drag_coefficient=0.035,
    max_normal_force_coefficient=1.1,
    max_load_factor=9.0,
)


def _cobra_target(velocity, altitude_m: float = 3_000.0) -> AttitudeAugmentedEntity:
    return AttitudeAugmentedEntity(
        name="target",
        state=State(position=[0.0, 0.0, altitude_m], velocity=velocity),
        vehicle=_VEHICLE,
        max_thrust=100_000.0,
    )


def _zoom_climb_velocity(speed: float = 150.0, gamma_deg: float = 60.0) -> list[float]:
    g = np.deg2rad(gamma_deg)
    return [speed * np.cos(g), 0.0, speed * np.sin(g)]


def test_post_stall_blend_is_continuous_through_stall_onset():
    alphas = np.deg2rad(np.linspace(5.0, 25.0, 20_001))  # 0.001 deg spacing
    cl, cd = np.array([post_stall_coefficients(a, cd0=0.035) for a in alphas]).T
    # A jump at the boundary would show up as one huge neighbour difference.
    assert np.max(np.abs(np.diff(cl))) < 1e-3
    assert np.max(np.abs(np.diff(cd))) < 1e-3
    # And the blend actually does something: CL collapses, CD rises.
    cl_stall, _ = post_stall_coefficients(ALPHA_STALL_RAD - np.deg2rad(2.0), 0.035)
    cl_85, _ = post_stall_coefficients(np.deg2rad(85.0), 0.035)
    _, cd_0 = post_stall_coefficients(0.0, 0.035)
    _, cd_90 = post_stall_coefficients(np.deg2rad(90.0), 0.035)
    assert cl_85 < 0.2 * cl_stall
    assert cd_90 > 20.0 * cd_0


def _hold_high_pitch_idle(target: AttitudeAugmentedEntity, duration_s: float):
    """Pitch to 88 deg and hold at idle thrust. No velocity/fall commands anywhere."""
    target.sync_attitude_to_velocity()
    target.attitude_active = True
    target.throttle = 0.02
    speeds, vzs = [], []
    for _ in range(int(round(duration_s / _DT))):
        target.theta_dot = 10.0 * (np.deg2rad(88.0) - target.theta)
        target.step(_DT, np.zeros(3))
        speeds.append(target.state.speed())
        vzs.append(float(target.state.velocity[2]))
    return np.array(speeds), np.array(vzs)


def test_high_pitch_low_thrust_bleeds_airspeed_monotonically_to_near_zero():
    target = _cobra_target(_zoom_climb_velocity())
    speeds, vzs = _hold_high_pitch_idle(target, duration_s=20.0)
    apex = int(np.argmax(vzs < 0.0))
    assert apex > 0, "vehicle never stopped climbing"
    climbing = speeds[: apex + 1]
    assert np.all(np.diff(climbing) <= 1e-9), "airspeed rose while climbing"
    assert climbing.min() < 5.0  # the hang


def test_fall_emerges_after_hang_without_a_fall_command():
    target = _cobra_target(_zoom_climb_velocity())
    speeds, vzs = _hold_high_pitch_idle(target, duration_s=20.0)
    hang = int(np.argmin(speeds))
    # Commands never changed (same pitch hold, same idle throttle), yet:
    assert vzs[hang - 50] > 0.0
    assert np.all(vzs[hang + 1 :] < 0.0)
    assert vzs[-1] < -5.0  # gravity-dominated fall is building


def test_inactive_attitude_entity_matches_point_mass_bit_for_bit():
    """Isolation: until CobraManeuver fires, the target IS a point mass."""
    point_mass = PointMassEntity(
        name="pm", state=State(position=[0.0, 0.0, 3_000.0], velocity=[240.0, 5.0, -3.0]),
        vehicle=_VEHICLE,
    )
    augmented = _cobra_target([240.0, 5.0, -3.0])
    cmd = np.array([0.0, 30.0, 10.0])
    for _ in range(300):
        point_mass.step(_DT, cmd, autopilot_tau=0.2)
        augmented.step(_DT, cmd, autopilot_tau=0.2)
    assert np.array_equal(point_mass.state.position, augmented.state.position)
    assert np.array_equal(point_mass.state.velocity, augmented.state.velocity)


def test_cobra_time_to_go_trigger():
    maneuver = CobraManeuver(_cobra_target([200.0, 0.0, 0.0]), trigger_time_to_go_s=5.0)
    target = State(position=[0.0, 0.0, 3_000.0], velocity=[200.0, 0.0, 0.0])
    far = State(position=[-5_000.0, 0.0, 3_000.0], velocity=[400.0, 0.0, 0.0])  # t_go 25 s
    near = State(position=[-800.0, 0.0, 3_000.0], velocity=[400.0, 0.0, 0.0])  # t_go 4 s
    maneuver.update_engagement(0.0, target, far)
    maneuver.lateral_accel(0.0, target)
    assert maneuver.phase == "armed"
    maneuver.update_engagement(1.0, target, near)
    maneuver.lateral_accel(1.0, target)
    assert maneuver.phase == "throttle_cut"


def test_cobra_runs_all_phases_to_recovery_through_simulation():
    target = _cobra_target(_zoom_climb_velocity(speed=160.0, gamma_deg=45.0))
    maneuver = CobraManeuver(target, trigger_time_s=1.0)
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(position=[-60_000.0, 0.0, 3_000.0], velocity=[300.0, 0.0, 0.0]),
        vehicle=VehicleParams(
            mass=50.0, reference_area=0.05, drag_coefficient=0.3,
            max_normal_force_coefficient=15.0, max_load_factor=25.0,
        ),
    )
    max_time = 40.0
    Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=ProportionalNavigation(navigation_constant=4.0),
        target_maneuver=maneuver,
        config=SimulationConfig(dt=_DT, max_time=max_time),
    ).run()

    phases = [name for _t, name in maneuver.phase_history]
    assert phases == list(CobraManeuver.PHASES)
    assert maneuver.phase == "recovered"
    assert maneuver.phase_history[-1][0] < max_time
    assert not target.attitude_active  # handed back to point-mass flight
