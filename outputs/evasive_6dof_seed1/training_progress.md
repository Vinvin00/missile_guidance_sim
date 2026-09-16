# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Pursuer plant: 6dof
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 92
- Episodes completed total: 92
- First/last quintile mean reward: -18.560980 / 0.189320
- Within-checkpoint reward change: +18.750299
- Fixed-eval hit rate: 22/50 (44.0%)
- Fixed-eval mean/median miss distance: 150.918 / 5.734 m
- Fixed-eval mean episode reward: 72.952712
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -2.894307 / 39.133789
- Fixed-eval mean legacy episode reward: 40.316264
- Fixed-eval mean control effort: 288316.958503 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 71.228 / 30.865 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/27/22
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_6dof_seed1/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_6dof_seed1/rl_checkpoint_01_eval.json`
- Training curve: `evasive_6dof_seed1/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 92
- Episodes completed total: 184
- First/last quintile mean reward: -6.626013 / -12.815825
- Within-checkpoint reward change: -6.189812
- Fixed-eval hit rate: 2/50 (4.0%)
- Fixed-eval mean/median miss distance: 250.362 / 91.892 m
- Fixed-eval mean episode reward: 27.654528
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -4.982421 / -4.076281
- Fixed-eval mean legacy episode reward: -59.598575
- Fixed-eval mean control effort: 839644.098672 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.237 / 36.303 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/39/2
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_6dof_seed1/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_6dof_seed1/rl_checkpoint_02_eval.json`
- Training curve: `evasive_6dof_seed1/training_curve.png`
