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
- Episodes completed this checkpoint: 154
- Episodes completed total: 154
- First/last quintile mean reward: 95.126790 / 94.752876
- Within-checkpoint reward change: -0.373914
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 4.299 / 3.783 m
- Fixed-eval mean episode reward: 106.204516
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.460101 / 83.951387
- Fixed-eval mean legacy episode reward: 124.874369
- Fixed-eval mean control effort: 695430.321665 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 168.500 / 73.056 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/5/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed2_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed2_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 145
- Episodes completed total: 299
- First/last quintile mean reward: 85.808419 / 96.646815
- Within-checkpoint reward change: +10.838396
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.202 / 3.684 m
- Fixed-eval mean episode reward: 102.392925
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.270105 / 79.949800
- Fixed-eval mean legacy episode reward: 116.657747
- Fixed-eval mean control effort: 641696.983104 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 150.981 / 68.054 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/8/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed2_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed2_pw0/training_curve.png`
