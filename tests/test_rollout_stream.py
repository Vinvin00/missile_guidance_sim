"""Unit tests for the captured-RL rollout WebSocket adapter."""

import numpy as np
import pytest

from guidance_sim.api.rollout_stream import build_rollout_trajectory


def test_no_maneuver_rollout_matches_baseline_eval_miss():
    trajectory = build_rollout_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="unit",
    )
    assert trajectory.case_name == "no_maneuver_demo"
    # Golden value tied to outputs/rl_rollouts/no_maneuver_demo.json,
    # regenerated 2026-09-16 against the promoted evasive_zemtgo10_seed8
    # CP8 baseline (was 3.0468213306506464 under the prior seed3 baseline,
    # 1.4967420807277796 before the lateral_basis_from_previous continuity fix).
    assert trajectory.closest_approach_m == pytest.approx(1.4868842209629864)
    assert trajectory.dt_s == pytest.approx(0.02)
    assert trajectory.frames[0].time_s == 0.0
    assert trajectory.frames[-1].range_m <= 5.0


def test_accel_fields_are_populated_and_structurally_bounded():
    trajectory = build_rollout_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="accel",
    )
    g_limit = 25.0 * 9.80665
    cmd_mags = []
    ach_mags = []
    for frame in trajectory.frames:
        cmd = np.array(
            [
                frame.pursuer_accel_cmd_m_s2.x,
                frame.pursuer_accel_cmd_m_s2.y,
                frame.pursuer_accel_cmd_m_s2.z,
            ]
        )
        ach = np.array(
            [
                frame.pursuer_accel_achieved_m_s2.x,
                frame.pursuer_accel_achieved_m_s2.y,
                frame.pursuer_accel_achieved_m_s2.z,
            ]
        )
        cmd_mags.append(float(np.linalg.norm(cmd)))
        ach_mags.append(float(np.linalg.norm(ach)))
    assert max(cmd_mags[1:-1]) > 1.0
    assert max(ach_mags[1:-1]) > 1.0
    assert max(cmd_mags) <= g_limit + 1e-3
    assert max(ach_mags) <= g_limit + 1e-3
    assert cmd_mags[0] == pytest.approx(0.0)
    assert ach_mags[0] == pytest.approx(0.0)
    assert cmd_mags[-1] == pytest.approx(0.0)
    assert ach_mags[-1] == pytest.approx(0.0)


def test_weave_scenario_maps_to_group_a_weave_hit():
    trajectory = build_rollout_trajectory(
        "evasive-climb",
        "ogl",
        stream_id="weave",
    )
    assert trajectory.case_name == "weave_5g_070hz"
    assert trajectory.closest_approach_m == pytest.approx(4.117097597896631)
    assert trajectory.outcome == "hit"
