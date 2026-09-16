# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 10 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: True (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -33.804517 / -36.523551
- Within-checkpoint reward change: -2.719034
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 3620.651 / 3396.261 m
- Fixed-eval mean episode reward: -63.324076
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -1.657563 / -99.693002
- Fixed-eval mean legacy episode reward: -82.167584
- Fixed-eval mean control effort: 20238.069944 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 28.303 / 28.086 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/6 / 3205.810 / 3208.065 m / -63.078169 / 18376.892959 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 4450.333 / 4450.837 m / -63.815891 / 23960.423915 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `hard_lineage/rl_checkpoint_01_eval.json`
- Training curve: `hard_lineage/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: -40.336758 / -27.815035
- Within-checkpoint reward change: +12.521723
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 1932.696 / 1568.035 m
- Fixed-eval mean episode reward: -54.722693
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -1.488369 / -91.260812
- Fixed-eval mean legacy episode reward: -48.403885
- Fixed-eval mean control effort: 18268.982365 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 26.945 / 26.662 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/6 / 1369.272 / 1286.981 m / -50.565088 / 17170.445824 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 3059.542 / 2861.506 m / -63.037901 / 20466.055446 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `hard_lineage/rl_checkpoint_02_eval.json`
- Training curve: `hard_lineage/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 16
- Episodes completed total: 48
- First/last quintile mean reward: -25.834242 / -12.517241
- Within-checkpoint reward change: +13.317001
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 497.378 / 30.133 m
- Fixed-eval mean episode reward: 2.605374
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -6.357454 / -29.063661
- Fixed-eval mean legacy episode reward: -38.117112
- Fixed-eval mean control effort: 83674.932670 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 55.579 / 53.235 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/6 / 22.221 / 19.375 m / 27.552504 / 109467.736484 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1447.691 / 1385.933 m / -47.288885 / 32089.325043 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `hard_lineage/rl_checkpoint_03_eval.json`
- Training curve: `hard_lineage/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 81,920
- Episodes completed this checkpoint: 16
- Episodes completed total: 64
- First/last quintile mean reward: -5.043875 / 20.231900
- Within-checkpoint reward change: +25.275775
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 535.188 / 21.809 m
- Fixed-eval mean episode reward: 37.477546
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -5.392357 / 4.843415
- Fixed-eval mean legacy episode reward: 30.548459
- Fixed-eval mean control effort: 83051.287438 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 49.712 / 44.620 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 11.963 / 12.156 m / 81.018763 / 96949.623023 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1581.638 / 1495.619 m / -49.604887 / 55254.616269 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `hard_lineage/rl_checkpoint_04_eval.json`
- Training curve: `hard_lineage/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 102,400
- Episodes completed this checkpoint: 16
- Episodes completed total: 80
- First/last quintile mean reward: 12.624609 / 12.326831
- Within-checkpoint reward change: -0.297778
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 550.207 / 7.260 m
- Fixed-eval mean episode reward: 34.320467
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -7.734044 / 4.028022
- Fixed-eval mean legacy episode reward: 29.692978
- Fixed-eval mean control effort: 118110.027924 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 54.486 / 49.165 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 6.673 / 4.895 m / 77.519030 / 157299.802954 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1637.275 / 1451.360 m / -52.076658 / 39730.477863 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `hard_lineage/rl_checkpoint_05_eval.json`
- Training curve: `hard_lineage/training_curve.png`
