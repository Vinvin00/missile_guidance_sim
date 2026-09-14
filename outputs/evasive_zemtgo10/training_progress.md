# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 99
- Episodes completed total: 99
- First/last quintile mean reward: -1.902237 / 21.813235
- Within-checkpoint reward change: +23.715472
- Fixed-eval hit rate: 8/50 (16.0%)
- Fixed-eval mean/median miss distance: 13.567 / 10.209 m
- Fixed-eval mean episode reward: 16.352259
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -35.931779 / 15.570808
- Fixed-eval mean legacy episode reward: -20.492295
- Fixed-eval mean control effort: 862937.587157 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 138.253 / 97.485 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 11/31/8
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 104
- Episodes completed total: 203
- First/last quintile mean reward: 51.104666 / 45.238339
- Within-checkpoint reward change: -5.866327
- Fixed-eval hit rate: 6/50 (12.0%)
- Fixed-eval mean/median miss distance: 10.879 / 9.162 m
- Fixed-eval mean episode reward: 10.673803
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -37.694159 / 11.654731
- Fixed-eval mean legacy episode reward: -35.376399
- Fixed-eval mean control effort: 1147439.820969 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 159.988 / 99.474 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/37/6
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 104
- Episodes completed total: 307
- First/last quintile mean reward: 28.603581 / 27.019576
- Within-checkpoint reward change: -1.584005
- Fixed-eval hit rate: 21/50 (42.0%)
- Fixed-eval mean/median miss distance: 6.545 / 5.200 m
- Fixed-eval mean episode reward: 51.595021
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.952642 / 41.834432
- Fixed-eval mean legacy episode reward: 31.881128
- Fixed-eval mean control effort: 865970.892660 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 140.582 / 85.237 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/23/21
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 110
- Episodes completed total: 417
- First/last quintile mean reward: 45.204499 / -22.573028
- Within-checkpoint reward change: -67.777527
- Fixed-eval hit rate: 6/50 (12.0%)
- Fixed-eval mean/median miss distance: 12.057 / 10.571 m
- Fixed-eval mean episode reward: -26.811090
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -75.138588 / 11.614268
- Fixed-eval mean legacy episode reward: -49.189408
- Fixed-eval mean control effort: 2061643.064790 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 223.569 / 147.509 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/35/6
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 120
- Episodes completed total: 537
- First/last quintile mean reward: 26.461099 / 70.524387
- Within-checkpoint reward change: +44.063288
- Fixed-eval hit rate: 26/50 (52.0%)
- Fixed-eval mean/median miss distance: 7.992 / 4.758 m
- Fixed-eval mean episode reward: 56.195083
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.316176 / 51.798029
- Fixed-eval mean legacy episode reward: 49.447817
- Fixed-eval mean control effort: 1067235.186808 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 174.695 / 98.292 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/21/26
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10/training_curve.png`
