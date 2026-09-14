# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 77000001
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 106
- Episodes completed total: 106
- First/last quintile mean reward: 9.710373 / 24.990237
- Within-checkpoint reward change: +15.279864
- Fixed-eval hit rate: 4/50 (8.0%)
- Fixed-eval mean/median miss distance: 14.644 / 12.475 m
- Fixed-eval mean episode reward: 10.603597
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -33.633231 / 7.523598
- Fixed-eval mean legacy episode reward: -44.229248
- Fixed-eval mean control effort: 753292.935687 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 130.958 / 96.092 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 21/25/4
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 106
- Episodes completed total: 212
- First/last quintile mean reward: 22.034182 / 20.222333
- Within-checkpoint reward change: -1.811849
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 9.585 / 9.387 m
- Fixed-eval mean episode reward: 23.820896
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -30.596990 / 17.704656
- Fixed-eval mean legacy episode reward: -25.089067
- Fixed-eval mean control effort: 844586.118770 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 144.939 / 94.592 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 28/13/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 115
- Episodes completed total: 327
- First/last quintile mean reward: 19.630814 / 57.389909
- Within-checkpoint reward change: +37.759095
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 9.973 / 7.832 m
- Fixed-eval mean episode reward: 31.702790
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.716605 / 27.706164
- Fixed-eval mean legacy episode reward: -4.514801
- Fixed-eval mean control effort: 947641.863874 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 146.674 / 93.383 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 17/19/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 119
- Episodes completed total: 446
- First/last quintile mean reward: 42.290325 / 64.005205
- Within-checkpoint reward change: +21.714881
- Fixed-eval hit rate: 33/50 (66.0%)
- Fixed-eval mean/median miss distance: 5.103 / 4.569 m
- Fixed-eval mean episode reward: 83.301069
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.327899 / 65.915738
- Fixed-eval mean legacy episode reward: 85.978268
- Fixed-eval mean control effort: 680591.848797 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.677 / 72.325 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/13/33
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 128
- Episodes completed total: 574
- First/last quintile mean reward: 74.831917 / 65.540803
- Within-checkpoint reward change: -9.291114
- Fixed-eval hit rate: 31/50 (62.0%)
- Fixed-eval mean/median miss distance: 5.540 / 4.451 m
- Fixed-eval mean episode reward: 77.003476
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -21.600590 / 61.890836
- Fixed-eval mean legacy episode reward: 73.862356
- Fixed-eval mean control effort: 908484.830436 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 167.155 / 83.610 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/9/31
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 137
- Episodes completed total: 711
- First/last quintile mean reward: 61.810577 / 77.551941
- Within-checkpoint reward change: +15.741363
- Fixed-eval hit rate: 34/50 (68.0%)
- Fixed-eval mean/median miss distance: 4.872 / 4.766 m
- Fixed-eval mean episode reward: 81.103421
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.533979 / 67.924170
- Fixed-eval mean legacy episode reward: 84.974542
- Fixed-eval mean control effort: 1045034.985128 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 190.209 / 89.534 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/12/34
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed2/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed2/training_curve.png`
