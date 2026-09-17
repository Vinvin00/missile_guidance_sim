# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Pursuer plant: pointmass
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 3316624790
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 96
- Episodes completed total: 96
- First/last quintile mean reward: 2.433886 / 14.131109
- Within-checkpoint reward change: +11.697222
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 14.256 / 12.771 m
- Fixed-eval mean episode reward: -18.996258
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -65.247993 / 9.538505
- Fixed-eval mean legacy episode reward: -35.372447
- Fixed-eval mean control effort: 1355943.651233 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 175.038 / 131.102 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/35/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 102
- Episodes completed total: 198
- First/last quintile mean reward: 9.778109 / 28.892931
- Within-checkpoint reward change: +19.114822
- Fixed-eval hit rate: 18/50 (36.0%)
- Fixed-eval mean/median miss distance: 6.933 / 5.837 m
- Fixed-eval mean episode reward: 31.781179
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -40.746099 / 35.814048
- Fixed-eval mean legacy episode reward: 20.424165
- Fixed-eval mean control effort: 940625.783870 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 144.356 / 100.512 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/24/18
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 120
- Episodes completed total: 318
- First/last quintile mean reward: 27.846790 / 77.400919
- Within-checkpoint reward change: +49.554129
- Fixed-eval hit rate: 26/50 (52.0%)
- Fixed-eval mean/median miss distance: 5.846 / 4.926 m
- Fixed-eval mean episode reward: 55.291332
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -33.291328 / 51.869430
- Fixed-eval mean legacy episode reward: 51.749813
- Fixed-eval mean control effort: 924321.854662 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.098 / 92.439 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/20/26
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 136
- Episodes completed total: 454
- First/last quintile mean reward: 76.585719 / 85.913798
- Within-checkpoint reward change: +9.328079
- Fixed-eval hit rate: 34/50 (68.0%)
- Fixed-eval mean/median miss distance: 4.964 / 4.495 m
- Fixed-eval mean episode reward: 82.139275
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.489066 / 67.915110
- Fixed-eval mean legacy episode reward: 89.523932
- Fixed-eval mean control effort: 686243.957569 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 139.914 / 77.190 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/12/34
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 136
- Episodes completed total: 590
- First/last quintile mean reward: 54.463422 / 76.214526
- Within-checkpoint reward change: +21.751105
- Fixed-eval hit rate: 32/50 (64.0%)
- Fixed-eval mean/median miss distance: 5.187 / 4.656 m
- Fixed-eval mean episode reward: 74.032361
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.589376 / 63.908507
- Fixed-eval mean legacy episode reward: 75.294774
- Fixed-eval mean control effort: 1027146.441405 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 179.061 / 85.610 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/15/32
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 149
- Episodes completed total: 739
- First/last quintile mean reward: 78.444683 / 114.404523
- Within-checkpoint reward change: +35.959840
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.159 / 3.886 m
- Fixed-eval mean episode reward: 91.473313
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.185306 / 73.945389
- Fixed-eval mean legacy episode reward: 102.121104
- Fixed-eval mean control effort: 716899.266613 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 149.215 / 73.372 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/9/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 165
- Episodes completed total: 904
- First/last quintile mean reward: 120.003891 / 139.547252
- Within-checkpoint reward change: +19.543361
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.004 / 3.709 m
- Fixed-eval mean episode reward: 132.402807
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.175828 / 110.865404
- Fixed-eval mean legacy episode reward: 117.467878
- Fixed-eval mean control effort: 570743.530708 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 136.456 / 66.972 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/6/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 167
- Episodes completed total: 1071
- First/last quintile mean reward: 133.235543 / 124.741603
- Within-checkpoint reward change: -8.493939
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.839 / 3.717 m
- Fixed-eval mean episode reward: 141.966540
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.183053 / 117.436363
- Fixed-eval mean legacy episode reward: 130.980929
- Fixed-eval mean control effort: 508697.052232 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 133.150 / 63.022 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/7/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed19/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed19/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed19/training_curve.png`
