"""CP0 validation for the delayed/estimated tracking chain in InterceptionEnv.

The spec's CP0 stop condition: with the sensor/estimator active the env must
produce a stable, non-NaN observation stream; the two new staleness/quality
channels must vary sensibly across an episode; and a guidance law that worked
fine under perfect truth must still intercept through the estimator (i.e. the
degraded state is honest, not broken).
"""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import ConstantTurn, NoManeuver
from guidance_sim.rl.actions import ACTION_LAYOUT_LATERAL2, world_to_lateral
from guidance_sim.rl.environment import (
    OBSERVATION_NAMES,
    STALENESS_SCALE,
    TRACKING_OBSERVATION_NAMES,
    InterceptionEnv,
    TrackingConfig,
)
from guidance_sim.simulation.engine import SimulationConfig

_SIM = SimulationConfig(dt=0.02, max_time=25.0, intercept_radius=5.0, autopilot_tau=0.2)


def _initial_conditions(lateral_offset_m: float = 400.0):
    def sample(_rng: np.random.Generator) -> tuple[State, State]:
        return (
            State(position=[0.0, 0.0, 3_000.0], velocity=[350.0, 0.0, 0.0]),
            State(
                position=[7_000.0, lateral_offset_m, 3_300.0],
                velocity=[-200.0, 0.0, 0.0],
            ),
        )

    return sample


def _tracked_env(maneuver=None, **tracking_kwargs) -> InterceptionEnv:
    factory = (lambda _rng: maneuver) if maneuver is not None else (lambda _rng: NoManeuver())
    return InterceptionEnv(
        config=_SIM,
        initial_condition_sampler=_initial_conditions(),
        maneuver_factory=factory,
        action_layout=ACTION_LAYOUT_LATERAL2,
        tracking=TrackingConfig(enabled=True, **tracking_kwargs),
    )


def _fly_pn(env: InterceptionEnv, seed: int = 0) -> dict[str, object]:
    """Run PN to termination against whatever target state the env exposes."""

    law = ProportionalNavigation(navigation_constant=4.0)
    env.reset(seed=seed)
    info: dict[str, object] = {}
    while True:
        assert env.pursuer is not None
        # PN consumes the same tracked (delayed/noisy) state the policy sees.
        observed_target = env._tracked_target_state()
        command = law.compute_command(env.pursuer.state, observed_target, env.config.dt)
        action = world_to_lateral(command, env.pursuer.state.velocity)
        _obs, _reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    return info


# --- Observation contract ---------------------------------------------------


def test_tracking_appends_two_channels_to_the_observation_contract():
    env = _tracked_env()

    assert env.observation_names == OBSERVATION_NAMES + TRACKING_OBSERVATION_NAMES
    assert env.observation_space.shape == (12,)


def test_legacy_contract_is_unchanged_when_tracking_is_off():
    env = InterceptionEnv(
        config=_SIM,
        initial_condition_sampler=_initial_conditions(),
        action_layout=ACTION_LAYOUT_LATERAL2,
    )

    assert env.observation_names == OBSERVATION_NAMES
    assert env.observation_space.shape == (10,)


def test_privileged_turn_rate_channel_cannot_coexist_with_tracking():
    with pytest.raises(ValueError, match="privileged ground-truth"):
        InterceptionEnv(
            config=_SIM,
            use_target_turn_rate_obs=True,
            tracking=TrackingConfig(enabled=True),
        )


def test_observation_stream_stays_finite_and_in_bounds_across_an_episode():
    env = _tracked_env(maneuver=ConstantTurn(accel=5.0 * G0))
    observation, _info = env.reset(seed=11)
    observations = [observation]
    for _ in range(400):
        action = np.zeros(2)
        observation, _reward, terminated, truncated, _info = env.step(action)
        observations.append(observation)
        if terminated or truncated:
            break

    stream = np.asarray(observations)
    assert np.all(np.isfinite(stream))
    assert np.all(stream >= env.observation_space.low - 1e-6)
    assert np.all(stream <= env.observation_space.high + 1e-6)


# --- The new staleness / uncertainty features -------------------------------


def test_staleness_and_uncertainty_vary_across_an_episode():
    env = _tracked_env(latency_range_s=(0.05, 0.05), update_rate_choices_hz=(25.0,))
    env.reset(seed=5)
    staleness: list[float] = []
    uncertainty: list[float] = []
    for _ in range(300):
        _obs, _reward, terminated, truncated, info = env.step(np.zeros(2))
        staleness.append(float(info["tracking_staleness"]))
        uncertainty.append(float(info["tracking_uncertainty"]))
        if terminated or truncated:
            break

    assert all(0.0 <= value <= 1.0 for value in staleness)
    assert all(0.0 <= value <= 1.0 for value in uncertainty)
    # Staleness must actually move: it sawtooths between seeker updates.
    assert np.std(staleness[10:]) > 0.0
    assert max(staleness[10:]) > min(staleness[10:])


def test_staleness_sawtooths_between_the_latency_floor_and_the_update_gap():
    """Age of information, not time since delivery.

    The policy's data is never fresher than the seeker latency, so staleness
    has a non-zero floor; between updates it climbs by the update gap and then
    drops back to that floor. It must oscillate in a bounded band rather than
    sitting at zero (no delay modelled) or ratcheting upward (lost track).
    """

    latency_s = 0.02
    update_rate_hz = 25.0
    env = _tracked_env(
        latency_range_s=(latency_s, latency_s),
        update_rate_choices_hz=(update_rate_hz,),
    )
    env.reset(seed=3)
    values: list[float] = []
    for _ in range(120):
        _obs, _reward, terminated, truncated, info = env.step(np.zeros(2))
        values.append(float(info["tracking_staleness"]))
        if terminated or truncated:
            break

    settled = values[20:]
    reference_s = max(latency_s, 1.0 / update_rate_hz)
    expected_floor = float(np.tanh(latency_s / (STALENESS_SCALE * reference_s)))
    expected_ceiling = float(
        np.tanh((latency_s + 1.0 / update_rate_hz) / (STALENESS_SCALE * reference_s))
    )

    assert min(settled) == pytest.approx(expected_floor, abs=1e-6)
    assert max(settled) <= expected_ceiling + 1e-6
    # It genuinely cycles rather than pinning to one end of the band.
    assert max(settled) > min(settled)


def test_episode_samples_its_own_latency_and_update_rate():
    env = _tracked_env()
    seen: set[tuple[float, float]] = set()
    for seed in range(12):
        env.reset(seed=seed)
        assert env._sensor_config is not None
        seen.add(
            (
                round(env._sensor_config.latency_s, 6),
                env._sensor_config.update_rate_hz,
            )
        )

    assert len(seen) > 1
    for latency_s, rate_hz in seen:
        assert 0.02 <= latency_s <= 0.08
        assert rate_hz in (25.0, 50.0)


# --- Truth vs. estimate separation ------------------------------------------


def test_policy_sees_a_degraded_state_while_metrics_stay_on_truth():
    env = _tracked_env()
    env.reset(seed=9)
    for _ in range(50):
        _obs, _reward, _terminated, _truncated, info = env.step(np.zeros(2))

    assert env.target is not None
    estimated = env._tracked_target_state()
    truth = env.target.state
    position_error_m = float(
        np.linalg.norm(estimated.position - truth.position)
    )

    # Delayed + noisy: the estimate must differ from truth...
    assert position_error_m > 0.0
    # ...but still track it closely enough to be usable, not diverge.
    assert position_error_m < 500.0
    # Reported range stays ground truth for metrics/plotting.
    assert float(info["range_m"]) == pytest.approx(
        float(np.linalg.norm(truth.position - env.pursuer.state.position))
    )
    assert info["observed_range_m"] != info["range_m"]


def test_hit_detection_uses_truth_not_the_estimate():
    """A lagging filter must not be able to fake an intercept."""

    env = _tracked_env()
    info = _fly_pn(env, seed=2)

    assert env.target is not None and env.pursuer is not None
    true_min_range_m = float(info["min_range_m"])
    if info["hit"]:
        assert true_min_range_m <= _SIM.intercept_radius


# --- CP0 gate: a working guidance law must survive the estimator ------------


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_pn_still_intercepts_a_non_maneuvering_target_through_the_estimator(seed):
    env = _tracked_env()
    info = _fly_pn(env, seed=seed)

    assert info["hit"], f"PN lost a NoManeuver intercept through the tracker: {info['outcome']}"


@pytest.mark.parametrize("turn_g", [3.0, 5.0])
def test_pn_tracking_degrades_constant_turn_miss_but_stays_bounded(turn_g):
    """Group B never converts inside 25 s; check the tracker does not make it
    catastrophically worse than the known perfect-truth plateau."""

    tracked = _tracked_env(maneuver=ConstantTurn(accel=turn_g * G0))
    perfect = InterceptionEnv(
        config=_SIM,
        initial_condition_sampler=_initial_conditions(),
        maneuver_factory=lambda _rng: ConstantTurn(accel=turn_g * G0),
        action_layout=ACTION_LAYOUT_LATERAL2,
    )

    tracked_info = _fly_pn(tracked, seed=4)
    perfect_info = _fly_pn(perfect, seed=4)

    tracked_miss_m = float(tracked_info["min_range_m"])
    perfect_miss_m = float(perfect_info["min_range_m"])
    assert np.isfinite(tracked_miss_m)
    # Tracking is allowed to hurt, but not by an order of magnitude -- that
    # would mean the estimator is broken, not merely imperfect.
    assert tracked_miss_m < max(10.0 * perfect_miss_m, 500.0)
