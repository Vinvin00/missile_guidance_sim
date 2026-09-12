"""Live classical-guidance trajectories for the visualization WebSocket.

Replaces ``rollout_stream.py`` (which replayed one of two frozen, captured
RL-rollout files regardless of which scenario or guidance law the client
picked) as the ``/ws/trajectory`` data source. Every stream request here
runs a fresh ``InterceptionEnv`` episode: the selected scenario picks the
target's maneuver family, the selected guidance law (PN/APN/OGL) actually
drives the interceptor, and live speed overrides reshape the initial
conditions instead of being validated and echoed only. Unless a caller
pins ``seed``, each call draws a fresh one, so replaying the same scenario
twice gives two different concrete engagements rather than the same
recording.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from guidance_sim.api.catalog import resolve_live_parameters
from guidance_sim.api.schemas import (
    BodyState,
    GuidanceLawId,
    ScenarioId,
    TrajectoryFrame,
    Vector3,
)
from guidance_sim.guidance.augmented_pn import AugmentedProportionalNavigation
from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.optimal_guidance import OptimalGuidance
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import (
    ConstantTurn,
    ManeuverProfile,
    NoManeuver,
    SinusoidalWeave,
)
from guidance_sim.rl.actions import ACTION_LAYOUT_LATERAL2, world_to_lateral
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.training import PPOTrainingConfig

_PN_N = 4.0
_APN_N = 4.0
_OGL_N = 3.0

# Catalog scenario id -> target maneuver family. Each family is sampled with
# randomized magnitude/direction/phase per episode (see `_maneuver_factory`),
# not a single fixed instance, so "the same scenario" still varies run to run.
_SCENARIO_MANEUVER: dict[ScenarioId, str] = {
    "crossing-intercept": "none",
    "head-on-intercept": "constant_turn",
    "evasive-climb": "weave",
}


@dataclass(frozen=True)
class LiveTrajectory:
    dt_s: float
    frames: list[TrajectoryFrame]
    closest_approach_m: float
    applied_parameters: dict[str, float]
    scenario_id: ScenarioId
    maneuver: str
    outcome: str


def _vec3(values: np.ndarray) -> Vector3:
    arr = np.asarray(values, dtype=float).reshape(3)
    return Vector3(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))


def _body(position: np.ndarray, velocity: np.ndarray) -> BodyState:
    return BodyState(position_m=_vec3(position), velocity_m_s=_vec3(velocity))


def _initial_condition_sampler(interceptor_speed_m_s: float, target_speed_m_s: float):
    """Randomized geometry around the demo envelope, at the live-controlled speeds."""

    def sample(rng: np.random.Generator) -> tuple[State, State]:
        target_range_m = float(rng.uniform(6_000.0, 8_000.0))
        lateral_offset_m = float(rng.uniform(-800.0, 800.0))
        target_altitude_m = float(rng.uniform(3_100.0, 3_500.0))
        heading_error_rad = float(np.deg2rad(rng.uniform(-2.0, 2.0)))
        return (
            State(
                position=[0.0, 0.0, 3_000.0],
                velocity=[
                    interceptor_speed_m_s * np.cos(heading_error_rad),
                    interceptor_speed_m_s * np.sin(heading_error_rad),
                    0.0,
                ],
            ),
            State(
                position=[target_range_m, lateral_offset_m, target_altitude_m],
                velocity=[-target_speed_m_s, 0.0, 0.0],
            ),
        )

    return sample


def _maneuver_factory(kind: str):
    def make(rng: np.random.Generator) -> ManeuverProfile:
        if kind == "none":
            return NoManeuver()
        magnitude_m_s2 = float(rng.uniform(3.0, 7.0) * G0)
        if kind == "constant_turn":
            turn_sign = -1.0 if float(rng.random()) < 0.5 else 1.0
            return ConstantTurn(accel=turn_sign * magnitude_m_s2)
        if kind == "weave":
            return SinusoidalWeave(
                amplitude=magnitude_m_s2,
                frequency_hz=float(rng.uniform(0.5, 1.0)),
                phase=float(rng.uniform(0.0, 2.0 * np.pi)),
            )
        raise ValueError(f"unsupported maneuver kind: {kind!r}")

    return make


def _guidance_law(guidance_law: GuidanceLawId, env: InterceptionEnv) -> GuidanceLaw:
    if guidance_law == "pn":
        return ProportionalNavigation(navigation_constant=_PN_N)
    if guidance_law == "apn":
        return AugmentedProportionalNavigation(
            navigation_constant=_APN_N,
            a_target_est=lambda: env.target.last_achieved_lateral_accel.copy(),
        )
    if guidance_law == "ogl":
        return OptimalGuidance(
            navigation_constant=_OGL_N,
            a_target_est=lambda: env.target.last_achieved_lateral_accel.copy(),
        )
    raise ValueError(f"unsupported guidance_law: {guidance_law!r}")


def build_live_trajectory(
    scenario_id: ScenarioId,
    guidance_law: GuidanceLawId,
    stream_id: str,
    parameter_overrides: dict[str, float] | None = None,
    *,
    seed: int | None = None,
) -> LiveTrajectory:
    """Run one fresh live engagement for the requested scenario/guidance law.

    ``seed`` is exposed for reproducible tests; the WebSocket handler leaves
    it unset so production streams draw a new one each request.
    """

    applied_parameters = resolve_live_parameters(parameter_overrides or {})
    interceptor_speed_m_s = applied_parameters["interceptor.speed"]
    target_speed_m_s = applied_parameters["target.speed"]
    maneuver = _SCENARIO_MANEUVER[scenario_id]

    config = PPOTrainingConfig().simulation_config()
    env = InterceptionEnv(
        config=config,
        initial_condition_sampler=_initial_condition_sampler(
            interceptor_speed_m_s, target_speed_m_s
        ),
        maneuver_factory=_maneuver_factory(maneuver),
        action_layout=ACTION_LAYOUT_LATERAL2,
        use_target_turn_rate_obs=False,
    )
    if seed is None:
        seed = int(np.random.SeedSequence().generate_state(1)[0])
    _observation, info = env.reset(seed=seed)
    assert env.pursuer is not None and env.target is not None
    law = _guidance_law(guidance_law, env)

    frames: list[TrajectoryFrame] = [
        TrajectoryFrame(
            stream_id=stream_id,
            sequence=0,
            time_s=0.0,
            pursuer=_body(env.pursuer.state.position, env.pursuer.state.velocity),
            target=_body(env.target.state.position, env.target.state.velocity),
            range_m=float(info["range_m"]),
            pursuer_accel_cmd_m_s2=Vector3(x=0.0, y=0.0, z=0.0),
            pursuer_accel_achieved_m_s2=Vector3(x=0.0, y=0.0, z=0.0),
        )
    ]

    last_info: dict[str, object] = info
    while True:
        command = law.compute_command(
            env.pursuer.state, env.target.state, env.config.dt
        )
        action = world_to_lateral(command, env.pursuer.state.velocity)
        _observation, _reward, terminated, truncated, info = env.step(action)
        last_info = info
        frames.append(
            TrajectoryFrame(
                stream_id=stream_id,
                sequence=len(frames),
                time_s=float(info["time_s"]),
                pursuer=_body(env.pursuer.state.position, env.pursuer.state.velocity),
                target=_body(env.target.state.position, env.target.state.velocity),
                range_m=float(info["range_m"]),
                pursuer_accel_cmd_m_s2=_vec3(info["action_commanded_m_s2"]),
                pursuer_accel_achieved_m_s2=_vec3(info["action_achieved_m_s2"]),
            )
        )
        if terminated or truncated:
            break

    # Match SimulationResult intercept convention: no command after hit.
    if bool(last_info.get("hit")):
        frames[-1] = frames[-1].model_copy(
            update={
                "pursuer_accel_cmd_m_s2": Vector3(x=0.0, y=0.0, z=0.0),
                "pursuer_accel_achieved_m_s2": Vector3(x=0.0, y=0.0, z=0.0),
            }
        )

    env.close()
    return LiveTrajectory(
        dt_s=float(config.dt),
        frames=frames,
        closest_approach_m=float(last_info["min_range_m"]),
        applied_parameters=applied_parameters,
        scenario_id=scenario_id,
        maneuver=maneuver,
        outcome=str(last_info["outcome"]),
    )
