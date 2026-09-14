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
- Episodes completed this checkpoint: 103
- Episodes completed total: 103
- First/last quintile mean reward: -4.818969 / 31.536843
- Within-checkpoint reward change: +36.355813
- Fixed-eval hit rate: 11/50 (22.0%)
- Fixed-eval mean/median miss distance: 11.278 / 8.955 m
- Fixed-eval mean episode reward: 28.869608
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -29.501137 / 21.657515
- Fixed-eval mean legacy episode reward: -6.380642
- Fixed-eval mean control effort: 389203.755782 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 93.362 / 70.873 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 18/21/11
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_effort8/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_effort8/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_effort8/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 109
- Episodes completed total: 212
- First/last quintile mean reward: 33.020628 / 49.828830
- Within-checkpoint reward change: +16.808202
- Fixed-eval hit rate: 13/50 (26.0%)
- Fixed-eval mean/median miss distance: 9.948 / 8.733 m
- Fixed-eval mean episode reward: 29.818768
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.595968 / 25.701506
- Fixed-eval mean legacy episode reward: -0.061951
- Fixed-eval mean control effort: 641315.911590 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 118.560 / 74.646 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 12/25/13
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_effort8/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_effort8/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 106
- Episodes completed total: 318
- First/last quintile mean reward: 23.845695 / 16.900974
- Within-checkpoint reward change: -6.944721
- Fixed-eval hit rate: 21/50 (42.0%)
- Fixed-eval mean/median miss distance: 6.870 / 5.822 m
- Fixed-eval mean episode reward: 39.526775
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -39.017743 / 41.831288
- Fixed-eval mean legacy episode reward: 39.481863
- Fixed-eval mean control effort: 649001.722489 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 120.771 / 79.194 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/23/21
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_effort8/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_effort8/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 112
- Episodes completed total: 430
- First/last quintile mean reward: 16.233280 / 2.717917
- Within-checkpoint reward change: -13.515364
- Fixed-eval hit rate: 21/50 (42.0%)
- Fixed-eval mean/median miss distance: 7.048 / 6.099 m
- Fixed-eval mean episode reward: -3.433377
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -81.971515 / 41.824908
- Fixed-eval mean legacy episode reward: 31.401306
- Fixed-eval mean control effort: 1314315.015002 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 182.581 / 117.608 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/22/21
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_effort8/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_effort8/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 123
- Episodes completed total: 553
- First/last quintile mean reward: 29.903960 / 36.240470
- Within-checkpoint reward change: +6.336509
- Fixed-eval hit rate: 28/50 (56.0%)
- Fixed-eval mean/median miss distance: 5.504 / 4.804 m
- Fixed-eval mean episode reward: 34.836490
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -57.764423 / 55.887682
- Fixed-eval mean legacy episode reward: 62.196536
- Fixed-eval mean control effort: 1108905.094813 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 172.042 / 98.582 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/17/28
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_effort8/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_effort8/training_curve.png`
