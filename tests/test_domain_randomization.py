"""Domain randomization is implemented but gated off by default."""

from __future__ import annotations

import numpy as np

from guidance_sim.physics.maneuvers import ConstantTurn, NoManeuver, SinusoidalWeave
from guidance_sim.rl.domain_randomization import (
    randomized_initial_conditions,
    randomized_maneuver_factory,
)
from guidance_sim.rl.training import (
    PPOTrainingConfig,
    make_training_vec_env,
    training_initial_conditions,
    training_maneuver_factory,
)


def test_default_training_uses_frozen_distribution_not_randomized():
    config = PPOTrainingConfig(timesteps_per_checkpoint=4, n_envs=1, n_steps=4, batch_size=4)
    assert config.domain_randomization is False
    rng_a = np.random.default_rng(11)
    rng_b = np.random.default_rng(11)
    frozen = training_initial_conditions(rng_a)
    again = training_initial_conditions(rng_b)
    np.testing.assert_array_equal(frozen[0].position, again[0].position)
    np.testing.assert_array_equal(frozen[1].velocity, again[1].velocity)

    vec_env = make_training_vec_env(config, checkpoint_index=1)
    try:
        assert vec_env.action_space.shape == (2,)
    finally:
        vec_env.close()


def test_randomized_samplers_draw_outside_frozen_ranges():
    speeds = []
    offsets = []
    for seed in range(80):
        _, target = randomized_initial_conditions(np.random.default_rng(seed))
        speeds.append(float(np.linalg.norm(target.velocity)))
        offsets.append(abs(float(target.position[1])))
    assert min(speeds) < 180.0 or max(speeds) > 220.0
    assert max(offsets) > 800.0

    weave_hz = []
    turn_g = []
    types = set()
    for seed in range(90):
        profile = randomized_maneuver_factory(np.random.default_rng(seed + 1_000))
        types.add(type(profile))
        if isinstance(profile, SinusoidalWeave):
            weave_hz.append(profile.frequency_hz)
        elif isinstance(profile, ConstantTurn):
            turn_g.append(abs(profile.accel) / 9.80665)
    assert types == {NoManeuver, ConstantTurn, SinusoidalWeave}
    assert min(weave_hz) < 0.5 or max(weave_hz) > 1.0
    assert min(turn_g) < 3.0 or max(turn_g) > 7.0
