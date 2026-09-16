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
- Episodes completed this checkpoint: 166
- Episodes completed total: 166
- First/last quintile mean reward: 95.736116 / 106.058796
- Within-checkpoint reward change: +10.322680
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.517 / 3.294 m
- Fixed-eval mean episode reward: 110.635646
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.046065 / 85.968480
- Fixed-eval mean legacy episode reward: 131.652423
- Fixed-eval mean control effort: 533617.042748 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 143.934 / 66.676 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/4/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed3_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed3_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 162
- Episodes completed total: 328
- First/last quintile mean reward: 106.146209 / 108.524775
- Within-checkpoint reward change: +2.378566
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.259 / 4.210 m
- Fixed-eval mean episode reward: 104.312468
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.359411 / 81.958649
- Fixed-eval mean legacy episode reward: 121.442635
- Fixed-eval mean control effort: 576075.070023 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 139.085 / 67.501 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed3_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed3_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed3_pw0/training_curve.png`
