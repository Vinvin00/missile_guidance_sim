# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 31415926
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 175
- Episodes completed total: 175
- First/last quintile mean reward: 121.444097 / 123.220881
- Within-checkpoint reward change: +1.776785
- Fixed-eval hit rate: 47/50 (94.0%)
- Fixed-eval mean/median miss distance: 3.383 / 3.098 m
- Fixed-eval mean episode reward: 157.854821
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -9.019101 / 130.160692
- Fixed-eval mean legacy episode reward: 145.229403
- Fixed-eval mean control effort: 770711.049349 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 191.006 / 65.614 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/2/47
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed6_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed6_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed6_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 181
- Episodes completed total: 356
- First/last quintile mean reward: 160.973386 / 122.422296
- Within-checkpoint reward change: -38.551090
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.522 / 3.284 m
- Fixed-eval mean episode reward: 144.629227
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.210771 / 120.126767
- Fixed-eval mean legacy episode reward: 128.411123
- Fixed-eval mean control effort: 681823.307859 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 162.738 / 66.534 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/5/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed6_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed6_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed6_pw50/training_curve.png`
