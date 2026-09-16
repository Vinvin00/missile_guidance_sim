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
- Episodes completed this checkpoint: 93
- Episodes completed total: 93
- First/last quintile mean reward: -82.695775 / -5.088920
- Within-checkpoint reward change: +77.606855
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 10.705 / 6.998 m
- Fixed-eval mean episode reward: 29.050187
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -8.040673 / 9.976262
- Fixed-eval mean legacy episode reward: -13.245335
- Fixed-eval mean control effort: 178700.342083 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 64.840 / 47.929 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/29/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_misstanh50/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_misstanh50/rl_checkpoint_01_eval.json`
- Training curve: `evasive_misstanh50/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 102
- Episodes completed total: 195
- First/last quintile mean reward: 13.811366 / 13.632406
- Within-checkpoint reward change: -0.178961
- Fixed-eval hit rate: 4/50 (8.0%)
- Fixed-eval mean/median miss distance: 13.023 / 11.874 m
- Fixed-eval mean episode reward: -35.555627
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -46.673334 / -15.996891
- Fixed-eval mean legacy episode reward: -51.024813
- Fixed-eval mean control effort: 1250277.710407 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 170.789 / 114.575 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/36/4
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_misstanh50/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_misstanh50/rl_checkpoint_02_eval.json`
- Training curve: `evasive_misstanh50/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 108
- Episodes completed total: 303
- First/last quintile mean reward: 8.035178 / 3.940079
- Within-checkpoint reward change: -4.095099
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 14.293 / 12.480 m
- Fixed-eval mean episode reward: -42.932675
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -47.113232 / -22.934041
- Fixed-eval mean legacy episode reward: -58.523492
- Fixed-eval mean control effort: 1185676.149239 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 164.124 / 112.337 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 12/36/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_misstanh50/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_misstanh50/rl_checkpoint_03_eval.json`
- Training curve: `evasive_misstanh50/training_curve.png`
