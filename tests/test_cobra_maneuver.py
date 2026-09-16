"""CobraManeuver on the 6-DOF rigid body.

The key claim under test: the pitch-up, hang and fall come out of control
deflections -> moments -> Euler's equations, and out of the force balance.
Nothing scripts attitude or trajectory. The only commands in these tests
are throttle and body-rate commands, and those go through the autopilot
and rate-limited actuators.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.aerodynamics import ALPHA_STALL_RAD, post_stall_coefficients
from guidance_sim.physics.controls import ELEVATOR, TV_PITCH
from guidance_sim.physics.entities import F16_6DOF, INTERCEPTOR_6DOF, RigidBodyEntity, State
from guidance_sim.physics.maneuvers import CobraManeuver
from guidance_sim.physics.rotational_dynamics import quat_from_euler
from guidance_sim.simulation.engine import Simulation, SimulationConfig

_DT = 0.01


def _cobra_target(velocity, altitude_m: float = 3_000.0) -> RigidBodyEntity:
    return RigidBodyEntity.from_state(State(position=[0.0, 0.0, altitude_m], velocity=velocity), F16_6DOF, "target")


def _zoom_climb_velocity(speed: float = 150.0, gamma_deg: float = 75.0) -> list[float]:
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


def _hold_high_pitch_idle(target: RigidBodyEntity, duration_s: float):
    """Command pitch rate toward 88 deg at idle thrust. No velocity/fall commands anywhere."""
    target.throttle = 0.02
    speeds, vzs = [], []
    for _ in range(int(round(duration_s / _DT))):
        theta = target.euler_angles()[1]
        target.rate_cmd = np.array([0.0, np.clip(3.0 * (np.deg2rad(88.0) - theta), -1.0, 1.0), 0.0])
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


def test_cobra_end_to_end_6dof_climb_hang_spiral_recovery_from_real_control_inputs():
    """Integration: full Cobra through Simulation, both vehicles 6-DOF."""
    target = _cobra_target(_zoom_climb_velocity(speed=160.0, gamma_deg=45.0))
    maneuver = CobraManeuver(target, trigger_time_s=1.0)
    pursuer = RigidBodyEntity.from_state(
        State(position=[-60_000.0, 0.0, 3_000.0], velocity=[300.0, 0.0, 0.0]), INTERCEPTOR_6DOF, "pursuer"
    )

    samples = []  # (phase, altitude, speed, pitch, elevator, tv_pitch)
    original = maneuver.lateral_accel

    def recording_lateral_accel(t, state):
        command = original(t, state)
        samples.append((maneuver.phase, state.altitude(), state.speed(), target.euler_angles()[1],
                        target.deflection[ELEVATOR], target.deflection[TV_PITCH]))
        return command

    maneuver.lateral_accel = recording_lateral_accel
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
    assert maneuver.phase_history[-1][0] < max_time
    assert target.rate_cmd is None  # handed back to the accel autopilot

    by_phase = {p: [s for s in samples if s[0] == p] for p in CobraManeuver.PHASES}
    start_alt = samples[0][1]
    # Climb: altitude gained during pitch-up, and the nose really got near vertical.
    assert max(s[1] for s in by_phase["pitch_up"]) > start_alt + 300.0
    assert max(s[3] for s in by_phase["pitch_up"] + by_phase["hang"]) > np.deg2rad(85.0)
    # The pitch-up was flown on the elevator (saturating), not a rate shortcut.
    assert min(s[4] for s in by_phase["pitch_up"]) < -0.5 * F16_6DOF.actuators.max_deflection[ELEVATOR]
    # Hang: slow, and thrust vectoring is doing the pitch work where q is gone.
    assert min(s[2] for s in by_phase["hang"]) < 40.0
    assert max(abs(s[5]) for s in by_phase["hang"]) > np.deg2rad(1.0)
    # Spiral: altitude lost, airspeed rebuilt.
    spiral = by_phase["spiral"]
    assert spiral[-1][1] < spiral[0][1] - 100.0
    assert spiral[-1][2] > spiral[0][2] + 20.0


def test_hold_level_until_trigger_cruises_instead_of_sinking():
    target = _cobra_target([150.0, 0.0, 0.0])
    maneuver = CobraManeuver(target, trigger_time_s=1e9, hold_level_until_trigger=True)
    for step in range(1_000):  # 10 s
        target.step(_DT, maneuver.lateral_accel(step * _DT, target.state))
    assert maneuver.phase == "armed"
    assert abs(target.state.altitude() - 3_000.0) < 20.0  # lift-less glide sinks ~490 m
    assert abs(target.state.speed() - 150.0) < 5.0  # throttle trims out drag


def test_body_up_is_orthogonal_to_nose_and_rolls_with_bank():
    target = _cobra_target([150.0, 0.0, 0.0])
    theta, psi = np.deg2rad(30.0), np.deg2rad(40.0)
    target.x[6:10] = quat_from_euler(0.0, theta, psi)
    level_up = target.body_up()
    assert level_up[2] > 0.0  # canopy up when wings level
    target.x[6:10] = quat_from_euler(np.deg2rad(60.0), theta, psi)
    banked_up = target.body_up()
    for up in (level_up, banked_up):
        assert np.isclose(np.linalg.norm(up), 1.0)
        assert np.isclose(np.dot(up, target.body_axis()), 0.0)
    assert np.isclose(np.degrees(np.arccos(np.dot(level_up, banked_up))), 60.0)
