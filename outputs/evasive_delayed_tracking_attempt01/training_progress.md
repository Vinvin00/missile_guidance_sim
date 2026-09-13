# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 8
- Episodes completed total: 8
- First/last quintile mean reward: -76.256729 / -69.257339
- Within-checkpoint reward change: +6.999390
- Fixed-eval hit rate: 0/50 (0.0%)
- Fixed-eval mean/median miss distance: 1231.089 / 1098.331 m
- Fixed-eval mean episode reward: -50.752238
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -0.502599 / -77.364237
- Fixed-eval mean legacy episode reward: -96.559682
- Fixed-eval mean control effort: 6106.903734 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 11.394 / 11.329 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/40/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_01_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 8
- Episodes completed total: 16
- First/last quintile mean reward: -56.221382 / -69.844017
- Within-checkpoint reward change: -13.622635
- Fixed-eval hit rate: 0/50 (0.0%)
- Fixed-eval mean/median miss distance: 1220.702 / 1296.503 m
- Fixed-eval mean episode reward: -52.720698
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -0.544620 / -79.290676
- Fixed-eval mean legacy episode reward: -93.721566
- Fixed-eval mean control effort: 7259.613653 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 12.613 / 12.042 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/40/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_02_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 8
- Episodes completed total: 24
- First/last quintile mean reward: -55.738487 / -76.746811
- Within-checkpoint reward change: -21.008324
- Fixed-eval hit rate: 0/50 (0.0%)
- Fixed-eval mean/median miss distance: 4110.202 / 4227.046 m
- Fixed-eval mean episode reward: -80.903723
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -8.112191 / -99.906131
- Fixed-eval mean legacy episode reward: -102.775970
- Fixed-eval mean control effort: 278880.345372 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 79.478 / 47.042 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/40/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_03_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 81,920
- Episodes completed this checkpoint: 8
- Episodes completed total: 32
- First/last quintile mean reward: -74.303833 / -79.121216
- Within-checkpoint reward change: -4.817383
- Fixed-eval hit rate: 0/50 (0.0%)
- Fixed-eval mean/median miss distance: 3988.849 / 4027.889 m
- Fixed-eval mean episode reward: -76.939612
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -4.166855 / -99.887356
- Fixed-eval mean legacy episode reward: -103.678821
- Fixed-eval mean control effort: 249286.181361 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 75.161 / 33.710 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/40/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_04_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 102,400
- Episodes completed this checkpoint: 8
- Episodes completed total: 40
- First/last quintile mean reward: -86.146759 / -74.330208
- Within-checkpoint reward change: +11.816551
- Fixed-eval hit rate: 0/50 (0.0%)
- Fixed-eval mean/median miss distance: 4671.812 / 4693.273 m
- Fixed-eval mean episode reward: -79.717290
- Fixed-eval mean reward components (shaping/effort/terminal): 27.114598 / -6.859787 / -99.972101
- Fixed-eval mean legacy episode reward: -117.760361
- Fixed-eval mean control effort: 801640.530528 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.809 / 43.269 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 10/40/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_delayed_tracking/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_delayed_tracking/rl_checkpoint_05_eval.json`
- Training curve: `evasive_delayed_tracking/training_curve.png`
