# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 102
- Episodes completed total: 102
- First/last quintile mean reward: 436.086305 / 270.088899
- Within-checkpoint reward change: -165.997406
- Fixed-eval hit rate: 22/50 (44.0%)
- Fixed-eval mean/median miss distance: 7.748 / 5.371 m
- Fixed-eval mean episode reward: 224.995829
- Fixed-eval mean reward components (shaping/effort/terminal): 195.423158 / -14.226161 / 43.798832
- Fixed-eval mean legacy episode reward: 39.429678
- Fixed-eval mean control effort: 476242.706039 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 102.833 / 63.780 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 15/13/22
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_shapinggamma/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_shapinggamma/rl_checkpoint_01_eval.json`
- Training curve: `evasive_shapinggamma/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 108
- Episodes completed total: 210
- First/last quintile mean reward: 254.480932 / 285.217666
- Within-checkpoint reward change: +30.736734
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 11.935 / 11.555 m
- Fixed-eval mean episode reward: 262.362574
- Fixed-eval mean reward components (shaping/effort/terminal): 283.141879 / -24.387057 / 3.607752
- Fixed-eval mean legacy episode reward: -63.028436
- Fixed-eval mean control effort: 1060640.842675 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 157.131 / 81.923 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 20/28/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_shapinggamma/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_shapinggamma/rl_checkpoint_02_eval.json`
- Training curve: `evasive_shapinggamma/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 106
- Episodes completed total: 316
- First/last quintile mean reward: 268.313733 / 241.467675
- Within-checkpoint reward change: -26.846059
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 7.887 / 7.106 m
- Fixed-eval mean episode reward: 231.428180
- Fixed-eval mean reward components (shaping/effort/terminal): 222.522683 / -18.871490 / 27.776986
- Fixed-eval mean legacy episode reward: -8.275589
- Fixed-eval mean control effort: 900446.434794 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 152.689 / 76.795 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 20/16/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_shapinggamma/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_shapinggamma/rl_checkpoint_03_eval.json`
- Training curve: `evasive_shapinggamma/training_curve.png`
