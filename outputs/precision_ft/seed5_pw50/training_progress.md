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
- Episodes completed this checkpoint: 150
- Episodes completed total: 150
- First/last quintile mean reward: 117.396771 / 107.565405
- Within-checkpoint reward change: -9.831366
- Fixed-eval hit rate: 38/50 (76.0%)
- Fixed-eval mean/median miss distance: 4.761 / 4.332 m
- Fixed-eval mean episode reward: 123.567800
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.725269 / 104.579838
- Fixed-eval mean legacy episode reward: 105.067501
- Fixed-eval mean control effort: 737686.528230 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 149.331 / 70.636 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/9/38
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed5_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed5_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed5_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 173
- Episodes completed total: 323
- First/last quintile mean reward: 124.439540 / 138.157176
- Within-checkpoint reward change: +13.717636
- Fixed-eval hit rate: 45/50 (90.0%)
- Fixed-eval mean/median miss distance: 3.624 / 3.385 m
- Fixed-eval mean episode reward: 152.745158
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -8.681882 / 124.713810
- Fixed-eval mean legacy episode reward: 141.396031
- Fixed-eval mean control effort: 474178.901581 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 137.638 / 58.867 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/3/45
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed5_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed5_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed5_pw50/training_curve.png`
