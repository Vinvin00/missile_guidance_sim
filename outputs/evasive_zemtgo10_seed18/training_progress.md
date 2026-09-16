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
- Training seed: 2645751311
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 103
- Episodes completed total: 103
- First/last quintile mean reward: -1.208643 / 38.508384
- Within-checkpoint reward change: +39.717027
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 10.882 / 8.622 m
- Fixed-eval mean episode reward: 18.378376
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -27.985302 / 9.650448
- Fixed-eval mean legacy episode reward: -33.868633
- Fixed-eval mean control effort: 580369.974926 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 114.924 / 88.461 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 25/20/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 103
- Episodes completed total: 206
- First/last quintile mean reward: 28.800910 / 47.539221
- Within-checkpoint reward change: +18.738310
- Fixed-eval hit rate: 20/50 (40.0%)
- Fixed-eval mean/median miss distance: 8.521 / 5.917 m
- Fixed-eval mean episode reward: 38.867772
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -37.617682 / 39.772223
- Fixed-eval mean legacy episode reward: 28.794996
- Fixed-eval mean control effort: 775704.502089 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 130.820 / 98.016 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/21/20
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 102
- Episodes completed total: 308
- First/last quintile mean reward: 47.283957 / 18.592432
- Within-checkpoint reward change: -28.691525
- Fixed-eval hit rate: 20/50 (40.0%)
- Fixed-eval mean/median miss distance: 6.594 / 5.669 m
- Fixed-eval mean episode reward: 40.140391
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -36.408318 / 39.835479
- Fixed-eval mean legacy episode reward: 29.566904
- Fixed-eval mean control effort: 887728.431909 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 145.659 / 97.578 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/23/20
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 105
- Episodes completed total: 413
- First/last quintile mean reward: 30.854194 / 30.108026
- Within-checkpoint reward change: -0.746168
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 9.894 / 8.519 m
- Fixed-eval mean episode reward: 4.092659
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -50.316085 / 17.695513
- Fixed-eval mean legacy episode reward: -25.641381
- Fixed-eval mean control effort: 1196380.241775 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 164.140 / 113.731 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/35/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 139
- Episodes completed total: 552
- First/last quintile mean reward: 51.027253 / 62.544482
- Within-checkpoint reward change: +11.517230
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.798 / 4.191 m
- Fixed-eval mean episode reward: 91.460417
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.185294 / 73.932480
- Fixed-eval mean legacy episode reward: 103.758480
- Fixed-eval mean control effort: 641327.018738 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 139.822 / 72.668 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/12/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 160
- Episodes completed total: 712
- First/last quintile mean reward: 100.887383 / 100.087962
- Within-checkpoint reward change: -0.799421
- Fixed-eval hit rate: 47/50 (94.0%)
- Fixed-eval mean/median miss distance: 3.627 / 3.669 m
- Fixed-eval mean episode reward: 121.691171
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -9.008912 / 93.986853
- Fixed-eval mean legacy episode reward: 150.290418
- Fixed-eval mean control effort: 389630.375426 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 127.938 / 59.914 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/2/47
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 170
- Episodes completed total: 882
- First/last quintile mean reward: 126.289383 / 142.489548
- Within-checkpoint reward change: +16.200164
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.761 / 3.578 m
- Fixed-eval mean episode reward: 145.663711
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.271008 / 119.221489
- Fixed-eval mean legacy episode reward: 135.849032
- Fixed-eval mean control effort: 543095.447660 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 149.763 / 63.170 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 163
- Episodes completed total: 1045
- First/last quintile mean reward: 100.617460 / 133.266213
- Within-checkpoint reward change: +32.648753
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.713 / 3.620 m
- Fixed-eval mean episode reward: 145.814461
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.696938 / 119.798168
- Fixed-eval mean legacy episode reward: 135.255544
- Fixed-eval mean control effort: 509228.665306 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 142.634 / 62.159 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed18/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed18/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed18/training_curve.png`
