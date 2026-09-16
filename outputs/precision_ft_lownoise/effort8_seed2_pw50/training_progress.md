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
- First/last quintile mean reward: 112.145663 / 120.995812
- Within-checkpoint reward change: +8.850149
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.216 / 4.117 m
- Fixed-eval mean episode reward: 124.092084
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.774275 / 111.153129
- Fixed-eval mean legacy episode reward: 120.815064
- Fixed-eval mean control effort: 728273.943398 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 165.740 / 74.173 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
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
- First/last quintile mean reward: 101.490365 / 128.357046
- Within-checkpoint reward change: +26.866682
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 3.946 / 3.807 m
- Fixed-eval mean episode reward: 126.095921
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.108470 / 112.491161
- Fixed-eval mean legacy episode reward: 120.998410
- Fixed-eval mean control effort: 704545.074226 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 161.790 / 71.416 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `effort8_seed2_pw50/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `effort8_seed2_pw50/rl_checkpoint_08_eval.json`
- Training curve: `effort8_seed2_pw50/training_curve.png`
