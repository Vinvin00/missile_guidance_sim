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

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 98
- Episodes completed total: 98
- First/last quintile mean reward: -2.735683 / 20.577226
- Within-checkpoint reward change: +23.312909
- Fixed-eval hit rate: 7/50 (14.0%)
- Fixed-eval mean/median miss distance: 12.189 / 10.696 m
- Fixed-eval mean episode reward: 5.407241
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -44.916524 / 13.610534
- Fixed-eval mean legacy episode reward: -23.260904
- Fixed-eval mean control effort: 731162.536294 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 126.455 / 86.390 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/34/7
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 104
- Episodes completed total: 202
- First/last quintile mean reward: 24.618300 / 20.987386
- Within-checkpoint reward change: -3.630915
- Fixed-eval hit rate: 8/50 (16.0%)
- Fixed-eval mean/median miss distance: 9.183 / 8.247 m
- Fixed-eval mean episode reward: -0.160521
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -52.589336 / 15.715584
- Fixed-eval mean legacy episode reward: -19.140186
- Fixed-eval mean control effort: 792700.885357 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.018 / 93.851 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 11/31/8
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 109
- Episodes completed total: 311
- First/last quintile mean reward: 19.755434 / 21.073882
- Within-checkpoint reward change: +1.318448
- Fixed-eval hit rate: 20/50 (40.0%)
- Fixed-eval mean/median miss distance: 6.945 / 6.103 m
- Fixed-eval mean episode reward: 28.391543
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -48.145476 / 39.823789
- Fixed-eval mean legacy episode reward: 30.184874
- Fixed-eval mean control effort: 800424.357340 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.134 / 88.407 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/23/20
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 116
- Episodes completed total: 427
- First/last quintile mean reward: 51.779525 / 42.258561
- Within-checkpoint reward change: -9.520964
- Fixed-eval hit rate: 34/50 (68.0%)
- Fixed-eval mean/median miss distance: 5.153 / 4.550 m
- Fixed-eval mean episode reward: 68.915326
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -35.715488 / 67.917584
- Fixed-eval mean legacy episode reward: 93.436959
- Fixed-eval mean control effort: 638217.207186 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 128.678 / 78.685 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/12/34
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 140
- Episodes completed total: 567
- First/last quintile mean reward: 43.058288 / 67.221951
- Within-checkpoint reward change: +24.163663
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.225 / 4.025 m
- Fixed-eval mean episode reward: 88.530716
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -26.132583 / 77.950069
- Fixed-eval mean legacy episode reward: 111.171219
- Fixed-eval mean control effort: 733271.908298 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 156.513 / 72.878 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/8/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 151
- Episodes completed total: 718
- First/last quintile mean reward: 74.669817 / 75.337918
- Within-checkpoint reward change: +0.668101
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.895 / 3.623 m
- Fixed-eval mean episode reward: 97.427942
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -23.247866 / 83.962577
- Fixed-eval mean legacy episode reward: 123.965188
- Fixed-eval mean control effort: 804106.030503 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 179.778 / 76.412 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/6/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 164
- Episodes completed total: 882
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
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 1046
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
- Model: `evasive_zemtgo10_effort8_seed2/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_effort8_seed2/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_effort8_seed2/training_curve.png`
