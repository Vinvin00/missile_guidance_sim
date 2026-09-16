# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 10 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: True (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 77777777
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -59.285182 / -45.138896
- Within-checkpoint reward change: +14.146286
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 785.984 / 447.498 m
- Fixed-eval mean episode reward: -19.110680
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -1.053893 / -56.083276
- Fixed-eval mean legacy episode reward: -41.406252
- Fixed-eval mean control effort: 13416.016535 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 23.138 / 22.478 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/6 / 425.577 / 417.596 m / -3.128820 / 12945.213796 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1506.797 / 1324.038 m / -51.074400 / 14357.622014 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage_seed2/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `hard_lineage_seed2/rl_checkpoint_01_eval.json`
- Training curve: `hard_lineage_seed2/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: 27.000985 / -49.078346
- Within-checkpoint reward change: -76.079331
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 590.662 / 17.126 m
- Fixed-eval mean episode reward: 38.040186
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -2.676760 / 2.690457
- Fixed-eval mean legacy episode reward: 27.240480
- Fixed-eval mean control effort: 35309.926110 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 36.512 / 34.719 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 9.251 / 6.433 m / 84.274732 / 40162.715813 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1753.483 / 1664.581 m / -54.428906 / 25604.346704 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage_seed2/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `hard_lineage_seed2/rl_checkpoint_02_eval.json`
- Training curve: `hard_lineage_seed2/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 16
- Episodes completed total: 48
- First/last quintile mean reward: -2.879914 / 0.052094
- Within-checkpoint reward change: +2.932007
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 556.587 / 9.876 m
- Fixed-eval mean episode reward: 38.897413
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -3.008298 / 3.879222
- Fixed-eval mean legacy episode reward: 29.237621
- Fixed-eval mean control effort: 47244.572760 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 38.951 / 34.795 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 6.564 / 5.160 m / 84.642221 / 50300.771595 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1656.633 / 1497.891 m / -52.592203 / 41132.175090 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage_seed2/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `hard_lineage_seed2/rl_checkpoint_03_eval.json`
- Training curve: `hard_lineage_seed2/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 81,920
- Episodes completed this checkpoint: 19
- Episodes completed total: 67
- First/last quintile mean reward: 61.681840 / 61.675660
- Within-checkpoint reward change: -0.006179
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 547.627 / 6.832 m
- Fixed-eval mean episode reward: 35.141791
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -7.091886 / 4.207188
- Fixed-eval mean legacy episode reward: 29.215101
- Fixed-eval mean control effort: 112354.652714 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 53.071 / 47.250 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 4.667 / 4.319 m / 78.650955 / 148053.634695 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1633.546 / 1440.601 m / -51.876537 / 40956.688751 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage_seed2/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `hard_lineage_seed2/rl_checkpoint_04_eval.json`
- Training curve: `hard_lineage_seed2/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 102,400
- Episodes completed this checkpoint: 17
- Episodes completed total: 84
- First/last quintile mean reward: 25.932490 / 44.432586
- Within-checkpoint reward change: +18.500096
- Fixed-eval hit rate: 4/9 (44.4%)
- Fixed-eval mean/median miss distance: 521.781 / 12.469 m
- Fixed-eval mean episode reward: 47.966485
- Fixed-eval mean reward components (shaping/effort/terminal): 38.026489 / -6.131348 / 16.071343
- Fixed-eval mean legacy episode reward: 52.416078
- Fixed-eval mean control effort: 113145.608993 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 57.229 / 45.770 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/4
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 4/6 / 6.620 / 3.759 m / 96.704342 / 148724.377667 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1552.102 / 1427.514 m / -49.509229 / 41988.071646 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `hard_lineage_seed2/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `hard_lineage_seed2/rl_checkpoint_05_eval.json`
- Training curve: `hard_lineage_seed2/training_curve.png`
