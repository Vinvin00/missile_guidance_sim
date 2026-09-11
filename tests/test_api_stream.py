"""Visualization API catalog and WebSocket protocol tests."""

from fastapi.testclient import TestClient
import numpy as np
import pytest

from guidance_sim.api.main import app
from guidance_sim.api.rollout_stream import build_rollout_trajectory


def test_catalog_exposes_generic_grounded_profiles():
    response = TestClient(app).get("/api/catalog")

    assert response.status_code == 200
    catalog = response.json()
    assert catalog["data_source"] == "synthetic"
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


def test_websocket_streams_ordered_rl_rollout():
    with TestClient(app).websocket_connect("/ws/trajectory") as websocket:
        websocket.send_json(
            {
                "type": "stream.start",
                "scenario_id": "crossing-intercept",
                "guidance_law": "pn",
                "frame_interval_ms": 0,
            }
        )
        started = websocket.receive_json()
        assert started["type"] == "stream.started"
        # Schema DataSource enum is still Literal["synthetic"]; value unchanged.
        assert started["data_source"] == "synthetic"
        assert started["applied_parameters"] == {
            "interceptor.speed": 700.0,
            "target.speed": 240.0,
        }
        assert started["dt_s"] == pytest.approx(0.02)
        assert started["frame_count"] > 2

        frames = [websocket.receive_json() for _ in range(started["frame_count"])]
        completed = websocket.receive_json()

    assert all(frame["type"] == "trajectory.frame" for frame in frames)
    assert [frame["sequence"] for frame in frames] == list(range(len(frames)))
    assert all(
        frame["stream_id"] == started["stream_id"] for frame in frames
    )
    assert frames[0]["range_m"] > frames[-1]["range_m"]
    assert frames[-1]["range_m"] <= 5.0
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
    assert frames[-1]["pursuer_accel_cmd_m_s2"] == {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }
    assert frames[-1]["pursuer_accel_achieved_m_s2"] == {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }
    assert completed == {
        "type": "stream.completed",
        "stream_id": started["stream_id"],
        "outcome": "intercept",
        "closest_approach_m": pytest.approx(1.2291061736251598, rel=0, abs=1e-9),
        "frame_count": len(frames),
        "data_source": "synthetic",
    }


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


def test_live_speed_overrides_are_echoed_without_reshaping_rollout():
    default = build_rollout_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="default",
    )
    overridden = build_rollout_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="overridden",
        parameter_overrides={
            "interceptor.speed": 600.0,
            "target.speed": 200.0,
        },
    )

    assert overridden.applied_parameters == {
        "interceptor.speed": 600.0,
        "target.speed": 200.0,
    }
    assert len(overridden.frames) == len(default.frames)
    assert overridden.closest_approach_m == pytest.approx(
        default.closest_approach_m
    )
    assert overridden.frames[10].pursuer.position_m == (
        default.frames[10].pursuer.position_m
    )


@pytest.mark.parametrize(
    ("scenario_id", "expected_case"),
    [
        ("crossing-intercept", "no_maneuver_demo"),
        ("head-on-intercept", "no_maneuver_demo"),
        ("evasive-climb", "weave_5g_070hz"),
    ],
)
@pytest.mark.parametrize("guidance_law", ["pn", "apn", "ogl"])
def test_all_catalog_combinations_stream_captured_hits(
    scenario_id,
    expected_case,
    guidance_law,
):
    trajectory = build_rollout_trajectory(
        scenario_id,
        guidance_law,
        stream_id="test-stream",
    )

    assert trajectory.case_name == expected_case
    assert trajectory.outcome == "hit"
    assert len(trajectory.frames) > 2
    assert trajectory.closest_approach_m <= 5.0
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
