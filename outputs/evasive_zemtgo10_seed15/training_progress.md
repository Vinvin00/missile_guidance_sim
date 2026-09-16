# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 1414213562
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 102
- Episodes completed total: 102
- First/last quintile mean reward: -6.907634 / 26.846412
- Within-checkpoint reward change: +33.754047
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 11.009 / 10.369 m
- Fixed-eval mean episode reward: 18.364162
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -36.008377 / 17.659308
- Fixed-eval mean legacy episode reward: -14.340301
- Fixed-eval mean control effort: 826388.390184 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.376 / 96.343 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/32/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 104
- Episodes completed total: 206
- First/last quintile mean reward: 46.463425 / 28.934276
- Within-checkpoint reward change: -17.529149
- Fixed-eval hit rate: 19/50 (38.0%)
- Fixed-eval mean/median miss distance: 7.101 / 5.562 m
- Fixed-eval mean episode reward: 50.581837
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.945896 / 37.814503
- Fixed-eval mean legacy episode reward: 21.896176
- Fixed-eval mean control effort: 870959.397118 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.373 / 78.947 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/26/19
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 115
- Episodes completed total: 321
- First/last quintile mean reward: 58.085050 / 47.224421
- Within-checkpoint reward change: -10.860628
- Fixed-eval hit rate: 27/50 (54.0%)
- Fixed-eval mean/median miss distance: 6.334 / 4.853 m
- Fixed-eval mean episode reward: 67.466895
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.104087 / 53.857751
- Fixed-eval mean legacy episode reward: 62.189746
- Fixed-eval mean control effort: 579260.616475 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 116.769 / 76.933 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/15/27
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 118
- Episodes completed total: 439
- First/last quintile mean reward: 37.901837 / 46.576562
- Within-checkpoint reward change: +8.674724
- Fixed-eval hit rate: 19/50 (38.0%)
- Fixed-eval mean/median miss distance: 5.999 / 5.249 m
- Fixed-eval mean episode reward: 40.154730
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -34.407836 / 37.849336
- Fixed-eval mean legacy episode reward: 21.024519
- Fixed-eval mean control effort: 1085383.819623 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 157.527 / 94.189 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/23/19
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 144
- Episodes completed total: 583
- First/last quintile mean reward: 61.817807 / 100.618143
- Within-checkpoint reward change: +38.800336
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.423 / 4.276 m
- Fixed-eval mean episode reward: 88.208497
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.444567 / 73.939834
- Fixed-eval mean legacy episode reward: 96.232665
- Fixed-eval mean control effort: 1071575.605219 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 196.030 / 86.691 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/10/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 163
- Episodes completed total: 746
- First/last quintile mean reward: 77.493239 / 95.884901
- Within-checkpoint reward change: +18.391662
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.772 / 4.156 m
- Fixed-eval mean episode reward: 85.411441
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.226279 / 71.924490
- Fixed-eval mean legacy episode reward: 93.057960
- Fixed-eval mean control effort: 1082091.411591 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 196.281 / 84.550 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/10/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 156
- Episodes completed total: 902
- First/last quintile mean reward: 118.271426 / 118.073137
- Within-checkpoint reward change: -0.198289
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.488 / 4.078 m
- Fixed-eval mean episode reward: 122.890936
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.155201 / 105.332907
- Fixed-eval mean legacy episode reward: 108.587497
- Fixed-eval mean control effort: 920724.571023 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 184.580 / 77.778 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/8/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 156
- Episodes completed total: 1058
- First/last quintile mean reward: 129.502125 / 135.948929
- Within-checkpoint reward change: +6.446804
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.275 / 4.070 m
- Fixed-eval mean episode reward: 129.879046
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.220236 / 109.386052
- Fixed-eval mean legacy episode reward: 113.283556
- Fixed-eval mean control effort: 893552.869369 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 185.052 / 73.883 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/8/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed15/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed15/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed15/training_curve.png`
