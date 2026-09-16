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
- Episodes completed this checkpoint: 153
- Episodes completed total: 153
- First/last quintile mean reward: 110.610830 / 107.068302
- Within-checkpoint reward change: -3.542528
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.991 / 3.973 m
- Fixed-eval mean episode reward: 135.714525
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.418776 / 111.420070
- Fixed-eval mean legacy episode reward: 126.962943
- Fixed-eval mean control effort: 548172.851264 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 141.237 / 64.832 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/6/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed4_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed4_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 148
- Episodes completed total: 301
- First/last quintile mean reward: 95.543678 / 111.265039
- Within-checkpoint reward change: +15.721361
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.186 / 3.971 m
- Fixed-eval mean episode reward: 130.111787
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.738080 / 109.136636
- Fixed-eval mean legacy episode reward: 112.582223
- Fixed-eval mean control effort: 834939.454073 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 179.269 / 74.932 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/8/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed4_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed4_pw50/training_curve.png`
