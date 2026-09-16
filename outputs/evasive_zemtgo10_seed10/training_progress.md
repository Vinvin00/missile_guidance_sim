# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 987654321
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 100
- Episodes completed total: 100
- First/last quintile mean reward: -22.176692 / 22.876864
- Within-checkpoint reward change: +45.053556
- Fixed-eval hit rate: 8/50 (16.0%)
- Fixed-eval mean/median miss distance: 11.517 / 11.016 m
- Fixed-eval mean episode reward: 1.943288
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -50.406007 / 15.636065
- Fixed-eval mean legacy episode reward: -21.636591
- Fixed-eval mean control effort: 1244187.527660 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 166.952 / 113.431 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/33/8
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 101
- Episodes completed total: 201
- First/last quintile mean reward: 11.655119 / 10.390521
- Within-checkpoint reward change: -1.264598
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 8.885 / 6.518 m
- Fixed-eval mean episode reward: 24.442088
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -40.010609 / 27.739466
- Fixed-eval mean legacy episode reward: 1.352245
- Fixed-eval mean control effort: 1043948.913109 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.398 / 98.881 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/28/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 119
- Episodes completed total: 320
- First/last quintile mean reward: 26.858005 / 43.368315
- Within-checkpoint reward change: +16.510310
- Fixed-eval hit rate: 24/50 (48.0%)
- Fixed-eval mean/median miss distance: 6.494 / 5.037 m
- Fixed-eval mean episode reward: 50.533041
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -34.024605 / 47.844416
- Fixed-eval mean legacy episode reward: 47.212946
- Fixed-eval mean control effort: 901762.701450 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 145.364 / 93.264 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/20/24
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 137
- Episodes completed total: 457
- First/last quintile mean reward: 66.451474 / 87.284817
- Within-checkpoint reward change: +20.833343
- Fixed-eval hit rate: 27/50 (54.0%)
- Fixed-eval mean/median miss distance: 5.767 / 4.647 m
- Fixed-eval mean episode reward: 56.735478
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -33.853405 / 53.875653
- Fixed-eval mean legacy episode reward: 56.000886
- Fixed-eval mean control effort: 1045750.000933 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 165.417 / 94.141 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/21/27
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 147
- Episodes completed total: 604
- First/last quintile mean reward: 76.500803 / 62.815385
- Within-checkpoint reward change: -13.685418
- Fixed-eval hit rate: 33/50 (66.0%)
- Fixed-eval mean/median miss distance: 5.185 / 4.600 m
- Fixed-eval mean episode reward: 73.201221
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -29.425770 / 65.913760
- Fixed-eval mean legacy episode reward: 82.612127
- Fixed-eval mean control effort: 1003339.434405 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 172.447 / 89.707 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/16/33
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 151
- Episodes completed total: 755
- First/last quintile mean reward: 88.263129 / 73.675237
- Within-checkpoint reward change: -14.587892
- Fixed-eval hit rate: 33/50 (66.0%)
- Fixed-eval mean/median miss distance: 5.076 / 4.635 m
- Fixed-eval mean episode reward: 80.369360
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.254999 / 65.911129
- Fixed-eval mean legacy episode reward: 85.106792
- Fixed-eval mean control effort: 825161.658829 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 154.905 / 79.956 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/16/33
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 139
- Episodes completed total: 894
- First/last quintile mean reward: 98.701429 / 96.035692
- Within-checkpoint reward change: -2.665737
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.430 / 4.298 m
- Fixed-eval mean episode reward: 133.756937
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.634346 / 109.678053
- Fixed-eval mean legacy episode reward: 121.857549
- Fixed-eval mean control effort: 646666.906840 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 149.816 / 66.946 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/8/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 151
- Episodes completed total: 1045
- First/last quintile mean reward: 112.882848 / 105.147868
- Within-checkpoint reward change: -7.734980
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.132 / 4.021 m
- Fixed-eval mean episode reward: 125.189265
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.661335 / 106.137370
- Fixed-eval mean legacy episode reward: 112.980701
- Fixed-eval mean control effort: 691591.742840 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.978 / 72.792 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/10/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed10/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed10/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed10/training_curve.png`
