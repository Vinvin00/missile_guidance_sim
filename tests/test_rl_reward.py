"""New-reward properties: closest-approach terminal, hit vs miss, flyby vs loiter."""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.rl.actions import world_to_lateral
from guidance_sim.rl.environment import InterceptionEnv
from guidance_sim.rl.reward import RewardConfig, compute_reward
from guidance_sim.simulation.engine import SimulationConfig


def _rollout(env: InterceptionEnv, policy, seed: int = 0) -> dict[str, float | str]:
    _, info = env.reset(seed=seed)
    total = 0.0
    shaping = 0.0
    effort = 0.0
    terminal = 0.0
    while True:
        action = policy(env, info)
        _, reward, terminated, truncated, info = env.step(action)
        total += float(reward)
        shaping += float(info["reward_terms"]["shaping"])
        effort += float(info["reward_terms"]["effort"])
        terminal += float(info["reward_terms"]["terminal"])
        if terminated or truncated:
            return {
                "total": total,
                "shaping": shaping,
                "effort": effort,
                "terminal": terminal,
                "outcome": str(info["outcome"]),
                "min_range_m": float(info["min_range_m"]),
                "final_range_m": float(info["range_m"]),
                "legacy_episode_reward": float(info["legacy_episode_reward"]),
            }


def _pn_policy(env: InterceptionEnv, info: dict[str, object]) -> np.ndarray:
    world = (
        4.0
        * float(info["closing_velocity_m_s"])
        * np.cross(info["los_rate_rad_s"], info["los_unit"])
    )
    assert env.pursuer is not None
    return world_to_lateral(world, env.pursuer.state.velocity)


def _zero_policy(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
    return np.zeros(env.action_space.shape, dtype=float)


def _turn_away_policy(env: InterceptionEnv, _info: dict[str, object]) -> np.ndarray:
    assert env.pursuer is not None and env.target is not None
    los = env.target.state.position - env.pursuer.state.position
    lateral = world_to_lateral(los, env.pursuer.state.velocity)
    norm = float(np.linalg.norm(lateral))
    if norm < 1e-9:
        return np.array([env.action_limit_m_s2, 0.0])
    return (-lateral / norm) * env.action_limit_m_s2


def test_pn_intercept_scores_above_pn_miss():
    hit_config = SimulationConfig(dt=0.02, max_time=45.0, intercept_radius=5.0)
    miss_config = SimulationConfig(dt=0.02, max_time=2.0, intercept_radius=5.0)
    hit = _rollout(InterceptionEnv(config=hit_config), _pn_policy)
    miss = _rollout(InterceptionEnv(config=miss_config), _pn_policy)
    assert hit["outcome"] == "hit"
    assert miss["outcome"] in ("timeout", "miss")
    assert hit["total"] > miss["total"] + 40.0, f"hit={hit} miss={miss}"


def test_close_then_flyby_scores_above_same_ic_loitering():
    config = SimulationConfig(dt=0.02, max_time=25.0, intercept_radius=5.0)
    flyby = _rollout(InterceptionEnv(config=config), _zero_policy, seed=1)
    loiter = _rollout(InterceptionEnv(config=config), _turn_away_policy, seed=1)
    assert flyby["outcome"] != "hit"
    assert loiter["outcome"] != "hit"
    assert flyby["min_range_m"] < loiter["min_range_m"]
    assert flyby["total"] > loiter["total"] + 10.0, f"flyby={flyby} loiter={loiter}"


def test_miss_terminal_uses_closest_approach_not_final_range():
    env = InterceptionEnv(
        config=SimulationConfig(dt=0.02, max_time=25.0, intercept_radius=5.0)
    )
    result = _rollout(env, _zero_policy, seed=2)
    assert result["final_range_m"] > result["min_range_m"] + 100.0
    expected = -100.0 * np.tanh(result["min_range_m"] / 1_000.0)
    not_final = -100.0 * np.tanh(result["final_range_m"] / 1_000.0)
    assert result["terminal"] == pytest.approx(expected, rel=1e-6)
    assert abs(result["terminal"] - not_final) > 1.0


def _base_reward_kwargs() -> dict[str, object]:
    return dict(
        previous_potential=0.0,
        zem_m=100.0,
        previous_range_m=1_000.0,
        current_range_m=990.0,
        min_range_m=990.0,
        achieved_lateral_m_s2=np.zeros(3),
        legacy_commanded_m_s2=np.array([50.0, 0.0, 0.0]),
        action_limit_m_s2=100.0,
        dt=0.02,
        outcome="ongoing",
    )


def test_effort_rate_weight_zero_ignores_commanded_jitter():
    """Default (0) must not price the commanded-accel step at all -- other
    callers assume effort_rate_weight=0 leaves the reward bit-identical to
    before this term existed."""

    kwargs = _base_reward_kwargs()
    config = RewardConfig()
    with_jump = compute_reward(
        **kwargs, config=config, previous_commanded_m_s2=np.array([-50.0, 0.0, 0.0])
    )
    no_previous = compute_reward(**kwargs, config=config, previous_commanded_m_s2=None)
    assert with_jump.effort == no_previous.effort


def test_effort_rate_weight_penalises_commanded_jitter_beyond_achieved_effort():
    """A policy that jitters the commanded accel every step costs more than
    one that holds it steady, even at equal achieved (post-lag) accel --
    the whole point of pricing the commanded *rate*, not just the achieved
    magnitude (docs/rl-interface-6dof.md, effort profile)."""

    kwargs = _base_reward_kwargs()
    config = RewardConfig(effort_rate_weight=1.0)

    steady = compute_reward(
        **kwargs, config=config, previous_commanded_m_s2=np.array([50.0, 0.0, 0.0])
    )
    jittering = compute_reward(
        **kwargs, config=config, previous_commanded_m_s2=np.array([-50.0, 0.0, 0.0])
    )
    assert jittering.effort < steady.effort
    expected_gap = -1.0 * kwargs["dt"] * (100.0 / kwargs["action_limit_m_s2"]) ** 2
    assert jittering.effort - steady.effort == pytest.approx(expected_gap, rel=1e-9)


def test_precision_bonus_uses_substep_closest_approach():
    config = SimulationConfig(dt=0.02, max_time=45.0, intercept_radius=5.0)
    plain = _rollout(InterceptionEnv(config=config), _pn_policy)
    env = InterceptionEnv(
        config=config,
        reward_config=RewardConfig(precision_weight=50.0, precision_scale_m=5.0),
    )
    precise = _rollout(env, _pn_policy)
    cpa = env.closest_approach_m
    assert precise["outcome"] == plain["outcome"] == "hit"
    # Sub-step CPA can only tighten the step-sampled minimum range.
    assert 0.0 <= cpa <= precise["min_range_m"] + 1e-9
    assert precise["terminal"] - plain["terminal"] == pytest.approx(
        50.0 * np.exp(-cpa / 5.0), rel=1e-6
    )
