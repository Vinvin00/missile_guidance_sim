# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 14142135
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 99
- Episodes completed total: 99
- First/last quintile mean reward: 1.537546 / 50.999154
- Within-checkpoint reward change: +49.461608
- Fixed-eval hit rate: 15/50 (30.0%)
- Fixed-eval mean/median miss distance: 10.389 / 7.378 m
- Fixed-eval mean episode reward: 47.663033
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.741344 / 29.691146
- Fixed-eval mean legacy episode reward: 17.874858
- Fixed-eval mean control effort: 390966.015569 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 92.168 / 69.644 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/29/15
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 105
- Episodes completed total: 204
- First/last quintile mean reward: 39.651545 / 28.682444
- Within-checkpoint reward change: -10.969101
- Fixed-eval hit rate: 15/50 (30.0%)
- Fixed-eval mean/median miss distance: 8.218 / 8.271 m
- Fixed-eval mean episode reward: 34.241189
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.237033 / 29.764992
- Fixed-eval mean legacy episode reward: 7.165041
- Fixed-eval mean control effort: 851090.911341 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 139.321 / 92.916 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/29/15
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 118
- Episodes completed total: 322
- First/last quintile mean reward: 38.099556 / 83.673627
- Within-checkpoint reward change: +45.574071
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.524 / 4.423 m
- Fixed-eval mean episode reward: 91.066210
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.581488 / 71.934468
- Fixed-eval mean legacy episode reward: 102.383752
- Fixed-eval mean control effort: 517522.218960 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 110.988 / 67.642 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/12/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 127
- Episodes completed total: 449
- First/last quintile mean reward: 45.937381 / 70.150556
- Within-checkpoint reward change: +24.213175
- Fixed-eval hit rate: 19/50 (38.0%)
- Fixed-eval mean/median miss distance: 6.965 / 5.606 m
- Fixed-eval mean episode reward: 39.036756
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -35.492684 / 37.816209
- Fixed-eval mean legacy episode reward: 19.904810
- Fixed-eval mean control effort: 1151216.415123 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 170.803 / 98.473 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/24/19
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 134
- Episodes completed total: 583
- First/last quintile mean reward: 68.129863 / 66.638539
- Within-checkpoint reward change: -1.491324
- Fixed-eval hit rate: 25/50 (50.0%)
- Fixed-eval mean/median miss distance: 6.035 / 4.973 m
- Fixed-eval mean episode reward: 51.210798
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -35.366593 / 49.864160
- Fixed-eval mean legacy episode reward: 45.744413
- Fixed-eval mean control effort: 1069347.624456 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 164.440 / 96.757 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/21/25
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 155
- Episodes completed total: 738
- First/last quintile mean reward: 91.553347 / 53.540614
- Within-checkpoint reward change: -38.012734
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.875 / 3.713 m
- Fixed-eval mean episode reward: 104.949672
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.726823 / 83.963265
- Fixed-eval mean legacy episode reward: 124.979735
- Fixed-eval mean control effort: 650529.601781 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 153.847 / 71.496 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/6/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed7/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed7/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed7/training_curve.png`
