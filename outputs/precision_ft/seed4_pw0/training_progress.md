# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 61803399
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 146
- Episodes completed total: 146
- First/last quintile mean reward: 71.591043 / 78.552945
- Within-checkpoint reward change: +6.961902
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.602 / 4.364 m
- Fixed-eval mean episode reward: 92.607081
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.039871 / 71.933721
- Fixed-eval mean legacy episode reward: 98.434965
- Fixed-eval mean control effort: 773668.550282 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 157.655 / 71.952 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/11/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed4_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed4_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 136
- Episodes completed total: 282
- First/last quintile mean reward: 88.283160 / 70.111828
- Within-checkpoint reward change: -18.171332
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.464 / 4.083 m
- Fixed-eval mean episode reward: 89.245352
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -21.409673 / 73.941795
- Fixed-eval mean legacy episode reward: 99.833017
- Fixed-eval mean control effort: 876371.068602 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 174.072 / 81.425 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed4_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed4_pw0/training_curve.png`
