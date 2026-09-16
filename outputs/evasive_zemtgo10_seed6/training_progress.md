# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 31415926
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 102
- Episodes completed total: 102
- First/last quintile mean reward: 2.530171 / 38.376746
- Within-checkpoint reward change: +35.846576
- Fixed-eval hit rate: 1/50 (2.0%)
- Fixed-eval mean/median miss distance: 16.668 / 15.542 m
- Fixed-eval mean episode reward: -10.020921
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -48.180705 / 1.446554
- Fixed-eval mean legacy episode reward: -63.225111
- Fixed-eval mean control effort: 1448346.614130 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 181.138 / 113.566 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 12/37/1
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 104
- Episodes completed total: 206
- First/last quintile mean reward: 23.891495 / 14.500234
- Within-checkpoint reward change: -9.391261
- Fixed-eval hit rate: 5/50 (10.0%)
- Fixed-eval mean/median miss distance: 13.671 / 12.562 m
- Fixed-eval mean episode reward: 4.812894
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -41.456050 / 9.555713
- Fixed-eval mean legacy episode reward: -48.928786
- Fixed-eval mean control effort: 1464424.586385 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 183.931 / 107.494 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 12/33/5
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 104
- Episodes completed total: 310
- First/last quintile mean reward: 26.010918 / 19.843890
- Within-checkpoint reward change: -6.167028
- Fixed-eval hit rate: 7/50 (14.0%)
- Fixed-eval mean/median miss distance: 9.589 / 8.187 m
- Fixed-eval mean episode reward: -8.261566
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -58.673337 / 13.698541
- Fixed-eval mean legacy episode reward: -41.504653
- Fixed-eval mean control effort: 1716100.179436 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 202.147 / 127.090 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/34/7
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 131
- Episodes completed total: 441
- First/last quintile mean reward: 44.599558 / 88.310384
- Within-checkpoint reward change: +43.710825
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 3.904 / 3.539 m
- Fixed-eval mean episode reward: 107.890862
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.779218 / 81.956850
- Fixed-eval mean legacy episode reward: 122.618131
- Fixed-eval mean control effort: 552259.960957 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 135.291 / 60.274 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/8/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 152
- Episodes completed total: 593
- First/last quintile mean reward: 100.953460 / 85.715051
- Within-checkpoint reward change: -15.238408
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 5.194 / 4.527 m
- Fixed-eval mean episode reward: 84.519605
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -22.109668 / 69.916043
- Fixed-eval mean legacy episode reward: 88.722984
- Fixed-eval mean control effort: 982067.050549 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 183.771 / 86.666 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/8/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 166
- Episodes completed total: 759
- First/last quintile mean reward: 80.549790 / 117.223138
- Within-checkpoint reward change: +36.673348
- Fixed-eval hit rate: 41/50 (82.0%)
- Fixed-eval mean/median miss distance: 4.019 / 3.759 m
- Fixed-eval mean episode reward: 103.056971
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.612597 / 81.956337
- Fixed-eval mean legacy episode reward: 117.609838
- Fixed-eval mean control effort: 837385.492280 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 180.617 / 73.461 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/7/41
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed6/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed6/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed6/training_curve.png`
