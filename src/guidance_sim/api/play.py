"""Play mode: a visitor flies the target against the frozen RL interceptor.

One ``PlayRound`` is one live episode of the same ``InterceptionEnv`` the
policy was trained and evaluated in; the only difference is the target's
maneuver, which is a ``PlayerManeuver`` fed by the visitor's keys. Finished
rounds are appended to a JSONL file (stick trace + seed + outcome) so they
can be replayed later as training/evaluation maneuvers.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import replace
from pathlib import Path
from threading import Lock

import gymnasium as gym
import numpy as np

from guidance_sim.api.catalog import resolve_live_parameters
from guidance_sim.api.live_stream import _body, _initial_condition_sampler, _vec3
from guidance_sim.api.schemas import TrajectoryFrame, Vector3
from guidance_sim.ml.policy_inference import get_shared_policy
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.maneuvers import PlayerManeuver
from guidance_sim.rl.actions import action_dimension
from guidance_sim.rl.environment import InterceptionEnv, TrackingConfig
from guidance_sim.rl.training import PPOTrainingConfig

# Front-quarter crossing start. A straight flight is caught, so doing nothing
# loses. It is beatable: scripted pilots that jink and then hold a hard turn
# inside 0.6-2.5 km escaped 42 of 120 rounds (2026-11-15), usually by a few
# metres. A tail chase was rejected: the interceptor is unpowered, so
# flying straight away simply outruns it and the round proves nothing.
PLAY_PARAMETERS = {
    "engagement.initial_range": 7_000.0,
    "engagement.lateral_offset": 0.0,
    "engagement.altitude_delta": 300.0,
    "engagement.target_heading": 120.0,
}
PLAYER_MAX_G = 9.0  # the env's default target structural limit
# Range opening for this long means the interceptor has flown past; without
# this a near miss drags on to the 45 s time limit.
ESCAPE_AFTER_OPENING_S = 3.0
MAX_ROUNDS_FILE_BYTES = 50_000_000  # stop logging before a free disk fills up

_REPO_ROOT = Path(__file__).resolve().parents[3]
_write_lock = Lock()


def rounds_path() -> Path:
    return Path(
        os.getenv("PLAYER_ROUNDS_PATH")
        or _REPO_ROOT / "outputs" / "player_rounds" / "rounds.jsonl"
    )


class PlayRound:
    def __init__(self, seed: int | None = None) -> None:
        self.policy = get_shared_policy()
        baseline = self.policy.baseline
        self.maneuver = PlayerManeuver(PLAYER_MAX_G * G0)
        self.env = InterceptionEnv(
            config=replace(
                PPOTrainingConfig().simulation_config(), max_time=baseline.max_time_s
            ),
            initial_condition_sampler=_initial_condition_sampler(
                resolve_live_parameters(PLAY_PARAMETERS)
            ),
            maneuver_factory=lambda _rng: self.maneuver,
            action_layout=baseline.action_layout,
            use_target_turn_rate_obs=baseline.use_target_turn_rate_obs,
            tracking=TrackingConfig(enabled=baseline.tracking_enabled),
        )
        n_action = action_dimension(baseline.action_layout)
        # Same wrapper the policy was trained/evaluated behind.
        self.stepper = gym.wrappers.RescaleAction(
            self.env,
            min_action=np.full(n_action, -1.0, dtype=np.float32),
            max_action=np.full(n_action, 1.0, dtype=np.float32),
        )
        self.seed = (
            int(np.random.SeedSequence().generate_state(1)[0]) if seed is None else seed
        )
        self.observation, self.info = self.stepper.reset(seed=self.seed)
        self.recurrent_state = None
        self.episode_start = np.array([True])
        self.inputs: list[list[float]] = []
        self.done = False
        self.sequence = 0
        self._opening_steps = 0

    def set_input(self, turn: object, pull: object) -> None:
        """Untrusted client input: anything not a finite number is ignored."""

        for name, value in (("turn", turn), ("pull", pull)):
            if isinstance(value, (int, float)) and np.isfinite(value):
                setattr(self.maneuver, name, float(np.clip(value, -1.0, 1.0)))

    def frame(self) -> dict[str, object]:
        env = self.env
        zero = Vector3(x=0.0, y=0.0, z=0.0)
        started = "action_commanded_m_s2" in self.info
        return TrajectoryFrame(
            stream_id="play",
            sequence=self.sequence,
            time_s=float(env.time_s),
            pursuer=_body(env.pursuer.state.position, env.pursuer.state.velocity),
            target=_body(env.target.state.position, env.target.state.velocity),
            range_m=float(self.info["range_m"]),
            pursuer_accel_cmd_m_s2=(
                _vec3(self.info["action_commanded_m_s2"]) if started else zero
            ),
            pursuer_accel_achieved_m_s2=(
                _vec3(self.info["action_achieved_m_s2"]) if started else zero
            ),
        ).model_dump(mode="json")

    def advance(self, steps: int = 1) -> dict[str, object]:
        for _ in range(steps):
            if self.done:
                break
            action, self.recurrent_state = self.policy.predict(
                self.observation,
                recurrent_state=self.recurrent_state,
                episode_start=self.episode_start,
            )
            self.episode_start[:] = False
            self.inputs.append([self.maneuver.turn, self.maneuver.pull])
            previous_range = float(self.info["range_m"])
            self.observation, _reward, terminated, truncated, self.info = (
                self.stepper.step(np.asarray(action, dtype=float).reshape(-1))
            )
            opening = float(self.info["range_m"]) > previous_range
            self._opening_steps = self._opening_steps + 1 if opening else 0
            self.done = bool(
                terminated
                or truncated
                or self._opening_steps * self.env.config.dt >= ESCAPE_AFTER_OPENING_S
            )
        self.sequence += 1
        return self.frame()

    def result(self) -> dict[str, object]:
        reason = self.info.get("termination_reason")
        if self.info.get("hit"):
            outcome = "caught"
        elif reason == "target_ground_impact":
            outcome = "crashed"
        else:
            outcome = "escaped"
        return {
            "outcome": outcome,
            "closest_approach_m": float(self.info["closest_approach_m"]),
            "time_s": float(self.env.time_s),
        }

    def save(self) -> None:
        record = {
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "seed": self.seed,
            "model": self.policy.baseline.model_path.name,
            "parameters": PLAY_PARAMETERS,
            "max_g": PLAYER_MAX_G,
            "dt_s": float(self.env.config.dt),
            **self.result(),
            "inputs": [[round(turn, 3), round(pull, 3)] for turn, pull in self.inputs],
        }
        path = rounds_path()
        with _write_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.stat().st_size > MAX_ROUNDS_FILE_BYTES:
                return
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")


def load_rounds() -> list[dict[str, object]]:
    path = rounds_path()
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def stats() -> dict[str, object]:
    # ponytail: re-reads the whole file per call; cache counts if it gets big.
    rounds = load_rounds()
    escapes = [r for r in rounds if r["outcome"] == "escaped"]
    return {
        "rounds": len(rounds),
        "caught": sum(r["outcome"] == "caught" for r in rounds),
        "escaped": len(escapes),
        "crashed": sum(r["outcome"] == "crashed" for r in rounds),
        "longest_survival_s": max((r["time_s"] for r in rounds), default=0.0),
    }
