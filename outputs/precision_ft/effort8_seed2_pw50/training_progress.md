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
- Episodes completed this checkpoint: 164
- Episodes completed total: 164
- First/last quintile mean reward: 121.799875 / 105.779101
- Within-checkpoint reward change: -16.020774
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.241 / 4.026 m
- Fixed-eval mean episode reward: 120.476618
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.972330 / 110.735717
- Fixed-eval mean legacy episode reward: 116.870338
- Fixed-eval mean control effort: 684643.219123 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 152.118 / 72.281 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/9/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `effort8_seed2_pw50/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `effort8_seed2_pw50/rl_checkpoint_07_eval.json`
- Training curve: `effort8_seed2_pw50/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 328
- First/last quintile mean reward: 112.306041 / 77.878301
- Within-checkpoint reward change: -34.427740
- Fixed-eval hit rate: 47/50 (94.0%)
- Fixed-eval mean/median miss distance: 3.520 / 3.581 m
- Fixed-eval mean episode reward: 154.324017
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.494773 / 129.105559
- Fixed-eval mean legacy episode reward: 151.816375
- Fixed-eval mean control effort: 351942.067076 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 118.898 / 56.007 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/2/47
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `effort8_seed2_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `effort8_seed2_pw50/rl_checkpoint_08_eval.json`
- Training curve: `effort8_seed2_pw50/training_curve.png`
