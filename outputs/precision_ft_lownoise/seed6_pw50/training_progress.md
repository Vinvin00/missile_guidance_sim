# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 31415926
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 171
- Episodes completed total: 171
- First/last quintile mean reward: 134.622400 / 94.821758
- Within-checkpoint reward change: -39.800642
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.360 / 3.805 m
- Fixed-eval mean episode reward: 124.903569
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.256513 / 107.446852
- Fixed-eval mean legacy episode reward: 106.907185
- Fixed-eval mean control effort: 904028.329893 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 181.140 / 77.823 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/8/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed6_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed6_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed6_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 335
- First/last quintile mean reward: 105.593408 / 132.812430
- Within-checkpoint reward change: +27.219022
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.796 / 3.473 m
- Fixed-eval mean episode reward: 137.138343
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.543385 / 116.968498
- Fixed-eval mean legacy episode reward: 122.606244
- Fixed-eval mean control effort: 798193.657022 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 176.835 / 72.828 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/7/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed6_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed6_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed6_pw50/training_curve.png`
