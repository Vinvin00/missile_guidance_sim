# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 1618033988
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 95
- Episodes completed total: 95
- First/last quintile mean reward: -3.731250 / 17.554836
- Within-checkpoint reward change: +21.286085
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 13.826 / 11.195 m
- Fixed-eval mean episode reward: -0.682514
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -46.948281 / 9.552536
- Fixed-eval mean legacy episode reward: -39.435221
- Fixed-eval mean control effort: 1213162.973633 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 165.977 / 112.326 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/36/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 102
- Episodes completed total: 197
- First/last quintile mean reward: 26.842135 / 48.693194
- Within-checkpoint reward change: +21.851058
- Fixed-eval hit rate: 16/50 (32.0%)
- Fixed-eval mean/median miss distance: 7.259 / 6.397 m
- Fixed-eval mean episode reward: 26.895790
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -41.618851 / 31.801410
- Fixed-eval mean legacy episode reward: 15.489869
- Fixed-eval mean control effort: 950926.134782 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 146.492 / 103.010 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/30/16
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 118
- Episodes completed total: 315
- First/last quintile mean reward: 44.226891 / 41.208091
- Within-checkpoint reward change: -3.018800
- Fixed-eval hit rate: 26/50 (52.0%)
- Fixed-eval mean/median miss distance: 6.216 / 4.934 m
- Fixed-eval mean episode reward: 49.677063
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -38.902120 / 51.865952
- Fixed-eval mean legacy episode reward: 54.938184
- Fixed-eval mean control effort: 1025905.366447 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 162.363 / 104.405 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/19/26
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 125
- Episodes completed total: 440
- First/last quintile mean reward: 39.209013 / 58.501084
- Within-checkpoint reward change: +19.292071
- Fixed-eval hit rate: 34/50 (68.0%)
- Fixed-eval mean/median miss distance: 5.439 / 4.559 m
- Fixed-eval mean episode reward: 75.645704
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.968190 / 67.900664
- Fixed-eval mean legacy episode reward: 86.460028
- Fixed-eval mean control effort: 1133178.671332 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 194.491 / 93.104 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/13/34
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 140
- Episodes completed total: 580
- First/last quintile mean reward: 79.099582 / 80.258469
- Within-checkpoint reward change: +1.158887
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.881 / 4.355 m
- Fixed-eval mean episode reward: 88.911380
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -21.732050 / 73.930199
- Fixed-eval mean legacy episode reward: 103.040312
- Fixed-eval mean control effort: 831702.768815 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 164.263 / 80.024 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 164
- Episodes completed total: 744
- First/last quintile mean reward: 100.842063 / 82.956797
- Within-checkpoint reward change: -17.885266
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.053 / 3.912 m
- Fixed-eval mean episode reward: 103.623841
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.046608 / 81.957219
- Fixed-eval mean legacy episode reward: 121.777211
- Fixed-eval mean control effort: 670692.555441 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.993 / 68.305 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 166
- Episodes completed total: 910
- First/last quintile mean reward: 152.440355 / 102.647146
- Within-checkpoint reward change: -49.793209
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.511 / 3.844 m
- Fixed-eval mean episode reward: 119.580588
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.268094 / 103.135452
- Fixed-eval mean legacy episode reward: 102.092526
- Fixed-eval mean control effort: 828421.824498 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 166.030 / 74.273 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 163
- Episodes completed total: 1073
- First/last quintile mean reward: 116.080200 / 146.790759
- Within-checkpoint reward change: +30.710559
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.676 / 3.457 m
- Fixed-eval mean episode reward: 140.716930
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.010943 / 118.014643
- Fixed-eval mean legacy episode reward: 129.218515
- Fixed-eval mean control effort: 718649.524629 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 170.055 / 67.814 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/6/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed12/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed12/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed12/training_curve.png`
