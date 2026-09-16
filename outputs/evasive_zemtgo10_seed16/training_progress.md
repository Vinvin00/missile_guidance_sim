# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 1732050807
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 99
- Episodes completed total: 99
- First/last quintile mean reward: -8.031722 / 30.827945
- Within-checkpoint reward change: +38.859668
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 10.541 / 10.337 m
- Fixed-eval mean episode reward: 3.680521
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -50.707459 / 17.674750
- Fixed-eval mean legacy episode reward: -17.206809
- Fixed-eval mean control effort: 1197779.569145 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 163.677 / 114.274 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/33/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 99
- Episodes completed total: 198
- First/last quintile mean reward: 15.611030 / 2.199631
- Within-checkpoint reward change: -13.411399
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 11.336 / 10.640 m
- Fixed-eval mean episode reward: -12.046846
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -58.394774 / 9.634698
- Fixed-eval mean legacy episode reward: -37.906793
- Fixed-eval mean control effort: 1464204.367017 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 181.431 / 123.487 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/35/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 120
- Episodes completed total: 318
- First/last quintile mean reward: 31.437322 / 75.112442
- Within-checkpoint reward change: +43.675120
- Fixed-eval hit rate: 22/50 (44.0%)
- Fixed-eval mean/median miss distance: 6.089 / 5.400 m
- Fixed-eval mean episode reward: 40.169647
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -40.397705 / 43.854122
- Fixed-eval mean legacy episode reward: 38.507705
- Fixed-eval mean control effort: 1036466.003963 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 150.701 / 98.540 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/22/22
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 151
- Episodes completed total: 469
- First/last quintile mean reward: 59.900483 / 98.103123
- Within-checkpoint reward change: +38.202640
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 4.746 / 4.321 m
- Fixed-eval mean episode reward: 79.753992
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.885249 / 69.926011
- Fixed-eval mean legacy episode reward: 93.954656
- Fixed-eval mean control effort: 836713.296344 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.954 / 85.683 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/12/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 143
- Episodes completed total: 612
- First/last quintile mean reward: 53.129393 / 82.663539
- Within-checkpoint reward change: +29.534147
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 4.538 / 4.186 m
- Fixed-eval mean episode reward: 77.735377
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.909072 / 69.931219
- Fixed-eval mean legacy episode reward: 84.657428
- Fixed-eval mean control effort: 1362794.980767 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 219.445 / 98.962 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/11/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 152
- Episodes completed total: 764
- First/last quintile mean reward: 60.691420 / 83.199886
- Within-checkpoint reward change: +22.508466
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.539 / 4.179 m
- Fixed-eval mean episode reward: 92.365956
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.285247 / 75.937972
- Fixed-eval mean legacy episode reward: 107.568825
- Fixed-eval mean control effort: 713620.476901 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 150.552 / 75.763 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/11/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 150
- Episodes completed total: 914
- First/last quintile mean reward: 104.154978 / 128.109516
- Within-checkpoint reward change: +23.954539
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.819 / 3.622 m
- Fixed-eval mean episode reward: 136.585921
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.484810 / 114.357501
- Fixed-eval mean legacy episode reward: 128.116321
- Fixed-eval mean control effort: 551067.384444 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.892 / 66.855 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/7/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 163
- Episodes completed total: 1077
- First/last quintile mean reward: 137.256275 / 135.461341
- Within-checkpoint reward change: -1.794934
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.728 / 3.855 m
- Fixed-eval mean episode reward: 144.497966
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.643332 / 119.428067
- Fixed-eval mean legacy episode reward: 137.947858
- Fixed-eval mean control effort: 449781.475014 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 127.220 / 61.743 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed16/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed16/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed16/training_curve.png`
