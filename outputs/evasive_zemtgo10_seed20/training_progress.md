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
- Training seed: 3605551275
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 103
- Episodes completed total: 103
- First/last quintile mean reward: -0.949787 / 9.980458
- Within-checkpoint reward change: +10.930246
- Fixed-eval hit rate: 12/50 (24.0%)
- Fixed-eval mean/median miss distance: 9.829 / 7.885 m
- Fixed-eval mean episode reward: 15.147209
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -45.271398 / 23.705377
- Fixed-eval mean legacy episode reward: -1.921464
- Fixed-eval mean control effort: 972189.664371 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 147.449 / 108.491 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/31/12
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 108
- Episodes completed total: 211
- First/last quintile mean reward: 31.562409 / 49.256253
- Within-checkpoint reward change: +17.693844
- Fixed-eval hit rate: 21/50 (42.0%)
- Fixed-eval mean/median miss distance: 7.322 / 5.355 m
- Fixed-eval mean episode reward: 40.390061
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -38.139879 / 41.816710
- Fixed-eval mean legacy episode reward: 36.922020
- Fixed-eval mean control effort: 881292.303485 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.171 / 93.275 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/24/21
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 116
- Episodes completed total: 327
- First/last quintile mean reward: 52.914677 / 46.847232
- Within-checkpoint reward change: -6.067445
- Fixed-eval hit rate: 13/50 (26.0%)
- Fixed-eval mean/median miss distance: 7.637 / 7.223 m
- Fixed-eval mean episode reward: 11.647480
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -50.846564 / 25.780814
- Fixed-eval mean legacy episode reward: -5.033041
- Fixed-eval mean control effort: 1200293.718705 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 165.993 / 114.452 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/30/13
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 127
- Episodes completed total: 454
- First/last quintile mean reward: 32.681370 / 63.578675
- Within-checkpoint reward change: +30.897305
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.845 / 4.324 m
- Fixed-eval mean episode reward: 88.570908
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.071617 / 73.929295
- Fixed-eval mean legacy episode reward: 102.579154
- Fixed-eval mean control effort: 703050.609296 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 145.940 / 77.274 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/12/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 146
- Episodes completed total: 600
- First/last quintile mean reward: 71.300571 / 98.132136
- Within-checkpoint reward change: +26.831565
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 4.804 / 4.333 m
- Fixed-eval mean episode reward: 79.868363
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.767157 / 69.922289
- Fixed-eval mean legacy episode reward: 91.145623
- Fixed-eval mean control effort: 857664.552872 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 159.806 / 84.529 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/12/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 138
- Episodes completed total: 738
- First/last quintile mean reward: 81.373046 / 81.815170
- Within-checkpoint reward change: +0.442124
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.427 / 4.158 m
- Fixed-eval mean episode reward: 84.395541
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -24.254073 / 71.936383
- Fixed-eval mean legacy episode reward: 99.347300
- Fixed-eval mean control effort: 755993.381168 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.908 / 80.920 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/14/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 157
- Episodes completed total: 895
- First/last quintile mean reward: 118.324363 / 132.860013
- Within-checkpoint reward change: +14.535650
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.649 / 3.986 m
- Fixed-eval mean episode reward: 108.830136
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -25.285804 / 97.402710
- Fixed-eval mean legacy episode reward: 98.280467
- Fixed-eval mean control effort: 818145.795727 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 156.835 / 82.864 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/12/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 145
- Episodes completed total: 1040
- First/last quintile mean reward: 137.162474 / 72.669444
- Within-checkpoint reward change: -64.493031
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.811 / 4.419 m
- Fixed-eval mean episode reward: 113.242164
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -21.977250 / 98.506183
- Fixed-eval mean legacy episode reward: 98.958405
- Fixed-eval mean control effort: 791669.758960 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.196 / 76.817 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/12/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed20/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed20/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed20/training_curve.png`
