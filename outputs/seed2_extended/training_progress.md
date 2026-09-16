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
- Episodes completed this checkpoint: 140
- Episodes completed total: 140
- First/last quintile mean reward: 118.877894 / 95.765969
- Within-checkpoint reward change: -23.111925
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 5.492 / 4.670 m
- Fixed-eval mean episode reward: 106.771206
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.840815 / 92.898791
- Fixed-eval mean legacy episode reward: 89.532429
- Fixed-eval mean control effort: 1015759.248334 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 190.858 / 89.812 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/11/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_extended/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed2_extended/rl_checkpoint_07_eval.json`
- Training curve: `seed2_extended/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 144
- Episodes completed total: 284
- First/last quintile mean reward: 79.984799 / 90.407221
- Within-checkpoint reward change: +10.422422
- Fixed-eval hit rate: 36/50 (72.0%)
- Fixed-eval mean/median miss distance: 4.973 / 4.477 m
- Fixed-eval mean episode reward: 111.463516
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -20.973133 / 95.723419
- Fixed-eval mean legacy episode reward: 97.511654
- Fixed-eval mean control effort: 805907.783525 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 161.690 / 81.750 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/11/36
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_extended/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed2_extended/rl_checkpoint_08_eval.json`
- Training curve: `seed2_extended/training_curve.png`

## Checkpoint 9

- Cumulative timesteps: 1,843,200
- Episodes completed this checkpoint: 141
- Episodes completed total: 425
- First/last quintile mean reward: 128.626130 / 104.339729
- Within-checkpoint reward change: -24.286401
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.389 / 4.061 m
- Fixed-eval mean episode reward: 127.899021
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.046465 / 106.232256
- Fixed-eval mean legacy episode reward: 117.900328
- Fixed-eval mean control effort: 624353.699971 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 150.278 / 73.648 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/6/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_extended/checkpoints/rl_checkpoint_09.zip`
- Evaluation details: `seed2_extended/rl_checkpoint_09_eval.json`
- Training curve: `seed2_extended/training_curve.png`

## Checkpoint 10

- Cumulative timesteps: 2,048,000
- Episodes completed this checkpoint: 152
- Episodes completed total: 577
- First/last quintile mean reward: 92.735343 / 129.366291
- Within-checkpoint reward change: +36.630948
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.266 / 3.998 m
- Fixed-eval mean episode reward: 119.957165
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.097855 / 101.341790
- Fixed-eval mean legacy episode reward: 103.711234
- Fixed-eval mean control effort: 695153.877492 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 147.387 / 73.096 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed2_extended/checkpoints/rl_checkpoint_10.zip`
- Evaluation details: `seed2_extended/rl_checkpoint_10_eval.json`
- Training curve: `seed2_extended/training_curve.png`
