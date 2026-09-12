"""Visualization API catalog and WebSocket protocol tests."""

from fastapi.testclient import TestClient
import numpy as np
import pytest

from guidance_sim.api.live_stream import build_live_trajectory
from guidance_sim.api.main import app


def test_catalog_exposes_generic_grounded_profiles():
    response = TestClient(app).get("/api/catalog")

    assert response.status_code == 200
    catalog = response.json()
    assert catalog["data_source"] == "rollout"
    assert [item["id"] for item in catalog["guidance_laws"]] == [
        "pn",
        "apn",
        "ogl",
    ]
    assert [item["label"] for item in catalog["scenarios"]] == [
        "NoManeuver",
        "ConstantTurn",
        "SinusoidalWeave",
    ]
    assert [profile["name"] for profile in catalog["vehicle_profiles"]] == [
        "Interceptor A",
        "Target B",
    ]
    target_speed = next(
        profile["parameters"]["speed"]
        for profile in catalog["vehicle_profiles"]
        if profile["role"] == "target"
    )
    assert target_speed["value"] == pytest.approx(240.0)
    assert target_speed["reference_min"] == pytest.approx(200.0)
    assert target_speed["reference_max"] == pytest.approx(300.0)
    assert "FOI-ADMIRE-2005" in target_speed["source_ids"]
    assert "AIAA-CLIMB-2024" in target_speed["source_ids"]
    assert "NPS-GUIDANCE-2000" not in target_speed["source_ids"]
    live_controls = []
    for profile in catalog["vehicle_profiles"]:
        for parameter_name, parameter in profile["parameters"].items():
            assert parameter["reference_min"] <= parameter["value"]
            assert parameter["value"] <= parameter["reference_max"]
            assert parameter["basis"] in {
                "direct",
                "synthesized",
                "illustrative",
            }
            assert parameter["source_ids"]
            if parameter["live_control"]:
                live_controls.append(f"{profile['role']}.{parameter_name}")
                assert parameter["control_step"] > 0
    assert live_controls == ["interceptor.speed", "target.speed"]


def _run_ws_scenario(scenario_id: str, guidance_law: str = "pn"):
    with TestClient(app).websocket_connect("/ws/trajectory") as websocket:
        websocket.send_json(
            {
                "type": "stream.start",
                "scenario_id": scenario_id,
                "guidance_law": guidance_law,
                "frame_interval_ms": 0,
            }
        )
        started = websocket.receive_json()
        frames = [websocket.receive_json() for _ in range(started["frame_count"])]
        completed = websocket.receive_json()
    return started, frames, completed


def test_websocket_streams_ordered_live_engagement():
    started, frames, completed = _run_ws_scenario("crossing-intercept")

    assert started["type"] == "stream.started"
    assert started["data_source"] == "rollout"
    assert started["applied_parameters"] == {
        "interceptor.speed": 700.0,
        "target.speed": 240.0,
    }
    assert started["dt_s"] == pytest.approx(0.02)
    assert started["frame_count"] > 2

    assert all(frame["type"] == "trajectory.frame" for frame in frames)
    assert [frame["sequence"] for frame in frames] == list(range(len(frames)))
    assert all(
        frame["stream_id"] == started["stream_id"] for frame in frames
    )
    assert frames[0]["range_m"] > frames[-1]["range_m"]
    cmd_mags = []
    ach_mags = []
    for frame in frames:
        for key in (
            "pursuer_accel_cmd_m_s2",
            "pursuer_accel_achieved_m_s2",
        ):
            assert set(frame[key]) == {"x", "y", "z"}
            assert all(np.isfinite(frame[key][axis]) for axis in "xyz")
        cmd = np.array([frame["pursuer_accel_cmd_m_s2"][a] for a in "xyz"])
        ach = np.array([frame["pursuer_accel_achieved_m_s2"][a] for a in "xyz"])
        cmd_mags.append(float(np.linalg.norm(cmd)))
        ach_mags.append(float(np.linalg.norm(ach)))
    assert max(cmd_mags[1:-1]) > 1.0
    assert max(ach_mags[1:-1]) > 1.0
    g_limit = 25.0 * 9.80665
    assert max(cmd_mags) <= g_limit + 1e-3
    assert completed["type"] == "stream.completed"
    assert completed["stream_id"] == started["stream_id"]
    assert completed["outcome"] in {"intercept", "miss"}
    assert completed["frame_count"] == len(frames)
    assert completed["data_source"] == "rollout"
    # NoManeuver against PN is an easy geometry: expect a clean intercept.
    assert completed["outcome"] == "intercept"
    assert frames[-1]["pursuer_accel_cmd_m_s2"] == {"x": 0.0, "y": 0.0, "z": 0.0}
    assert frames[-1]["pursuer_accel_achieved_m_s2"] == {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }


def test_websocket_reruns_same_scenario_with_a_different_path():
    """Regression test: the picker used to replay one of two frozen files, so
    the same scenario always produced byte-identical target/interceptor
    trajectories. Live simulation with a fresh seed per stream should not.
    """

    _started_a, frames_a, _completed_a = _run_ws_scenario("evasive-climb")
    _started_b, frames_b, _completed_b = _run_ws_scenario("evasive-climb")

    target_a = frames_a[5]["target"]["position_m"]
    target_b = frames_b[5]["target"]["position_m"]
    assert target_a != target_b


def test_websocket_scenarios_drive_distinct_target_maneuvers():
    """crossing-intercept and head-on-intercept used to alias to the same
    captured file; they must now be genuinely different target behavior.
    """

    _started_none, frames_none, _c1 = _run_ws_scenario("crossing-intercept")
    _started_turn, frames_turn, _c2 = _run_ws_scenario("head-on-intercept")

    # A non-maneuvering target's lateral (y) position barely drifts; a
    # constant-turn target's does, by construction.
    target_y_none = [f["target"]["position_m"]["y"] for f in frames_none]
    target_y_turn = [f["target"]["position_m"]["y"] for f in frames_turn]
    assert max(target_y_none) - min(target_y_none) < 50.0
    assert max(target_y_turn) - min(target_y_turn) > 200.0


def test_websocket_rejects_unknown_scenario():
    with TestClient(app).websocket_connect("/ws/trajectory") as websocket:
        websocket.send_json(
            {
                "type": "stream.start",
                "scenario_id": "not-a-scenario",
                "guidance_law": "pn",
            }
        )
        error = websocket.receive_json()

    assert error["type"] == "stream.error"
    assert error["code"] == "invalid_request"


def test_websocket_rejects_out_of_range_live_parameter():
    with TestClient(app).websocket_connect("/ws/trajectory") as websocket:
        websocket.send_json(
            {
                "type": "stream.start",
                "scenario_id": "crossing-intercept",
                "guidance_law": "pn",
                "parameter_overrides": {"interceptor.speed": 1_200.0},
            }
        )
        error = websocket.receive_json()

    assert error["type"] == "stream.error"
    assert error["code"] == "invalid_parameter_override"
    assert "between 600 and 1000" in error["detail"]


def test_live_speed_overrides_reshape_the_trajectory():
    default = build_live_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="default",
        seed=12345,
    )
    overridden = build_live_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="overridden",
        parameter_overrides={
            "interceptor.speed": 600.0,
            "target.speed": 200.0,
        },
        seed=12345,
    )

    assert overridden.applied_parameters == {
        "interceptor.speed": 600.0,
        "target.speed": 200.0,
    }
    # Same seed (same sampled geometry) but different speeds must produce a
    # different concrete engagement -- speed overrides used to be validated
    # and echoed only, never reshaping the frozen rollout.
    assert overridden.frames[10].pursuer.position_m != (
        default.frames[10].pursuer.position_m
    )


@pytest.mark.parametrize(
    ("scenario_id", "expected_maneuver"),
    [
        ("crossing-intercept", "none"),
        ("head-on-intercept", "constant_turn"),
        ("evasive-climb", "weave"),
    ],
)
@pytest.mark.parametrize("guidance_law", ["pn", "apn", "ogl"])
def test_all_catalog_combinations_run_a_clean_live_episode(
    scenario_id,
    expected_maneuver,
    guidance_law,
):
    trajectory = build_live_trajectory(
        scenario_id,
        guidance_law,
        stream_id="test-stream",
        seed=42,
    )

    assert trajectory.maneuver == expected_maneuver
    assert trajectory.outcome in {"hit", "miss", "timeout"}
    assert len(trajectory.frames) > 2
    assert all(
        np.isfinite(
            [
                frame.range_m,
                frame.pursuer.position_m.x,
                frame.pursuer.position_m.y,
                frame.pursuer.position_m.z,
                frame.target.position_m.x,
                frame.target.position_m.y,
                frame.target.position_m.z,
                frame.pursuer_accel_cmd_m_s2.x,
                frame.pursuer_accel_achieved_m_s2.x,
            ]
        ).all()
        for frame in trajectory.frames
    )
