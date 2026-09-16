# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 27182818
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 98
- Episodes completed total: 98
- First/last quintile mean reward: -10.668428 / 24.780835
- Within-checkpoint reward change: +35.449262
- Fixed-eval hit rate: 1/50 (2.0%)
- Fixed-eval mean/median miss distance: 14.702 / 14.014 m
- Fixed-eval mean episode reward: 0.890950
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -37.334582 / 1.512302
- Fixed-eval mean legacy episode reward: -60.033728
- Fixed-eval mean control effort: 1131071.172253 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 158.601 / 98.503 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/39/1
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 102
- Episodes completed total: 200
- First/last quintile mean reward: 10.334130 / 45.869886
- Within-checkpoint reward change: +35.535755
- Fixed-eval hit rate: 18/50 (36.0%)
- Fixed-eval mean/median miss distance: 7.765 / 6.239 m
- Fixed-eval mean episode reward: 34.808636
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -37.693402 / 35.788807
- Fixed-eval mean legacy episode reward: 16.458124
- Fixed-eval mean control effort: 1086153.154776 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 160.122 / 101.740 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/26/18
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 114
- Episodes completed total: 314
- First/last quintile mean reward: 21.818905 / 51.920921
- Within-checkpoint reward change: +30.102017
- Fixed-eval hit rate: 19/50 (38.0%)
- Fixed-eval mean/median miss distance: 6.889 / 5.747 m
- Fixed-eval mean episode reward: 40.370485
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -34.166279 / 37.823534
- Fixed-eval mean legacy episode reward: 17.388040
- Fixed-eval mean control effort: 1108640.893117 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 166.638 / 99.002 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/26/19
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 123
- Episodes completed total: 437
- First/last quintile mean reward: 59.832469 / 51.788875
- Within-checkpoint reward change: -8.043594
- Fixed-eval hit rate: 27/50 (54.0%)
- Fixed-eval mean/median miss distance: 5.723 / 4.643 m
- Fixed-eval mean episode reward: 64.336238
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.256170 / 53.879178
- Fixed-eval mean legacy episode reward: 54.413370
- Fixed-eval mean control effort: 947941.288805 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 159.457 / 85.891 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/17/27
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 151
- Episodes completed total: 588
- First/last quintile mean reward: 81.636255 / 79.261850
- Within-checkpoint reward change: -2.374404
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.753 / 3.578 m
- Fixed-eval mean episode reward: 114.345968
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.336318 / 87.969056
- Fixed-eval mean legacy episode reward: 136.080386
- Fixed-eval mean control effort: 532885.394098 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 144.320 / 64.829 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 164
- Episodes completed total: 752
- First/last quintile mean reward: 96.271528 / 94.582992
- Within-checkpoint reward change: -1.688536
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.747 / 3.486 m
- Fixed-eval mean episode reward: 108.185654
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.491562 / 83.963985
- Fixed-eval mean legacy episode reward: 124.732911
- Fixed-eval mean control effort: 665034.179406 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 158.891 / 67.815 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/6/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 162
- Episodes completed total: 914
- First/last quintile mean reward: 127.422237 / 119.328941
- Within-checkpoint reward change: -8.093295
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 4.062 / 3.954 m
- Fixed-eval mean episode reward: 141.319300
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.343937 / 115.950007
- Fixed-eval mean legacy episode reward: 129.983446
- Fixed-eval mean control effort: 606774.447473 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.568 / 65.785 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/5/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 1078
- First/last quintile mean reward: 141.809578 / 106.258959
- Within-checkpoint reward change: -35.550619
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.349 / 4.287 m
- Fixed-eval mean episode reward: 135.887467
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.254466 / 111.428703
- Fixed-eval mean legacy episode reward: 121.645580
- Fixed-eval mean control effort: 642938.829104 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 153.524 / 66.653 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed5/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed5/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed5/training_curve.png`
