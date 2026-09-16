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
- Episodes completed this checkpoint: 157
- Episodes completed total: 157
- First/last quintile mean reward: 84.042994 / 91.658240
- Within-checkpoint reward change: +7.615245
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.107 / 4.167 m
- Fixed-eval mean episode reward: 102.579888
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.083107 / 77.949765
- Fixed-eval mean legacy episode reward: 112.874034
- Fixed-eval mean control effort: 505558.155478 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 122.557 / 60.748 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/9/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw0/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `seed4_pw0/rl_checkpoint_07_eval.json`
- Training curve: `seed4_pw0/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 170
- Episodes completed total: 327
- First/last quintile mean reward: 114.491829 / 101.604565
- Within-checkpoint reward change: -12.887265
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 3.975 / 3.958 m
- Fixed-eval mean episode reward: 106.824022
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -11.850490 / 81.961282
- Fixed-eval mean legacy episode reward: 121.214218
- Fixed-eval mean control effort: 464625.248385 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 121.139 / 60.097 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `seed4_pw0/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `seed4_pw0/rl_checkpoint_08_eval.json`
- Training curve: `seed4_pw0/training_curve.png`
