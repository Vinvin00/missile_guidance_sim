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
- Episodes completed this checkpoint: 167
- Episodes completed total: 167
- First/last quintile mean reward: 105.656250 / 151.778941
- Within-checkpoint reward change: +46.122690
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.146 / 4.129 m
- Fixed-eval mean episode reward: 135.057137
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -13.438339 / 111.782245
- Fixed-eval mean legacy episode reward: 122.874020
- Fixed-eval mean control effort: 565532.395073 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 142.645 / 67.634 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/6/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed3_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed3_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 165
- Episodes completed total: 332
- First/last quintile mean reward: 108.328764 / 136.078928
- Within-checkpoint reward change: +27.750164
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 3.999 / 3.702 m
- Fixed-eval mean episode reward: 136.731466
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.522995 / 112.541231
- Fixed-eval mean legacy episode reward: 121.383767
- Fixed-eval mean control effort: 606091.572115 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 146.264 / 65.011 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/6/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed3_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed3_pw50/training_curve.png`
