"""Play mode: player-steered target, live round, saved rounds."""

import json

import numpy as np
import pytest
from fastapi.testclient import TestClient

from guidance_sim.api import play
from guidance_sim.api.main import app
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import PlayerManeuver


@pytest.fixture(autouse=True)
def rounds_file(tmp_path, monkeypatch):
    path = tmp_path / "rounds.jsonl"
    monkeypatch.setenv("PLAYER_ROUNDS_PATH", str(path))
    return path


def test_player_maneuver_is_lateral_and_scaled_by_the_stick():
    state = State(position=[0.0, 0.0, 3000.0], velocity=[200.0, 0.0, 0.0])
    maneuver = PlayerManeuver(9.0 * G0)

    assert np.allclose(maneuver.lateral_accel(0.0, state), 0.0)
    maneuver.turn, maneuver.pull = 1.0, 0.0
    assert np.allclose(maneuver.lateral_accel(0.0, state), [0.0, 9.0 * G0, 0.0])  # left
    maneuver.turn, maneuver.pull = 0.0, -0.5
    assert np.allclose(maneuver.lateral_accel(0.0, state), [0.0, 0.0, -4.5 * G0])  # dive
    maneuver.turn, maneuver.pull = 5.0, 0.0  # out-of-range stick is clipped
    command = maneuver.lateral_accel(0.0, state)
    assert np.isclose(np.linalg.norm(command), 9.0 * G0)
    assert abs(np.dot(command, state.velocity)) < 1e-9


def test_player_maneuver_replays_a_recorded_trace():
    state = State(position=[0.0, 0.0, 3000.0], velocity=[200.0, 0.0, 0.0])
    maneuver = PlayerManeuver(10.0, trace=[[1.0, 0.0], [0.0, 1.0]], dt=0.02)

    assert np.allclose(maneuver.lateral_accel(0.0, state), [0.0, 10.0, 0.0])
    assert np.allclose(maneuver.lateral_accel(0.02, state), [0.0, 0.0, 10.0])
    assert np.allclose(maneuver.lateral_accel(9.0, state), [0.0, 0.0, 10.0])  # holds last


def test_a_passive_pilot_is_caught_and_the_round_replays_exactly(rounds_file):
    game = play.PlayRound(seed=3)
    game.set_input("left", float("nan"))  # garbage input is ignored
    while not game.done:
        game.set_input(1.0 if game.env.time_s > 5.0 else 0.0, 0.0)
        game.advance()
    game.save()

    saved = json.loads(rounds_file.read_text())
    assert saved["outcome"] == game.result()["outcome"] == "caught"
    assert play.stats()["caught"] == 1

    # The saved stick trace + seed reproduce the same round: this is what
    # makes saved human rounds usable as training/evaluation maneuvers.
    replay = play.PlayRound(seed=saved["seed"])
    replay.maneuver.trace = np.asarray(saved["inputs"])
    while not replay.done:
        replay.advance()
    assert replay.result()["closest_approach_m"] == pytest.approx(
        saved["closest_approach_m"], abs=0.05
    )


def test_play_websocket_runs_a_round_and_saves_it(rounds_file, monkeypatch):
    monkeypatch.setattr(play, "PLAY_PARAMETERS", {**play.PLAY_PARAMETERS, "engagement.initial_range": 2000.0, "engagement.target_heading": 180.0})
    with TestClient(app).websocket_connect("/ws/play") as socket:
        ready = socket.receive_json()
        assert ready["type"] == "play.ready" and ready["frame"]["sequence"] == 0
        socket.send_json({"turn": 1, "pull": 0})
        frames = 0
        while (message := socket.receive_json())["type"] == "trajectory.frame":
            frames += 1
    assert frames > 10
    assert message["type"] == "play.completed"
    assert message["outcome"] in {"caught", "escaped", "crashed"}
    assert message["stats"]["rounds"] == 1
    assert TestClient(app).get("/api/play/stats").json()["rounds"] == 1


def test_saved_rounds_feed_retraining(rounds_file):
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "retrain_from_rounds",
        Path(__file__).resolve().parents[1] / "scripts" / "retrain_from_rounds.py",
    )
    retrain = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(retrain)

    game = play.PlayRound(seed=3)
    while not game.done:
        game.advance()
    game.save()
    records = play.load_rounds()

    # A saved round runs through the existing eval loop as a case.
    result = retrain.score(
        game.policy._model, retrain.finetune_config(), retrain.round_cases(records)
    )
    assert result["hits"] == result["cases"] == 1  # passive pilot is still caught

    # Training mix: human_fraction picks replayed rounds vs evasive episodes.
    rng = np.random.default_rng(0)
    for fraction, expect_player in ((1.0, True), (0.0, False)):
        initial_conditions, maneuver = retrain.mixed_samplers(records, fraction)
        initial_conditions(rng)
        assert isinstance(maneuver(rng), PlayerManeuver) is expect_player

    assert [len(part) for part in retrain.split_rounds(list(range(8)))] == [6, 2]
    same = {"frozen": {"hits": 5, "max_miss_m": 9.0}, "human_held_out": {"hits": 1}}
    better = {"frozen": {"hits": 5, "max_miss_m": 9.0}, "human_held_out": {"hits": 2}}
    assert retrain.verdict(same, same)[0] is False
    assert retrain.verdict(same, better)[0] is True
