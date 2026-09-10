"""Phase 2 checkpoint orchestration, scenario mix, and fixed evaluation."""

from __future__ import annotations

from dataclasses import asdict
import json

import numpy as np
import pytest

from guidance_sim.physics.maneuvers import (
    ConstantTurn,
    NoManeuver,
    SinusoidalWeave,
)
from guidance_sim.rl.training import (
    FIXED_EVALUATION_CASES,
    PPOTrainingConfig,
    evaluate_policy,
    make_training_vec_env,
    run_checkpoint,
    training_initial_conditions,
    training_maneuver_factory,
)
from guidance_sim.simulation.engine import SimulationConfig


class _ZeroRecurrentPolicy:
    def __init__(self) -> None:
        self.episode_starts: list[bool] = []

    def predict(
        self,
        observation,
        *,
        state=None,
        episode_start=None,
        deterministic=True,
    ):
        del observation, deterministic
        self.episode_starts.append(bool(episode_start[0]))
        return np.zeros(2, dtype=np.float32), state


def test_training_samplers_are_seeded_and_mix_all_required_profiles():
    rng_a = np.random.default_rng(77)
    rng_b = np.random.default_rng(77)
    states_a = training_initial_conditions(rng_a)
    states_b = training_initial_conditions(rng_b)
    for state_a, state_b in zip(states_a, states_b):
        np.testing.assert_array_equal(state_a.position, state_b.position)
        np.testing.assert_array_equal(state_a.velocity, state_b.velocity)

    profiles = [
        training_maneuver_factory(np.random.default_rng(seed))
        for seed in range(60)
    ]
    assert {type(profile) for profile in profiles} == {
        NoManeuver,
        ConstantTurn,
        SinusoidalWeave,
    }
    for profile in profiles:
        if isinstance(profile, ConstantTurn):
            assert 3.0 <= abs(profile.accel) / 9.80665 <= 7.0
        elif isinstance(profile, SinusoidalWeave):
            assert 3.0 <= profile.amplitude / 9.80665 <= 7.0
            assert 0.5 <= profile.frequency_hz <= 1.0


def test_fixed_evaluation_is_deterministic_and_resets_recurrent_state():
    config = SimulationConfig(
        dt=0.02,
        max_time=0.04,
        intercept_radius=5.0,
        autopilot_tau=0.2,
    )
    cases = FIXED_EVALUATION_CASES[:3]
    policy_a = _ZeroRecurrentPolicy()
    policy_b = _ZeroRecurrentPolicy()
    summary_a = evaluate_policy(policy_a, cases=cases, simulation_config=config)
    summary_b = evaluate_policy(policy_b, cases=cases, simulation_config=config)

    assert asdict(summary_a) == asdict(summary_b)
    assert summary_a.n_cases == 3
    assert summary_a.n_hits == 0
    assert summary_a.n_ground_impacts == 0
    assert summary_a.n_timeouts == 3
    for case in summary_a.cases:
        assert case.episode_reward == pytest.approx(
            case.progress_reward + case.effort_penalty + case.terminal_reward
        )
    assert summary_a.group_a.n_cases == 3
    assert summary_a.group_b.n_cases == 0
    assert sum(policy_a.episode_starts) == len(cases)
    assert all(
        not value
        for index, value in enumerate(policy_a.episode_starts)
        if index % 2 == 1
    )


def test_eval_groups_split_feasible_and_budget_constrained_cases():
    config = SimulationConfig(
        dt=0.02,
        max_time=0.04,
        intercept_radius=5.0,
        autopilot_tau=0.2,
    )
    summary = evaluate_policy(
        _ZeroRecurrentPolicy(),
        cases=FIXED_EVALUATION_CASES,
        simulation_config=config,
    )
    assert summary.group_a.n_cases == 6
    assert summary.group_b.n_cases == 3
    assert summary.group_a.n_cases + summary.group_b.n_cases == summary.n_cases
    assert {case.maneuver for case in summary.cases if case.maneuver != "constant_turn"} <= {
        "none",
        "weave",
    }


def test_ppo_action_wrapper_rescales_to_physical_limit_before_dynamics():
    config = PPOTrainingConfig(
        timesteps_per_checkpoint=4,
        n_envs=1,
        max_time=1.0,
        n_steps=4,
        batch_size=4,
        n_epochs=1,
    )
    vec_env = make_training_vec_env(config, checkpoint_index=1)
    try:
        np.testing.assert_array_equal(vec_env.action_space.low, -np.ones(2))
        np.testing.assert_array_equal(vec_env.action_space.high, np.ones(2))
        vec_env.reset()
        _, _, _, infos = vec_env.step(np.ones((1, 2), dtype=np.float32))
        commanded = np.asarray(infos[0]["action_commanded_m_s2"])
        assert commanded.shape == (3,)
        assert np.linalg.norm(commanded) == pytest.approx(25.0 * 9.80665)
    finally:
        vec_env.close()


def test_checkpoint_smoke_train_save_evaluate_and_refuse_overwrite(tmp_path):
    config = PPOTrainingConfig(
        timesteps_per_checkpoint=8,
        n_envs=1,
        dt=0.02,
        max_time=0.04,
        n_steps=4,
        batch_size=4,
        n_epochs=1,
        lstm_hidden_size=8,
    )
    report = run_checkpoint(1, output_dir=tmp_path, config=config)

    assert report.cumulative_timesteps == 8
    assert report.checkpoint_path.exists()
    assert report.episode_csv_path.exists()
    assert b"\r\n" not in report.episode_csv_path.read_bytes()
    assert report.curve_path.exists()
    assert report.evaluation_path.exists()
    assert report.progress_path.exists()
    assert report.curve.checkpoint_episodes == 4
    assert report.evaluation.n_cases == len(FIXED_EVALUATION_CASES)
    assert report.evaluation.mean_episode_reward == pytest.approx(
        report.evaluation.mean_progress_reward
        + report.evaluation.mean_effort_penalty
        + report.evaluation.mean_terminal_reward
    )
    assert not report.convergence_warning
    progress_text = report.progress_path.read_text(encoding="utf-8")
    assert "Checkpoint 1" in progress_text
    assert "mean control effort" in progress_text
    assert "ground impact/timeout/hit" in progress_text
    assert not progress_text.endswith("\n\n")
    metadata = json.loads(
        (tmp_path / "rl_checkpoint_01.json").read_text(encoding="utf-8")
    )
    assert len(metadata["observation_names"]) == 10

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        run_checkpoint(1, output_dir=tmp_path, config=config)
    with pytest.raises(FileNotFoundError, match="preceding checkpoint"):
        run_checkpoint(2, output_dir=tmp_path / "fresh", config=config)

    stale_dir = tmp_path / "stale"
    (stale_dir / "checkpoints").mkdir(parents=True)
    (stale_dir / "checkpoints" / "rl_checkpoint_01.zip").write_bytes(b"stale")
    (stale_dir / "rl_checkpoint_01.json").write_text(
        json.dumps({"observation_names": ["old_contract"]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="incompatible observation"):
        run_checkpoint(2, output_dir=stale_dir, config=config)


def test_training_budget_is_exactly_five_equal_checkpoints():
    config = PPOTrainingConfig()
    assert config.total_checkpoints == 5
    assert config.total_timesteps == 102_400
    assert config.timesteps_per_checkpoint * 5 == config.total_timesteps
    assert config.domain_randomization is False
    assert config.action_layout == "lateral2"

    with pytest.raises(ValueError, match="exactly five"):
        PPOTrainingConfig(total_checkpoints=4)
