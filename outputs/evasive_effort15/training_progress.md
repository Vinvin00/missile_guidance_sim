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
- Episodes completed this checkpoint: 101
- Episodes completed total: 101
- First/last quintile mean reward: 380.853130 / 265.771162
- Within-checkpoint reward change: -115.081967
- Fixed-eval hit rate: 1/50 (2.0%)
- Fixed-eval mean/median miss distance: 12.339 / 11.485 m
- Fixed-eval mean episode reward: 241.960528
- Fixed-eval mean reward components (shaping/effort/terminal): 303.469732 / -63.099285 / 1.590080
- Fixed-eval mean legacy episode reward: -56.421815
- Fixed-eval mean control effort: 420082.548471 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 97.528 / 76.046 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 22/27/1
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_effort15/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_effort15/rl_checkpoint_01_eval.json`
- Training curve: `evasive_effort15/training_curve.png`
