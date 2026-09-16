# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 99999999
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 107
- Episodes completed total: 107
- First/last quintile mean reward: -4.293958 / 46.297984
- Within-checkpoint reward change: +50.591942
- Fixed-eval hit rate: 11/50 (22.0%)
- Fixed-eval mean/median miss distance: 11.279 / 8.482 m
- Fixed-eval mean episode reward: 25.424589
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.944165 / 21.655524
- Fixed-eval mean legacy episode reward: -15.520499
- Fixed-eval mean control effort: 822147.943916 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 137.457 / 94.238 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 19/20/11
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 109
- Episodes completed total: 216
- First/last quintile mean reward: 50.105408 / 21.583159
- Within-checkpoint reward change: -28.522249
- Fixed-eval hit rate: 27/50 (54.0%)
- Fixed-eval mean/median miss distance: 6.169 / 4.838 m
- Fixed-eval mean episode reward: 73.560164
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.008751 / 53.855685
- Fixed-eval mean legacy episode reward: 61.322212
- Fixed-eval mean control effort: 601966.089215 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 111.402 / 67.006 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/16/27
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 117
- Episodes completed total: 333
- First/last quintile mean reward: 40.498715 / 50.159503
- Within-checkpoint reward change: +9.660788
- Fixed-eval hit rate: 21/50 (42.0%)
- Fixed-eval mean/median miss distance: 7.091 / 5.938 m
- Fixed-eval mean episode reward: 47.786590
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -30.745061 / 41.818420
- Fixed-eval mean legacy episode reward: 28.350005
- Fixed-eval mean control effort: 1011553.966875 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.218 / 91.494 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/22/21
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 127
- Episodes completed total: 460
- First/last quintile mean reward: 53.267283 / 64.952475
- Within-checkpoint reward change: +11.685192
- Fixed-eval hit rate: 28/50 (56.0%)
- Fixed-eval mean/median miss distance: 5.644 / 4.688 m
- Fixed-eval mean episode reward: 64.446298
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.147153 / 55.880221
- Fixed-eval mean legacy episode reward: 59.078570
- Fixed-eval mean control effort: 973966.472767 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 162.040 / 89.631 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/16/28
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 126
- Episodes completed total: 586
- First/last quintile mean reward: 52.736401 / 68.241427
- Within-checkpoint reward change: +15.505026
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.764 / 4.308 m
- Fixed-eval mean episode reward: 98.856285
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -13.789024 / 75.932079
- Fixed-eval mean legacy episode reward: 107.038234
- Fixed-eval mean control effort: 721825.649795 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 155.356 / 69.620 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/9/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 158
- Episodes completed total: 744
- First/last quintile mean reward: 95.073208 / 97.631043
- Within-checkpoint reward change: +2.557835
- Fixed-eval hit rate: 45/50 (90.0%)
- Fixed-eval mean/median miss distance: 3.838 / 3.617 m
- Fixed-eval mean episode reward: 117.816686
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -8.870298 / 89.973754
- Fixed-eval mean legacy episode reward: 140.752438
- Fixed-eval mean control effort: 518643.229542 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 146.092 / 60.154 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/45
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 182
- Episodes completed total: 926
- First/last quintile mean reward: 135.822686 / 143.272306
- Within-checkpoint reward change: +7.449620
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.577 / 3.392 m
- Fixed-eval mean episode reward: 148.639989
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -9.439954 / 121.366712
- Fixed-eval mean legacy episode reward: 131.723128
- Fixed-eval mean control effort: 553549.291126 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 145.129 / 58.709 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/6/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 170
- Episodes completed total: 1096
- First/last quintile mean reward: 133.907336 / 146.043566
- Within-checkpoint reward change: +12.136230
- Fixed-eval hit rate: 45/50 (90.0%)
- Fixed-eval mean/median miss distance: 3.461 / 3.465 m
- Fixed-eval mean episode reward: 153.214243
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -8.513587 / 125.014600
- Fixed-eval mean legacy episode reward: 141.409366
- Fixed-eval mean control effort: 491362.373992 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 141.924 / 57.796 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/45
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed8/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed8/training_curve.png`
