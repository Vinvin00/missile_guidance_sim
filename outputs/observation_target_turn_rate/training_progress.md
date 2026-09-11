# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 13 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, target_turn_rate_x_scaled, target_turn_rate_y_scaled, target_turn_rate_z_scaled`)
- use_target_turn_rate_obs: True
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
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -55.815498 / -76.815272
- Within-checkpoint reward change: -20.999774
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 1341.473 / 574.218 m
- Fixed-eval mean episode reward: -30.928991
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -0.413604 / -55.789297
- Fixed-eval mean legacy episode reward: -53.433268
- Fixed-eval mean control effort: 5606.512235 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 14.539 / 13.696 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/8/0
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/6 / 363.752 / 318.729 m / -9.413900 / 4761.572867 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 3296.915 / 2683.136 m / -73.959172 / 7296.390971 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `observation_target_turn_rate/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `observation_target_turn_rate/rl_checkpoint_01_eval.json`
- Training curve: `observation_target_turn_rate/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: -21.075020 / -39.479040
- Within-checkpoint reward change: -18.404020
- Fixed-eval hit rate: 1/9 (11.1%)
- Fixed-eval mean/median miss distance: 699.137 / 41.377 m
- Fixed-eval mean episode reward: -0.038341
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -3.902316 / -21.409935
- Fixed-eval mean legacy episode reward: -16.939560
- Fixed-eval mean control effort: 61073.672899 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 45.285 / 40.337 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/8/1
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 1/6 / 23.368 / 20.184 m / 35.436869 / 68019.807777 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 2050.674 / 1584.947 m / -70.988760 / 47181.403144 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `observation_target_turn_rate/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `observation_target_turn_rate/rl_checkpoint_02_eval.json`
- Training curve: `observation_target_turn_rate/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 16
- Episodes completed total: 48
- First/last quintile mean reward: -13.496463 / 82.131703
- Within-checkpoint reward change: +95.628166
- Fixed-eval hit rate: 4/9 (44.4%)
- Fixed-eval mean/median miss distance: 631.813 / 6.582 m
- Fixed-eval mean episode reward: 30.927631
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -9.384081 / 15.037803
- Fixed-eval mean legacy episode reward: 46.727063
- Fixed-eval mean control effort: 163406.856787 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 63.950 / 53.929 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/4
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 4/6 / 4.739 / 3.331 m / 80.459857 / 204916.974102 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1885.961 / 1259.335 m / -68.136821 / 80386.622158 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `observation_target_turn_rate/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `observation_target_turn_rate/rl_checkpoint_03_eval.json`
- Training curve: `observation_target_turn_rate/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 81,920
- Episodes completed this checkpoint: 16
- Episodes completed total: 64
- First/last quintile mean reward: 85.636255 / -12.111208
- Within-checkpoint reward change: -97.747463
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 539.666 / 6.540 m
- Fixed-eval mean episode reward: 17.256168
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -12.480054 / 4.462312
- Fixed-eval mean legacy episode reward: 23.454178
- Fixed-eval mean control effort: 245028.755158 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 80.420 / 62.297 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 5.004 / 5.376 m / 57.604107 / 346003.126561 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1608.991 / 1482.359 m / -63.439710 / 43080.012351 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `observation_target_turn_rate/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `observation_target_turn_rate/rl_checkpoint_04_eval.json`
- Training curve: `observation_target_turn_rate/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 102,400
- Episodes completed this checkpoint: 16
- Episodes completed total: 80
- First/last quintile mean reward: 42.514596 / 46.758200
- Within-checkpoint reward change: +4.243604
- Fixed-eval hit rate: 5/9 (55.6%)
- Fixed-eval mean/median miss distance: 535.810 / 4.117 m
- Fixed-eval mean episode reward: 44.359883
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -7.890627 / 26.976600
- Fixed-eval mean legacy episode reward: 71.888389
- Fixed-eval mean control effort: 172259.260424 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 68.480 / 52.644 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/4/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 5/6 / 3.850 / 3.653 m / 98.086397 / 236059.992646 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1599.731 / 1452.783 m / -63.093146 / 44657.795979 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `observation_target_turn_rate/rl_checkpoint_05_eval.json`
- Training curve: `observation_target_turn_rate/training_curve.png`
