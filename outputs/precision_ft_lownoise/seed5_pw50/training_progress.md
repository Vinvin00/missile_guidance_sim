# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 27182818
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 162
- Episodes completed total: 162
- First/last quintile mean reward: 127.422237 / 119.328941
- Within-checkpoint reward change: -8.093295
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 4.062 / 3.954 m
- Fixed-eval mean episode reward: 141.319300
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.343937 / 115.950007
- Fixed-eval mean legacy episode reward: 129.983446
- Fixed-eval mean control effort: 606774.447473 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.568 / 65.785 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/5/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed5_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed5_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed5_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 326
- First/last quintile mean reward: 141.809578 / 106.258959
- Within-checkpoint reward change: -35.550619
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.349 / 4.287 m
- Fixed-eval mean episode reward: 135.887467
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.254466 / 111.428703
- Fixed-eval mean legacy episode reward: 121.645580
- Fixed-eval mean control effort: 642938.829104 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 153.524 / 66.653 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed5_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed5_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed5_pw50/training_curve.png`
