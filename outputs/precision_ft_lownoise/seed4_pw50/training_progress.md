# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 61803399
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 153
- Episodes completed total: 153
- First/last quintile mean reward: 94.005827 / 132.651740
- Within-checkpoint reward change: +38.645913
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.697 / 4.047 m
- Fixed-eval mean episode reward: 122.518031
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -16.765764 / 102.570564
- Fixed-eval mean legacy episode reward: 102.885498
- Fixed-eval mean control effort: 565076.055325 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 127.012 / 69.372 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/11/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed4_pw50/rl_checkpoint_07_eval.json`
- Training curve: `seed4_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 317
- First/last quintile mean reward: 142.058735 / 125.358846
- Within-checkpoint reward change: -16.699889
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 3.858 / 3.994 m
- Fixed-eval mean episode reward: 148.221513
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -9.210505 / 120.718787
- Fixed-eval mean legacy episode reward: 136.471241
- Fixed-eval mean control effort: 357278.360798 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 110.915 / 55.975 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/4/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed4_pw50/rl_checkpoint_08_eval.json`
- Training curve: `seed4_pw50/training_curve.png`
