# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 77000001
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 146
- Episodes completed total: 146
- First/last quintile mean reward: 119.044594 / 111.106520
- Within-checkpoint reward change: -7.938074
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.273 / 4.011 m
- Fixed-eval mean episode reward: 127.324673
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.027381 / 105.638824
- Fixed-eval mean legacy episode reward: 113.362580
- Fixed-eval mean control effort: 619706.346425 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 143.403 / 69.825 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/9/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed2_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed2_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 156
- Episodes completed total: 302
- First/last quintile mean reward: 102.988208 / 94.856049
- Within-checkpoint reward change: -8.132159
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 4.356 / 3.953 m
- Fixed-eval mean episode reward: 134.944579
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -13.532517 / 111.763865
- Fixed-eval mean legacy episode reward: 123.974534
- Fixed-eval mean control effort: 778789.635759 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 181.323 / 76.039 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/4/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed2_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed2_pw50/training_curve.png`
