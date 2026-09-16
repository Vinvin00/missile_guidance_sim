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
- Episodes completed this checkpoint: 136
- Episodes completed total: 136
- First/last quintile mean reward: 99.433389 / 32.526271
- Within-checkpoint reward change: -66.907118
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.445 / 4.319 m
- Fixed-eval mean episode reward: 97.978564
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.683618 / 77.948951
- Fixed-eval mean legacy episode reward: 110.785620
- Fixed-eval mean control effort: 767753.425283 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 167.941 / 77.252 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/9/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed2_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed2_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 143
- Episodes completed total: 279
- First/last quintile mean reward: 80.015948 / 105.288960
- Within-checkpoint reward change: +25.273012
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.700 / 4.387 m
- Fixed-eval mean episode reward: 91.315154
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.332014 / 71.933938
- Fixed-eval mean legacy episode reward: 99.363313
- Fixed-eval mean control effort: 712900.050714 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 148.093 / 73.231 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/11/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed2_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed2_pw0/training_curve.png`
