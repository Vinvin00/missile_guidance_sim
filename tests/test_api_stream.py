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
    for profile in catalog["vehicle_profiles"]:
        for parameter in profile["parameters"].values():
            assert parameter["reference_min"] <= parameter["value"]
            assert parameter["value"] <= parameter["reference_max"]
            assert parameter["basis"] in {
                "direct",
                "synthesized",
                "illustrative",
            }
            assert parameter["source_ids"]


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
