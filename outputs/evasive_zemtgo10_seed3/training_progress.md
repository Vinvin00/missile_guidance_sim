# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 43500777
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 97
- Episodes completed total: 97
- First/last quintile mean reward: -17.120566 / 29.247653
- Within-checkpoint reward change: +46.368219
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 9.876 / 7.898 m
- Fixed-eval mean episode reward: 27.731940
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -36.687787 / 27.706497
- Fixed-eval mean legacy episode reward: 11.405954
- Fixed-eval mean control effort: 756710.099597 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 123.099 / 93.230 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/28/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 96
- Episodes completed total: 193
- First/last quintile mean reward: 5.876174 / 17.864886
- Within-checkpoint reward change: +11.988711
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 14.269 / 13.819 m
- Fixed-eval mean episode reward: -12.571451
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -52.814242 / 3.529560
- Fixed-eval mean legacy episode reward: -52.640963
- Fixed-eval mean control effort: 1372639.689558 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 176.462 / 118.901 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 11/37/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 106
- Episodes completed total: 299
- First/last quintile mean reward: 47.747669 / 35.556543
- Within-checkpoint reward change: -12.191126
- Fixed-eval hit rate: 10/50 (20.0%)
- Fixed-eval mean/median miss distance: 8.822 / 8.548 m
- Fixed-eval mean episode reward: 16.090491
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -40.356363 / 19.733624
- Fixed-eval mean legacy episode reward: -17.680109
- Fixed-eval mean control effort: 1025463.480499 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.918 / 102.371 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 11/29/10
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 113
- Episodes completed total: 412
- First/last quintile mean reward: 49.886790 / 25.160937
- Within-checkpoint reward change: -24.725852
- Fixed-eval hit rate: 12/50 (24.0%)
- Fixed-eval mean/median miss distance: 8.341 / 6.954 m
- Fixed-eval mean episode reward: 18.103699
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -42.367072 / 23.757540
- Fixed-eval mean legacy episode reward: -17.146991
- Fixed-eval mean control effort: 1374675.351846 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 182.152 / 108.030 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/30/12
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 141
- Episodes completed total: 553
- First/last quintile mean reward: 65.449707 / 92.288860
- Within-checkpoint reward change: +26.839153
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.447 / 3.973 m
- Fixed-eval mean episode reward: 91.532219
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.117832 / 73.936820
- Fixed-eval mean legacy episode reward: 101.936258
- Fixed-eval mean control effort: 734805.910255 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 153.468 / 76.393 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 150
- Episodes completed total: 703
- First/last quintile mean reward: 80.038903 / 87.619080
- Within-checkpoint reward change: +7.580177
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.094 / 3.929 m
- Fixed-eval mean episode reward: 103.939416
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.732307 / 81.958492
- Fixed-eval mean legacy episode reward: 121.220738
- Fixed-eval mean control effort: 615507.308660 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 144.864 / 67.746 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed3/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed3/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed3/training_curve.png`
