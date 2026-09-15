"""Live, step-by-step RL-policy inference sessions for the guidance API.

This backs ``POST /api/guidance/session`` and ``POST /api/guidance/step``.
Unlike ``rollout_stream.py`` (which replays a pre-captured JSON episode), a
session here holds a live ``InterceptionEnv`` -- the same scenario/physics
stepping code used by ``guidance_sim.rl.training.evaluate_policy`` and by
``scripts/capture_rl_rollout.py`` -- and asks the frozen policy for one
action per ``step`` call. Physics is therefore byte-for-byte the same code
path as a fresh evaluation run; only the frozen checkpoint load path is new
(``guidance_sim.ml.policy_inference``).

Sessions live in an in-process dict. That is adequate for a single-worker
API process driving a handful of interactive/verification sessions; it is
not meant to survive a process restart or scale across workers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import gymnasium as gym
import numpy as np

from guidance_sim.ml.policy_inference import FrozenPolicy, get_shared_policy
from guidance_sim.physics.maneuvers import ConstantTurn, ManeuverProfile, NoManeuver, SinusoidalWeave
from guidance_sim.rl.actions import action_dimension
from guidance_sim.rl.environment import InterceptionEnv, TrackingConfig
from guidance_sim.rl.training import FIXED_EVALUATION_CASES, PPOTrainingConfig

_FIXED_CASES_BY_NAME = {case.name: case for case in FIXED_EVALUATION_CASES}
# Matches evaluate_policy()/capture_rl_rollout.py's seed convention
# (seed + case_index) exactly, so a named-case live session reproduces the
# same sensor-noise/latency draw as the offline capture for that case. This
# only became observable once tracking (which makes the seed matter -- it
# drives the stochastic update-rate/latency/noise draw) was enabled for the
# live path: previously reset() ignoring case_index was silently harmless.
_FIXED_CASE_INDEX = {case.name: index for index, case in enumerate(FIXED_EVALUATION_CASES)}


class LiveGuidanceError(ValueError):
    """Raised for invalid session-start/step requests (mapped to HTTP 400)."""


class SessionNotFoundError(KeyError):
    """Raised when a step is requested against an unknown/expired session."""


def _maneuver_from_spec(
    kind: str,
    accel_g: float,
    frequency_hz: float,
    phase_rad: float,
) -> ManeuverProfile:
    from guidance_sim.physics.atmosphere import G0

    if kind == "none":
        return NoManeuver()
    if kind == "constant_turn":
        return ConstantTurn(accel=accel_g * G0)
    if kind == "weave":
        return SinusoidalWeave(
            amplitude=accel_g * G0,
            frequency_hz=frequency_hz,
            phase=phase_rad,
        )
    raise LiveGuidanceError(f"unsupported target_maneuver.kind: {kind!r}")


def _fixed_case_ingredients(case_name: str):
    if case_name not in _FIXED_CASES_BY_NAME:
        raise LiveGuidanceError(
            f"unknown case_name: {case_name!r}; known cases: "
            f"{sorted(_FIXED_CASES_BY_NAME)}"
        )
    from guidance_sim.rl.training import _case_initial_conditions, _case_maneuver

    case = _FIXED_CASES_BY_NAME[case_name]
    return _case_initial_conditions(case), _case_maneuver(case)


def _custom_ingredients(
    pursuer_position_m: tuple[float, float, float],
    pursuer_velocity_m_s: tuple[float, float, float],
    target_position_m: tuple[float, float, float],
    target_velocity_m_s: tuple[float, float, float],
    maneuver_kind: str,
    maneuver_accel_g: float,
    maneuver_frequency_hz: float,
    maneuver_phase_rad: float,
):
    from guidance_sim.physics.entities import State

    def sample(_rng: np.random.Generator) -> tuple[State, State]:
        return (
            State(position=list(pursuer_position_m), velocity=list(pursuer_velocity_m_s)),
            State(position=list(target_position_m), velocity=list(target_velocity_m_s)),
        )

    def make(_rng: np.random.Generator) -> ManeuverProfile:
        return _maneuver_from_spec(
            maneuver_kind, maneuver_accel_g, maneuver_frequency_hz, maneuver_phase_rad
        )

    return sample, make


@dataclass
class LiveGuidanceSession:
    session_id: str
    physical_env: InterceptionEnv
    env: gym.Env
    policy: FrozenPolicy
    recurrent_state: Any
    episode_start: np.ndarray
    sequence: int
    observation: np.ndarray
    done: bool


_SESSIONS: dict[str, LiveGuidanceSession] = {}


def _vec3(values: np.ndarray) -> dict[str, float]:
    arr = np.asarray(values, dtype=float).reshape(3)
    return {"x": float(arr[0]), "y": float(arr[1]), "z": float(arr[2])}


def _body(position: np.ndarray, velocity: np.ndarray) -> dict[str, object]:
    return {"position_m": _vec3(position), "velocity_m_s": _vec3(velocity)}


def _frame_payload(session: LiveGuidanceSession, info: dict[str, object]) -> dict[str, object]:
    env = session.physical_env
    assert env.pursuer is not None and env.target is not None
    return {
        "session_id": session.session_id,
        "sequence": session.sequence,
        "time_s": float(env.time_s),
        "pursuer": _body(env.pursuer.state.position, env.pursuer.state.velocity),
        "target": _body(env.target.state.position, env.target.state.velocity),
        "range_m": float(info["range_m"]),
        "pursuer_accel_cmd_m_s2": _vec3(info["action_commanded_m_s2"]),
        "pursuer_accel_achieved_m_s2": _vec3(info["action_achieved_m_s2"]),
        "terminated": bool(info["outcome"] != "ongoing"),
        "outcome": str(info["outcome"]),
        "hit": bool(info["hit"]),
    }


def start_session(
    *,
    case_name: str | None,
    pursuer_position_m: tuple[float, float, float] | None,
    pursuer_velocity_m_s: tuple[float, float, float] | None,
    target_position_m: tuple[float, float, float] | None,
    target_velocity_m_s: tuple[float, float, float] | None,
    maneuver_kind: str,
    maneuver_accel_g: float,
    maneuver_frequency_hz: float,
    maneuver_phase_rad: float,
    seed: int,
    policy: FrozenPolicy | None = None,
) -> dict[str, object]:
    """Reset a fresh ``InterceptionEnv`` and return its initial frame."""

    custom_fields = (
        pursuer_position_m,
        pursuer_velocity_m_s,
        target_position_m,
        target_velocity_m_s,
    )
    if case_name is not None and any(field is not None for field in custom_fields):
        raise LiveGuidanceError("pass either case_name or an explicit pursuer/target state, not both")
    if case_name is not None:
        initial_condition_sampler, maneuver_factory = _fixed_case_ingredients(case_name)
        seed = seed + _FIXED_CASE_INDEX[case_name]
    else:
        if any(field is None for field in custom_fields):
            raise LiveGuidanceError(
                "custom sessions require pursuer_position_m, pursuer_velocity_m_s, "
                "target_position_m, and target_velocity_m_s"
            )
        initial_condition_sampler, maneuver_factory = _custom_ingredients(
            pursuer_position_m,  # type: ignore[arg-type]
            pursuer_velocity_m_s,  # type: ignore[arg-type]
            target_position_m,  # type: ignore[arg-type]
            target_velocity_m_s,  # type: ignore[arg-type]
            maneuver_kind,
            maneuver_accel_g,
            maneuver_frequency_hz,
            maneuver_phase_rad,
        )

    policy = policy or get_shared_policy()
    baseline = policy.baseline
    config = PPOTrainingConfig(
        action_layout=baseline.action_layout,
        use_target_turn_rate_obs=baseline.use_target_turn_rate_obs,
        # The evasive lineage trained on a 45s budget, not the frozen
        # lineage's 25s default -- serving under the old default would
        # truncate genuine in-progress intercepts as spurious timeouts.
        max_time=baseline.max_time_s,
    ).simulation_config()
    n_action = action_dimension(baseline.action_layout)

    physical_env = InterceptionEnv(
        config=config,
        initial_condition_sampler=initial_condition_sampler,
        maneuver_factory=maneuver_factory,
        action_layout=baseline.action_layout,
        use_target_turn_rate_obs=baseline.use_target_turn_rate_obs,
        # Must match the baseline's own training-time obs contract, same
        # reasoning as live_stream.py's build_live_trajectory -- a mismatch
        # here is a hard obs-shape crash, not a silent degradation.
        tracking=TrackingConfig(enabled=baseline.tracking_enabled),
    )
    env = gym.wrappers.RescaleAction(
        physical_env,
        min_action=np.full(n_action, -1.0, dtype=np.float32),
        max_action=np.full(n_action, 1.0, dtype=np.float32),
    )
    observation, info = env.reset(seed=seed)

    session_id = str(uuid4())
    session = LiveGuidanceSession(
        session_id=session_id,
        physical_env=physical_env,
        env=env,
        policy=policy,
        recurrent_state=None,
        episode_start=np.array([True], dtype=bool),
        sequence=0,
        observation=observation,
        done=False,
    )
    _SESSIONS[session_id] = session
    return _frame_payload(session, info)


def step_session(session_id: str) -> dict[str, object]:
    """Ask the frozen policy for one live action and advance physics by one step."""

    session = _SESSIONS.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    if session.done:
        raise LiveGuidanceError(f"session {session_id} has already terminated")

    n_action = action_dimension(session.policy.baseline.action_layout)
    action, next_recurrent_state = session.policy.predict(
        session.observation,
        recurrent_state=session.recurrent_state,
        episode_start=session.episode_start,
        deterministic=True,
    )
    action = np.asarray(action, dtype=float).reshape(-1, n_action)[0]

    observation, _reward, terminated, truncated, info = session.env.step(action)
    session.recurrent_state = next_recurrent_state
    session.episode_start[:] = False
    session.observation = observation
    session.sequence += 1
    session.done = bool(terminated or truncated)

    payload = _frame_payload(session, info)
    if session.done:
        session.env.close()
        del _SESSIONS[session_id]
    return payload
