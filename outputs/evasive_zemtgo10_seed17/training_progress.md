# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 2236067977
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 98
- Episodes completed total: 98
- First/last quintile mean reward: -9.146500 / 41.335346
- Within-checkpoint reward change: +50.481846
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 10.074 / 8.855 m
- Fixed-eval mean episode reward: 39.353611
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -25.058431 / 27.698811
- Fixed-eval mean legacy episode reward: 4.644098
- Fixed-eval mean control effort: 488310.270801 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 103.880 / 81.296 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/28/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed17/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed17/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed17/training_curve.png`
