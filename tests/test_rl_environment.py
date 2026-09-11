"""Phase 1: Gymnasium environment contract, physics flow, and reward sanity."""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import SinusoidalWeave
from guidance_sim.rl.actions import world_to_lateral
from guidance_sim.rl.environment import (
    ALTITUDE_RATE_SCALE_M_S,
    ALTITUDE_SCALE_M,
    CLOSING_SPEED_SCALE_M_S,
    LOS_RATE_SCALE_RAD_S,
    OBSERVATION_NAMES,
    RANGE_SCALE_M,
    TARGET_TURN_RATE_SCALE_RAD_S,
    InterceptionEnv,
    compute_target_turn_rate_rad_s,
    observation_names,
)
from guidance_sim.simulation.engine import SimulationConfig


def _assert_observation_contract(
    env: InterceptionEnv,
    observation: np.ndarray,
) -> None:
    expected_dim = len(env.observation_names)
    assert observation.shape == (expected_dim,)
    assert observation.dtype == np.float32
    assert env.observation_space.contains(observation)
    assert np.all(np.isfinite(observation))
    assert env.observation_space.shape == (expected_dim,)


def _zero_action(env: InterceptionEnv) -> np.ndarray:
    return np.zeros(env.action_space.shape, dtype=np.float32)


def test_reset_and_step_match_gymnasium_contract():
    env = InterceptionEnv(
        config=SimulationConfig(dt=0.02, max_time=1.0, autopilot_tau=0.2)
    )

    observation, info = env.reset(seed=17)
    _assert_observation_contract(env, observation)
    assert env.action_space.shape == (2,)
    assert env.action_space.dtype == np.float32
    assert info["outcome"] == "ongoing"
    assert info["range_m"] > 0.0
    assert info["action_layout"] == "lateral2"
    assert OBSERVATION_NAMES == (
        "los_unit_x",
        "los_unit_y",
        "los_unit_z",
        "los_rate_x_scaled",
        "los_rate_y_scaled",
        "los_rate_z_scaled",
        "range_scaled",
        "closing_velocity_scaled",
        "height_above_ground_scaled",
        "altitude_rate_scaled",
    )
    expected = np.concatenate(
        (
            info["los_unit"],
            np.tanh(info["los_rate_rad_s"] / LOS_RATE_SCALE_RAD_S),
            [
                info["range_m"] / (info["range_m"] + RANGE_SCALE_M),
                np.tanh(
                    info["closing_velocity_m_s"] / CLOSING_SPEED_SCALE_M_S
                ),
                info["height_above_ground_m"]
                / (info["height_above_ground_m"] + ALTITUDE_SCALE_M),
                np.tanh(
                    info["altitude_rate_m_s"] / ALTITUDE_RATE_SCALE_M_S
                ),
            ],
        )
    ).astype(np.float32)
    np.testing.assert_array_equal(observation, expected)

    next_observation, reward, terminated, truncated, next_info = env.step(
        _zero_action(env)
    )
    _assert_observation_contract(env, next_observation)
    assert np.isfinite(reward)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert next_info["action_requested_m_s2"].shape == (2,)
    assert next_info["action_commanded_m_s2"].shape == (3,)
    assert next_info["action_achieved_m_s2"].shape == (3,)
    assert "legacy_reward" in next_info
    assert "legacy_episode_reward" in next_info


def test_action_flows_through_norm_bound_lag_and_dynamics_clamp():
    dt = 0.05
    tau = 0.2
    env = InterceptionEnv(
        config=SimulationConfig(dt=dt, max_time=1.0, autopilot_tau=tau)
    )
    observation, _ = env.reset(seed=1)
    _assert_observation_contract(env, observation)
    assert env.pursuer is not None
    velocity_at_issue = env.pursuer.state.velocity.copy()

    requested = env.action_space.high.astype(float)
    observation, _, terminated, truncated, info = env.step(requested)
    _assert_observation_contract(env, observation)
    commanded = info["action_commanded_m_s2"]
    achieved = info["action_achieved_m_s2"]

    assert not terminated and not truncated
    assert info["action_was_clipped"]
    assert np.linalg.norm(commanded) == pytest.approx(
        env.action_limit_m_s2, rel=1e-12
    )
    velocity_unit = velocity_at_issue / np.linalg.norm(velocity_at_issue)
    assert abs(float(np.dot(commanded, velocity_unit))) < 1e-7
    assert np.linalg.norm(achieved) < np.linalg.norm(commanded)
    assert np.linalg.norm(achieved) <= env.action_limit_m_s2 + 1e-9
    assert abs(float(np.dot(velocity_at_issue, achieved))) < 1e-7
    lag_fraction = 1.0 - np.exp(-dt / tau)
    expected_achieved = lag_fraction * commanded
    np.testing.assert_allclose(achieved, expected_achieved, rtol=1e-10, atol=1e-10)
    expected_effort = (
        -env.reward_config.effort_weight
        * dt
        * (float(np.linalg.norm(achieved)) / env.action_limit_m_s2) ** 2
    )
    assert info["reward_terms"]["effort"] == pytest.approx(expected_effort)


def _rollout(
    env: InterceptionEnv,
    policy,
) -> tuple[float, str, float]:
    observation, info = env.reset(seed=123)
    _assert_observation_contract(env, observation)
    total_reward = 0.0
    while True:
        action = policy(env, info)
        observation, reward, terminated, truncated, info = env.step(action)
        _assert_observation_contract(env, observation)
        total_reward += reward
        if terminated or truncated:
            return total_reward, str(info["outcome"]), float(info["min_range_m"])


def test_direct_intercept_scores_above_wandering_wasteful_control():
    config = SimulationConfig(
        dt=0.02,
        max_time=45.0,
        intercept_radius=5.0,
        autopilot_tau=0.2,
    )

    def pn_policy(env: InterceptionEnv, info: dict[str, object]) -> np.ndarray:
        world = (
            4.0
            * float(info["closing_velocity_m_s"])
            * np.cross(info["los_rate_rad_s"], info["los_unit"])
        )
        assert env.pursuer is not None
        return world_to_lateral(world, env.pursuer.state.velocity)

    def wandering_policy(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
        return np.array([env.action_limit_m_s2, 0.0])

    direct = _rollout(InterceptionEnv(config=config), pn_policy)
    wandering = _rollout(InterceptionEnv(config=config), wandering_policy)

    assert direct[1] == "hit"
    assert direct[0] > wandering[0] + 50.0, (
        f"direct={direct}, wandering={wandering}"
    )


def _near_hit_sampler(_rng: np.random.Generator) -> tuple[State, State]:
    return (
        State(position=[0.0, 0.0, 1000.0], velocity=[30.0, 0.0, 0.0]),
        State(position=[10.0, 0.0, 1000.0], velocity=[-30.0, 0.0, 0.0]),
    )


def test_hit_is_terminated_not_truncated():
    env = InterceptionEnv(
        config=SimulationConfig(
            dt=0.1,
            max_time=1.0,
            intercept_radius=5.0,
            autopilot_tau=0.0,
        ),
        initial_condition_sampler=_near_hit_sampler,
    )
    env.reset(seed=0)
    observation, reward, terminated, truncated, info = env.step(_zero_action(env))
    _assert_observation_contract(env, observation)

    assert terminated
    assert not truncated
    assert info["outcome"] == "hit"
    assert info["termination_reason"] == "intercept"
    assert info["reward_terms"]["terminal"] == pytest.approx(100.0)
    assert reward > 50.0
    assert info["legacy_reward"] == pytest.approx(
        info["reward_terms"]["legacy_total"]
    )


def _ground_miss_sampler(_rng: np.random.Generator) -> tuple[State, State]:
    return (
        State(position=[0.0, 0.0, 0.2], velocity=[100.0, 0.0, -10.0]),
        State(position=[1000.0, 0.0, 100.0], velocity=[0.0, 0.0, 0.0]),
    )


def _timeout_sampler(_rng: np.random.Generator) -> tuple[State, State]:
    return (
        State(position=[0.0, 0.0, 1000.0], velocity=[100.0, 0.0, 0.0]),
        State(position=[1000.0, 0.0, 1000.0], velocity=[100.0, 0.0, 0.0]),
    )


def test_ground_impact_is_physical_miss_and_timeout_is_truncation():
    miss_env = InterceptionEnv(
        config=SimulationConfig(dt=0.05, max_time=1.0, autopilot_tau=0.0),
        initial_condition_sampler=_ground_miss_sampler,
    )
    miss_env.reset(seed=0)
    observation, _, terminated, truncated, info = miss_env.step(_zero_action(miss_env))
    _assert_observation_contract(miss_env, observation)
    assert terminated and not truncated
    assert info["outcome"] == "miss"
    assert info["termination_reason"] == "pursuer_ground_impact"
    expected_terminal = -100.0 * np.tanh(
        float(info["min_range_m"]) / miss_env.reward_config.miss_tanh_scale_m
    )
    assert info["reward_terms"]["terminal"] == pytest.approx(expected_terminal)
    assert info["reward_terms"]["legacy_terminal"] == pytest.approx(-100.0)
    assert observation[-2] == pytest.approx(0.0)
    assert info["height_above_ground_m"] <= 0.0

    timeout_env = InterceptionEnv(
        config=SimulationConfig(dt=0.1, max_time=0.2, autopilot_tau=0.0),
        initial_condition_sampler=_timeout_sampler,
    )
    observation, _ = timeout_env.reset(seed=0)
    _assert_observation_contract(timeout_env, observation)
    observation, _, terminated, truncated, _ = timeout_env.step(_zero_action(timeout_env))
    _assert_observation_contract(timeout_env, observation)
    assert not terminated and not truncated
    observation, _, terminated, truncated, info = timeout_env.step(
        _zero_action(timeout_env)
    )
    _assert_observation_contract(timeout_env, observation)
    assert not terminated and truncated
    assert info["outcome"] == "timeout"
    assert info["termination_reason"] == "time_limit"
    expected_timeout = -100.0 * np.tanh(
        float(info["min_range_m"]) / timeout_env.reward_config.miss_tanh_scale_m
    )
    assert info["reward_terms"]["terminal"] == pytest.approx(expected_timeout)
    assert info["reward_terms"]["legacy_terminal"] == pytest.approx(-100.0)


def test_seeded_reset_is_deterministic_and_constructs_fresh_episode_objects():
    def seeded_sampler(rng: np.random.Generator) -> tuple[State, State]:
        offset = float(rng.uniform(-500.0, 500.0))
        return (
            State(
                position=[0.0, 0.0, 3000.0],
                velocity=[350.0, 0.0, 0.0],
            ),
            State(
                position=[7000.0, offset, 3300.0],
                velocity=[-200.0, 0.0, 0.0],
            ),
        )

    def seeded_maneuver(rng: np.random.Generator) -> SinusoidalWeave:
        return SinusoidalWeave(
            amplitude=30.0,
            frequency_hz=0.5,
            phase=float(rng.uniform(0.0, 2.0 * np.pi)),
        )

    env = InterceptionEnv(
        initial_condition_sampler=seeded_sampler,
        maneuver_factory=seeded_maneuver,
    )
    observation_a, _ = env.reset(seed=99)
    _assert_observation_contract(env, observation_a)
    pursuer_a = env.pursuer
    target_a = env.target
    maneuver_a = env.target_maneuver
    env.step(np.array([0.0, 20.0]))

    observation_b, _ = env.reset(seed=99)
    _assert_observation_contract(env, observation_b)
    np.testing.assert_array_equal(observation_a, observation_b)
    assert env.pursuer is not pursuer_a
    assert env.target is not target_a
    assert env.target_maneuver is not maneuver_a
    assert np.allclose(env.pursuer.last_achieved_lateral_accel, 0.0)

    observation_c, _ = env.reset(seed=100)
    _assert_observation_contract(env, observation_c)
    assert not np.array_equal(observation_b, observation_c)


def test_target_turn_rate_matches_circular_turn_hand_check():
    """omega = cross(v, a) / |v|^2; |omega| = |a|/|v| for pure lateral a."""

    speed = 200.0
    accel = 3.0 * 9.80665  # 3 g lateral
    velocity = np.array([speed, 0.0, 0.0])
    lateral = np.array([0.0, accel, 0.0])
    omega = compute_target_turn_rate_rad_s(velocity, lateral)

    expected = np.array([0.0, 0.0, accel / speed])
    np.testing.assert_allclose(omega, expected, rtol=0.0, atol=1e-12)
    assert float(np.linalg.norm(omega)) == pytest.approx(accel / speed)
    # Along-track accel contributes nothing.
    np.testing.assert_allclose(
        compute_target_turn_rate_rad_s(velocity, np.array([accel, 0.0, 0.0])),
        np.zeros(3),
        atol=1e-12,
    )
    np.testing.assert_array_equal(
        compute_target_turn_rate_rad_s(np.zeros(3), lateral),
        np.zeros(3),
    )


def test_use_target_turn_rate_obs_appends_scaled_channels_and_zero_fallback():
    from guidance_sim.physics.atmosphere import G0
    from guidance_sim.physics.maneuvers import ConstantTurn

    assert observation_names(use_target_turn_rate_obs=False) == OBSERVATION_NAMES
    assert len(observation_names(use_target_turn_rate_obs=True)) == 13

    def turn_factory(_rng: np.random.Generator) -> ConstantTurn:
        return ConstantTurn(accel=3.0 * G0)

    env = InterceptionEnv(
        config=SimulationConfig(dt=0.02, max_time=1.0, autopilot_tau=0.0),
        maneuver_factory=turn_factory,
        use_target_turn_rate_obs=True,
    )
    observation, info = env.reset(seed=3)
    _assert_observation_contract(env, observation)
    assert observation.shape == (13,)
    # Decision point: pre-step achieved accel is zero → turn-rate channels zero.
    np.testing.assert_array_equal(observation[-3:], np.zeros(3, dtype=np.float32))
    np.testing.assert_allclose(info["target_turn_rate_rad_s"], 0.0)

    observation, _, _, _, info = env.step(_zero_action(env))
    _assert_observation_contract(env, observation)
    expected_omega = compute_target_turn_rate_rad_s(
        env.target.state.velocity,
        env.target.last_achieved_lateral_accel,
    )
    np.testing.assert_allclose(info["target_turn_rate_rad_s"], expected_omega)
    np.testing.assert_allclose(
        observation[-3:],
        np.tanh(expected_omega / TARGET_TURN_RATE_SCALE_RAD_S).astype(np.float32),
    )
    # Sustained turn: |omega| = |a_perp| / |v| (along-track residual ignored).
    speed = float(np.linalg.norm(env.target.state.velocity))
    a_vec = env.target.last_achieved_lateral_accel
    a_lat = float(np.linalg.norm(a_vec))
    assert a_lat > 1.0
    v_hat = env.target.state.velocity / speed
    a_perp = float(np.linalg.norm(a_vec - np.dot(a_vec, v_hat) * v_hat))
    assert float(np.linalg.norm(expected_omega)) == pytest.approx(
        a_perp / speed, rel=1e-9, abs=1e-12
    )

    # Default flag off keeps the frozen 10-D contract.
    default_env = InterceptionEnv(
        config=SimulationConfig(dt=0.02, max_time=1.0, autopilot_tau=0.0)
    )
    obs_default, _ = default_env.reset(seed=3)
    assert obs_default.shape == (10,)
    assert default_env.use_target_turn_rate_obs is False
