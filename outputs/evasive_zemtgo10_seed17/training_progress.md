# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 2236067977
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 98
- Episodes completed total: 98
- First/last quintile mean reward: -9.146500 / 41.335346
- Within-checkpoint reward change: +50.481846
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 10.074 / 8.855 m
- Fixed-eval mean episode reward: 39.353611
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -25.058431 / 27.698811
- Fixed-eval mean legacy episode reward: 4.644098
- Fixed-eval mean control effort: 488310.270801 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 103.880 / 81.296 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/28/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 102
- Episodes completed total: 200
- First/last quintile mean reward: 26.508703 / 44.416945
- Within-checkpoint reward change: +17.908242
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 14.032 / 13.123 m
- Fixed-eval mean episode reward: 21.504868
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -24.756090 / 9.547727
- Fixed-eval mean legacy episode reward: -31.223108
- Fixed-eval mean control effort: 480378.261660 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 104.002 / 82.096 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 13/32/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 109
- Episodes completed total: 309
- First/last quintile mean reward: 34.803841 / 58.370911
- Within-checkpoint reward change: +23.567070
- Fixed-eval hit rate: 29/50 (58.0%)
- Fixed-eval mean/median miss distance: 6.624 / 4.720 m
- Fixed-eval mean episode reward: 56.198114
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -38.370663 / 57.855546
- Fixed-eval mean legacy episode reward: 70.598833
- Fixed-eval mean control effort: 880298.227775 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.630 / 106.561 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/17/29
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 120
- Episodes completed total: 429
- First/last quintile mean reward: 66.799466 / 46.280163
- Within-checkpoint reward change: -20.519302
- Fixed-eval hit rate: 32/50 (64.0%)
- Fixed-eval mean/median miss distance: 5.195 / 4.357 m
- Fixed-eval mean episode reward: 65.145551
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -35.473653 / 63.905974
- Fixed-eval mean legacy episode reward: 80.561229
- Fixed-eval mean control effort: 1017432.998304 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 175.814 / 98.866 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/15/32
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 134
- Episodes completed total: 563
- First/last quintile mean reward: 39.404448 / 74.672944
- Within-checkpoint reward change: +35.268496
- Fixed-eval hit rate: 29/50 (58.0%)
- Fixed-eval mean/median miss distance: 5.438 / 4.837 m
- Fixed-eval mean episode reward: 54.627663
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -39.980546 / 57.894979
- Fixed-eval mean legacy episode reward: 66.058562
- Fixed-eval mean control effort: 1152056.617935 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 178.871 / 103.160 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/17/29
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 151
- Episodes completed total: 714
- First/last quintile mean reward: 72.181247 / 98.350583
- Within-checkpoint reward change: +26.169337
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.534 / 4.174 m
- Fixed-eval mean episode reward: 86.859597
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -25.796986 / 75.943352
- Fixed-eval mean legacy episode reward: 107.213401
- Fixed-eval mean control effort: 855826.721324 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 167.647 / 86.875 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/10/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 154
- Episodes completed total: 868
- First/last quintile mean reward: 104.471016 / 140.862571
- Within-checkpoint reward change: +36.391555
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.138 / 3.992 m
- Fixed-eval mean episode reward: 122.805186
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.883866 / 106.975821
- Fixed-eval mean legacy episode reward: 113.082252
- Fixed-eval mean control effort: 750744.516813 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 160.157 / 77.545 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/9/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 155
- Episodes completed total: 1023
- First/last quintile mean reward: 100.385171 / 111.266455
- Within-checkpoint reward change: +10.881284
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.761 / 3.597 m
- Fixed-eval mean episode reward: 135.270580
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.765923 / 118.323272
- Fixed-eval mean legacy episode reward: 134.019855
- Fixed-eval mean control effort: 730554.701760 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 162.801 / 78.067 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`
