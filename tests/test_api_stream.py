"""Visualization API catalog and WebSocket protocol tests."""

from fastapi.testclient import TestClient
import numpy as np
import pytest

from guidance_sim.api.main import app
from guidance_sim.api.mock_stream import build_mock_trajectory


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
    assert [profile["name"] for profile in catalog["vehicle_profiles"]] == [
        "Interceptor A",
        "Target B",
    ]
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


def test_websocket_streams_ordered_synthetic_trajectory():
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
        assert started["data_source"] == "synthetic"
        assert started["applied_parameters"] == {
            "interceptor.speed": 700.0,
            "target.speed": 240.0,
        }

        frames = [websocket.receive_json() for _ in range(started["frame_count"])]
        completed = websocket.receive_json()

    assert all(frame["type"] == "trajectory.frame" for frame in frames)
    assert [frame["sequence"] for frame in frames] == list(range(len(frames)))
    assert all(
        frame["stream_id"] == started["stream_id"] for frame in frames
    )
    assert frames[0]["range_m"] > frames[-1]["range_m"]
    assert frames[-1]["range_m"] <= 5.0
    assert completed == {
        "type": "stream.completed",
        "stream_id": started["stream_id"],
        "outcome": "intercept",
        "closest_approach_m": frames[-1]["range_m"],
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


def test_live_speed_overrides_change_preview_and_initial_state():
    default = build_mock_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="default",
    )
    slower = build_mock_trajectory(
        "crossing-intercept",
        "pn",
        stream_id="slower",
        parameter_overrides={
            "interceptor.speed": 600.0,
            "target.speed": 300.0,
        },
    )

    assert len(slower.frames) > len(default.frames)
    assert np.linalg.norm(
        [
            slower.frames[0].pursuer.velocity_m_s.x,
            slower.frames[0].pursuer.velocity_m_s.y,
            slower.frames[0].pursuer.velocity_m_s.z,
        ]
    ) == pytest.approx(600.0)
    assert np.linalg.norm(
        [
            slower.frames[0].target.velocity_m_s.x,
            slower.frames[0].target.velocity_m_s.y,
            slower.frames[0].target.velocity_m_s.z,
        ]
    ) == pytest.approx(300.0)


@pytest.mark.parametrize(
    "scenario_id",
    ["crossing-intercept", "head-on-intercept", "evasive-climb"],
)
@pytest.mark.parametrize("guidance_law", ["pn", "apn", "ogl"])
def test_all_catalog_combinations_produce_finite_intercept_previews(
    scenario_id,
    guidance_law,
):
    trajectory = build_mock_trajectory(
        scenario_id,
        guidance_law,
        stream_id="test-stream",
    )

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
            ]
        ).all()
        for frame in trajectory.frames
    )
