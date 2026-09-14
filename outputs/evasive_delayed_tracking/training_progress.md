# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 96
- Episodes completed total: 96
- First/last quintile mean reward: -25.772617 / -9.195227
- Within-checkpoint reward change: +16.577390
- Fixed-eval hit rate: 13/50 (26.0%)
- Fixed-eval mean/median miss distance: 140.984 / 22.861 m
- Fixed-eval mean episode reward: 46.347330
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -2.145945 / 21.378676
- Fixed-eval mean legacy episode reward: -5.639473
- Fixed-eval mean control effort: 40124.548306 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 30.509 / 24.524 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 24/13/13
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_01_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 106
- Episodes completed total: 202
- First/last quintile mean reward: 12.650071 / 37.641785
- Within-checkpoint reward change: +24.991715
- Fixed-eval hit rate: 10/50 (20.0%)
- Fixed-eval mean/median miss distance: 14.953 / 9.965 m
- Fixed-eval mean episode reward: 33.554237
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -13.087241 / 19.526880
- Fixed-eval mean legacy episode reward: -16.829046
- Fixed-eval mean control effort: 369947.779945 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 93.187 / 61.819 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 28/12/10
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_02_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 117
- Episodes completed total: 319
- First/last quintile mean reward: 30.747297 / 49.254601
- Within-checkpoint reward change: +18.507304
- Fixed-eval hit rate: 18/50 (36.0%)
- Fixed-eval mean/median miss distance: 7.582 / 6.051 m
- Fixed-eval mean episode reward: 49.159300
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -13.746448 / 35.791150
- Fixed-eval mean legacy episode reward: 21.704273
- Fixed-eval mean control effort: 442294.494936 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 100.669 / 60.947 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 13/19/18
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_03_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 113
- Episodes completed total: 432
- First/last quintile mean reward: 43.223500 / 26.606068
- Within-checkpoint reward change: -16.617432
- Fixed-eval hit rate: 6/50 (12.0%)
- Fixed-eval mean/median miss distance: 9.561 / 9.693 m
- Fixed-eval mean episode reward: 8.030404
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -30.780641 / 11.696447
- Fixed-eval mean legacy episode reward: -48.515413
- Fixed-eval mean control effort: 1415186.646873 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 187.674 / 94.223 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 24/20/6
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_04_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 111
- Episodes completed total: 543
- First/last quintile mean reward: 26.731313 / 18.099324
- Within-checkpoint reward change: -8.631989
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 9.620 / 8.412 m
- Fixed-eval mean episode reward: 3.140152
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -41.675106 / 17.700660
- Fixed-eval mean legacy episode reward: -42.870447
- Fixed-eval mean control effort: 1857816.300547 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 220.040 / 113.595 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 17/24/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_05_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`
