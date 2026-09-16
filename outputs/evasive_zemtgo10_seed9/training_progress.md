# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 123456789
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 106
- Episodes completed total: 106
- First/last quintile mean reward: 1.235152 / 18.912429
- Within-checkpoint reward change: +17.677278
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 15.954 / 12.754 m
- Fixed-eval mean episode reward: 23.971129
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.221770 / 9.479669
- Fixed-eval mean legacy episode reward: -38.172815
- Fixed-eval mean control effort: 485469.259526 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 108.995 / 80.258 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 30/15/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 108
- Episodes completed total: 214
- First/last quintile mean reward: 25.860855 / 48.973881
- Within-checkpoint reward change: +23.113026
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 13.748 / 11.287 m
- Fixed-eval mean episode reward: 17.422623
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.838043 / 3.547436
- Fixed-eval mean legacy episode reward: -61.791443
- Fixed-eval mean control effort: 963191.972549 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.222 / 81.300 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 30/18/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 118
- Episodes completed total: 332
- First/last quintile mean reward: 26.921208 / 50.706523
- Within-checkpoint reward change: +23.785315
- Fixed-eval hit rate: 19/50 (38.0%)
- Fixed-eval mean/median miss distance: 7.392 / 6.090 m
- Fixed-eval mean episode reward: 53.989858
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.531098 / 37.807725
- Fixed-eval mean legacy episode reward: 15.429801
- Fixed-eval mean control effort: 963209.777182 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 154.118 / 77.885 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 16/15/19
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 127
- Episodes completed total: 459
- First/last quintile mean reward: 30.123705 / 74.711406
- Within-checkpoint reward change: +44.587701
- Fixed-eval hit rate: 22/50 (44.0%)
- Fixed-eval mean/median miss distance: 6.203 / 5.406 m
- Fixed-eval mean episode reward: 63.983039
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.580525 / 43.850334
- Fixed-eval mean legacy episode reward: 26.264590
- Fixed-eval mean control effort: 1045335.217763 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 167.229 / 72.783 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 17/11/22
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 141
- Episodes completed total: 600
- First/last quintile mean reward: 68.434370 / 75.019474
- Within-checkpoint reward change: +6.585104
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.716 / 4.128 m
- Fixed-eval mean episode reward: 90.519162
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.119796 / 71.925727
- Fixed-eval mean legacy episode reward: 90.875195
- Fixed-eval mean control effort: 1088512.315894 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 199.700 / 83.248 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/8/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 140
- Episodes completed total: 740
- First/last quintile mean reward: 80.823110 / 76.410158
- Within-checkpoint reward change: -4.412952
- Fixed-eval hit rate: 32/50 (64.0%)
- Fixed-eval mean/median miss distance: 5.233 / 4.394 m
- Fixed-eval mean episode reward: 82.558222
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.052515 / 63.897507
- Fixed-eval mean legacy episode reward: 70.097204
- Fixed-eval mean control effort: 1161312.936843 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 196.290 / 81.709 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/9/32
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 152
- Episodes completed total: 892
- First/last quintile mean reward: 125.406454 / 105.777325
- Within-checkpoint reward change: -19.629129
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.807 / 4.248 m
- Fixed-eval mean episode reward: 126.473661
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.240777 / 106.001208
- Fixed-eval mean legacy episode reward: 104.169673
- Fixed-eval mean control effort: 1043747.889845 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 199.022 / 82.337 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/7/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 151
- Episodes completed total: 1043
- First/last quintile mean reward: 120.709482 / 96.865609
- Within-checkpoint reward change: -23.843873
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 5.229 / 4.519 m
- Fixed-eval mean episode reward: 114.608414
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.128111 / 95.023294
- Fixed-eval mean legacy episode reward: 84.672758
- Fixed-eval mean control effort: 1094589.402465 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 199.157 / 82.581 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/7/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed9/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed9/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed9/training_curve.png`
