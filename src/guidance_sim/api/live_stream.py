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

from dataclasses import dataclass, replace

import gymnasium as gym
import numpy as np

from guidance_sim.api.catalog import (
    CATALOG,
    get_live_parameters,
    resolve_live_parameters,
)
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
from guidance_sim.physics.entities import F16_6DOF, RigidBodyEntity, State
from guidance_sim.physics.maneuvers import (
    CobraManeuver,
    ConstantTurn,
    ManeuverProfile,
    NoManeuver,
    SinusoidalWeave,
)
from guidance_sim.rl.actions import (
    ACTION_LAYOUT_LATERAL2,
    action_dimension,
    world_to_lateral,
)
from guidance_sim.rl.environment import (
    InterceptionEnv,
    TrackingConfig,
    _default_pursuer_vehicle,
)
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
    "g-limited-turn": "constant_turn",
    "cobra-evasion": "cobra",
}
# The env's default target is a 40 kg drone; a Cobra needs a fighter-class
# 6-DOF airframe (F-16 mass/inertia/aero, with thrust vectoring for the hang).
_COBRA_TARGET_VEHICLE = F16_6DOF.vehicle
# Re-tuned for the 6-DOF airframe (see NOTES.md 2026-09-16). The old
# instant-rate shortcut's nose-snap dodged PN/APN/OGL at 0.9 s time-to-go.
# Raw range/closing-speed time-to-go is not monotonic in this tail chase as
# the unpowered interceptor bleeds speed. Use a deterministic 2 s cue so the
# finite-rate pitch-up is visible well before closest approach. Full thrust
# is used only through the pull; the maneuver returns to idle at the pitch
# target so it reaches an apex and falls instead of climbing forever.
_COBRA_TRIGGER_TIME_S = 2.0
_COBRA_PITCH_UP_THROTTLE = 1.0
# Scenarios that cap the interceptor's structural g below the env default.
_SCENARIO_PURSUER_G_LIMIT: dict[ScenarioId, float] = {
    s.id: s.pursuer_g_limit for s in CATALOG.scenarios if s.pursuer_g_limit is not None
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
    episode_reward: float


def _vec3(values: np.ndarray) -> Vector3:
    arr = np.asarray(values, dtype=float).reshape(3)
    return Vector3(x=float(arr[0]), y=float(arr[1]), z=float(arr[2]))


def _body(
    position: np.ndarray,
    velocity: np.ndarray,
    attitude: RigidBodyEntity | None = None,
) -> BodyState:
    return BodyState(
        position_m=_vec3(position),
        velocity_m_s=_vec3(velocity),
        body_axis=None if attitude is None else _vec3(attitude.body_axis()),
        body_up=None if attitude is None else _vec3(attitude.body_up()),
    )


def _initial_condition_sampler(params: dict[str, float]):
    """Geometry from the live controls; only a small launch heading error is random."""

    interceptor_speed_m_s = params["interceptor.speed"]
    target_speed_m_s = params["target.speed"]
    target_heading_rad = float(np.deg2rad(params["engagement.target_heading"]))

    def sample(rng: np.random.Generator) -> tuple[State, State]:
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
                position=[
                    params["engagement.initial_range"],
                    params["engagement.lateral_offset"],
                    3_000.0 + params["engagement.altitude_delta"],
                ],
                velocity=[
                    target_speed_m_s * np.cos(target_heading_rad),
                    target_speed_m_s * np.sin(target_heading_rad),
                    0.0,
                ],
            ),
        )

    return sample


def _maneuver_factory(kind: str, maneuver_g: float):
    def make(rng: np.random.Generator) -> ManeuverProfile:
        if kind in ("none", "cobra"):
            # Cobra needs the target entity, which the env builds after this
            # factory runs; build_live_trajectory swaps it in after reset.
            return NoManeuver()
        magnitude_m_s2 = maneuver_g * G0
        if kind == "constant_turn":
            turn_sign = -1.0 if float(rng.random()) < 0.5 else 1.0
            return ConstantTurn(accel=turn_sign * magnitude_m_s2)
        if kind == "weave":
            return SinusoidalWeave(
                amplitude=magnitude_m_s2,
                # a/omega^2 lateral swing: 0.5-1 Hz was ~5 m, i.e. invisible.
                frequency_hz=float(rng.uniform(0.1, 0.25)),
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
    maneuver = _SCENARIO_MANEUVER[scenario_id]

    policy = None
    use_turn_rate_obs = False
    action_layout = ACTION_LAYOUT_LATERAL2
    tracking = TrackingConfig()
    max_time_s = PPOTrainingConfig().max_time
    if guidance_law == "rl":
        from guidance_sim.ml.policy_inference import get_shared_policy

        policy = get_shared_policy()
        use_turn_rate_obs = policy.baseline.use_target_turn_rate_obs
        action_layout = policy.baseline.action_layout
        # Must match the baseline's own training-time obs contract exactly
        # (TrackingConfig(enabled=True)'s other fields are already the
        # lineage defaults evasive_redesign_config trained against) -- a
        # tracking-enabled baseline fed an env built with tracking off (or
        # vice versa) is a hard obs-shape crash, not a silent degradation.
        tracking = TrackingConfig(enabled=policy.baseline.tracking_enabled)
        # The evasive lineage trained on a 45s budget, not the frozen
        # lineage's 25s default -- serving it under the old default would
        # truncate genuine in-progress intercepts as spurious timeouts.
        # Classical guidance laws below are unaffected (max_time_s only
        # changes inside this `if guidance_law == "rl"` branch).
        max_time_s = policy.baseline.max_time_s

    config = replace(PPOTrainingConfig().simulation_config(), max_time=max_time_s)
    env = InterceptionEnv(
        config=config,
        initial_condition_sampler=_initial_condition_sampler(applied_parameters),
        maneuver_factory=_maneuver_factory(
            maneuver, applied_parameters["engagement.target_maneuver_g"]
        ),
        action_layout=action_layout,
        use_target_turn_rate_obs=use_turn_rate_obs,
        tracking=tracking,
        target_vehicle=_COBRA_TARGET_VEHICLE if maneuver == "cobra" else None,
        pursuer_vehicle=(
            replace(_default_pursuer_vehicle(), max_load_factor=g_limit)
            if (g_limit := _SCENARIO_PURSUER_G_LIMIT.get(scenario_id)) is not None
            else None
        ),
    )
    if seed is None:
        seed = int(np.random.SeedSequence().generate_state(1)[0])
    observation, info = env.reset(seed=seed)
    assert env.pursuer is not None and env.target is not None
    if maneuver == "cobra":
        # Same state, 6-DOF entity; env and obs untouched.
        env.target = RigidBodyEntity.from_state(env.target.state, F16_6DOF, name=env.target.name)
        env.target_maneuver = CobraManeuver(
            env.target,
            trigger_time_s=_COBRA_TRIGGER_TIME_S,
            hold_level_until_trigger=True,
            pitch_up_throttle=_COBRA_PITCH_UP_THROTTLE,
        )
    if policy is not None:
        # Same wrapper the policy was trained/evaluated behind.
        stepper = gym.wrappers.RescaleAction(
            env,
            min_action=np.full(action_dimension(action_layout), -1.0, dtype=np.float32),
            max_action=np.full(action_dimension(action_layout), 1.0, dtype=np.float32),
        )
        recurrent_state = None
        episode_start = np.array([True])
    else:
        stepper = env
        law = _guidance_law(guidance_law, env)

    frames: list[TrajectoryFrame] = [
        TrajectoryFrame(
            stream_id=stream_id,
            sequence=0,
            time_s=0.0,
            pursuer=_body(env.pursuer.state.position, env.pursuer.state.velocity),
            target=_body(
                    env.target.state.position,
                    env.target.state.velocity,
                    env.target if maneuver == "cobra" else None,
                ),
            range_m=float(info["range_m"]),
            pursuer_accel_cmd_m_s2=Vector3(x=0.0, y=0.0, z=0.0),
            pursuer_accel_achieved_m_s2=Vector3(x=0.0, y=0.0, z=0.0),
        )
    ]

    last_info: dict[str, object] = info
    episode_reward = 0.0
    while True:
        if policy is not None:
            action, recurrent_state = policy.predict(
                observation,
                recurrent_state=recurrent_state,
                episode_start=episode_start,
            )
            action = np.asarray(action, dtype=float).reshape(-1)
            episode_start[:] = False
        else:
            command = law.compute_command(
                env.pursuer.state, env.target.state, env.config.dt
            )
            action = world_to_lateral(command, env.pursuer.state.velocity)
        observation, reward, terminated, truncated, info = stepper.step(action)
        episode_reward += float(reward)
        last_info = info
        frames.append(
            TrajectoryFrame(
                stream_id=stream_id,
                sequence=len(frames),
                time_s=float(info["time_s"]),
                pursuer=_body(env.pursuer.state.position, env.pursuer.state.velocity),
                target=_body(
                    env.target.state.position,
                    env.target.state.velocity,
                    env.target if maneuver == "cobra" else None,
                ),
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
        closest_approach_m=float(last_info["closest_approach_m"]),
        applied_parameters=applied_parameters,
        scenario_id=scenario_id,
        maneuver=maneuver,
        outcome=str(last_info["outcome"]),
        episode_reward=episode_reward,
    )


# Monte Carlo spread applied around the operator's setup for trial overlays.
_TRIAL_JITTER = {
    "engagement.initial_range": 750.0,
    "engagement.lateral_offset": 500.0,
    "engagement.altitude_delta": 200.0,
    "engagement.target_heading": 10.0,
}
_TRIAL_FRAME_STRIDE = 5  # 0.1 s at dt=0.02: plenty for a polyline, 5x smaller payload


def build_rl_trials(
    scenario_id: ScenarioId,
    parameter_overrides: dict[str, float] | None,
    count: int,
    *,
    seed: int | None = None,
) -> list[dict[str, object]]:
    """Run ``count`` frozen-RL-policy episodes dispersed around the given setup."""

    controls = get_live_parameters()
    base = resolve_live_parameters(parameter_overrides or {})
    rng = np.random.default_rng(seed)
    trials: list[dict[str, object]] = []
    for episode in range(1, count + 1):
        overrides = dict(base)
        for name, spread in _TRIAL_JITTER.items():
            bounds = controls[name]
            overrides[name] = float(
                np.clip(
                    base[name] + rng.uniform(-spread, spread),
                    bounds.reference_min,
                    bounds.reference_max,
                )
            )
        run = build_live_trajectory(
            scenario_id,
            "rl",
            f"rl-trial-{episode}",
            overrides,
            seed=int(rng.integers(2**31)),
        )
        frames = run.frames[::_TRIAL_FRAME_STRIDE]
        if frames[-1] is not run.frames[-1]:
            frames.append(run.frames[-1])
        trials.append(
            {
                "episode": episode,
                "reward": run.episode_reward,
                "success": run.outcome == "hit",
                "outcome": "intercept" if run.outcome == "hit" else "miss",
                "closest_approach_m": run.closest_approach_m,
                "frames": [frame.model_dump(mode="json") for frame in frames],
            }
        )
    return trials
