# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 43500777
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 156
- Episodes completed total: 156
- First/last quintile mean reward: 85.333103 / 78.455812
- Within-checkpoint reward change: -6.877291
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.779 / 3.740 m
- Fixed-eval mean episode reward: 111.000543
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.681029 / 85.968342
- Fixed-eval mean legacy episode reward: 131.408315
- Fixed-eval mean control effort: 522284.667113 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.768 / 63.800 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/6/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed3_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed3_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 160
- Episodes completed total: 316
- First/last quintile mean reward: 88.325924 / 93.000806
- Within-checkpoint reward change: +4.674882
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.516 / 4.099 m
- Fixed-eval mean episode reward: 91.744571
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.903691 / 73.935031
- Fixed-eval mean legacy episode reward: 101.359619
- Fixed-eval mean control effort: 710173.874471 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 145.771 / 72.654 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/10/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed3_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed3_pw0/training_curve.png`
