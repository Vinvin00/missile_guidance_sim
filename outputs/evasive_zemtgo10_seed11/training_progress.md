# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 1123581321
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 106
- Episodes completed total: 106
- First/last quintile mean reward: 0.287061 / 42.144436
- Within-checkpoint reward change: +41.857375
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 14.583 / 11.516 m
- Fixed-eval mean episode reward: 11.236774
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.995215 / 3.518758
- Fixed-eval mean legacy episode reward: -58.054334
- Fixed-eval mean control effort: 1010209.090443 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 152.279 / 88.778 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 25/23/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 112
- Episodes completed total: 218
- First/last quintile mean reward: 29.301583 / 30.246572
- Within-checkpoint reward change: +0.944989
- Fixed-eval hit rate: 10/50 (20.0%)
- Fixed-eval mean/median miss distance: 9.104 / 8.168 m
- Fixed-eval mean episode reward: 33.131962
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.305353 / 19.724085
- Fixed-eval mean legacy episode reward: -24.246008
- Fixed-eval mean control effort: 1019584.060057 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 157.769 / 82.130 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 27/13/10
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 115
- Episodes completed total: 333
- First/last quintile mean reward: 48.135710 / 47.958474
- Within-checkpoint reward change: -0.177237
- Fixed-eval hit rate: 17/50 (34.0%)
- Fixed-eval mean/median miss distance: 7.827 / 6.491 m
- Fixed-eval mean episode reward: 45.290623
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -25.211015 / 33.788407
- Fixed-eval mean legacy episode reward: 8.015810
- Fixed-eval mean control effort: 925325.247549 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 149.351 / 83.816 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 18/15/17
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 129
- Episodes completed total: 462
- First/last quintile mean reward: 53.001179 / 33.289359
- Within-checkpoint reward change: -19.711820
- Fixed-eval hit rate: 22/50 (44.0%)
- Fixed-eval mean/median miss distance: 6.232 / 5.410 m
- Fixed-eval mean episode reward: 59.705043
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.860116 / 43.851929
- Fixed-eval mean legacy episode reward: 27.476004
- Fixed-eval mean control effort: 1014382.907297 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 158.795 / 78.736 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 13/15/22
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 146
- Episodes completed total: 608
- First/last quintile mean reward: 94.658536 / 101.061827
- Within-checkpoint reward change: +6.403292
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.153 / 3.864 m
- Fixed-eval mean episode reward: 100.259643
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.402666 / 75.949078
- Fixed-eval mean legacy episode reward: 104.834454
- Fixed-eval mean control effort: 753341.416766 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 158.212 / 68.930 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/8/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 174
- Episodes completed total: 782
- First/last quintile mean reward: 103.056974 / 106.097549
- Within-checkpoint reward change: +3.040576
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.455 / 4.083 m
- Fixed-eval mean episode reward: 96.153078
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.502707 / 75.942554
- Fixed-eval mean legacy episode reward: 101.999732
- Fixed-eval mean control effort: 907888.942476 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 180.825 / 78.240 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/7/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 164
- Episodes completed total: 946
- First/last quintile mean reward: 119.997574 / 130.114817
- Within-checkpoint reward change: +10.117244
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.395 / 4.252 m
- Fixed-eval mean episode reward: 130.527804
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.564797 / 106.379370
- Fixed-eval mean legacy episode reward: 108.144478
- Fixed-eval mean control effort: 838451.550241 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 175.702 / 71.819 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/5/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 163
- Episodes completed total: 1109
- First/last quintile mean reward: 127.401598 / 120.076403
- Within-checkpoint reward change: -7.325194
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.386 / 4.195 m
- Fixed-eval mean episode reward: 135.581555
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.543357 / 110.411682
- Fixed-eval mean legacy episode reward: 118.198061
- Fixed-eval mean control effort: 775341.128667 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 172.983 / 69.832 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/5/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed11/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed11/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed11/training_curve.png`
