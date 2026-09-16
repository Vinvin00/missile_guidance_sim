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

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 98
- Episodes completed total: 98
- First/last quintile mean reward: 1.720134 / 18.767240
- Within-checkpoint reward change: +17.047106
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 9.192 / 7.533 m
- Fixed-eval mean episode reward: 35.839286
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.606214 / 27.732269
- Fixed-eval mean legacy episode reward: 9.047766
- Fixed-eval mean control effort: 698848.402982 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 124.137 / 85.684 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 7/29/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 101
- Episodes completed total: 199
- First/last quintile mean reward: 19.267283 / 19.381961
- Within-checkpoint reward change: +0.114679
- Fixed-eval hit rate: 16/50 (32.0%)
- Fixed-eval mean/median miss distance: 7.940 / 7.149 m
- Fixed-eval mean episode reward: 35.506610
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -32.987056 / 31.780435
- Fixed-eval mean legacy episode reward: 11.361677
- Fixed-eval mean control effort: 920077.049947 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 141.629 / 90.698 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/26/16
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 120
- Episodes completed total: 333
- First/last quintile mean reward: 61.768544 / 60.630394
- Within-checkpoint reward change: -1.138150
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.552 / 4.262 m
- Fixed-eval mean episode reward: 92.144546
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.506808 / 73.938124
- Fixed-eval mean legacy episode reward: 103.746789
- Fixed-eval mean control effort: 609555.163218 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 133.616 / 71.523 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/12/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 142
- Episodes completed total: 475
- First/last quintile mean reward: 70.407683 / 61.169646
- Within-checkpoint reward change: -9.238037
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.336 / 3.950 m
- Fixed-eval mean episode reward: 102.617257
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.045891 / 79.949918
- Fixed-eval mean legacy episode reward: 118.455395
- Fixed-eval mean control effort: 547490.927435 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 134.618 / 67.868 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/8/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 147
- Episodes completed total: 622
- First/last quintile mean reward: 88.362558 / 90.242285
- Within-checkpoint reward change: +1.879727
- Fixed-eval hit rate: 37/50 (74.0%)
- Fixed-eval mean/median miss distance: 4.972 / 4.108 m
- Fixed-eval mean episode reward: 91.999807
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -18.638043 / 73.924620
- Fixed-eval mean legacy episode reward: 100.832559
- Fixed-eval mean control effort: 704539.937255 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 151.042 / 74.051 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/9/37
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 145
- Episodes completed total: 767
- First/last quintile mean reward: 75.561888 / 62.577021
- Within-checkpoint reward change: -12.984867
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.410 / 4.405 m
- Fixed-eval mean episode reward: 104.352106
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.311081 / 79.949957
- Fixed-eval mean legacy episode reward: 118.604587
- Fixed-eval mean control effort: 446413.323391 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 115.121 / 61.501 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/7/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 153
- Episodes completed total: 920
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
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 164
- Episodes completed total: 1084
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
- Model: `evasive_zemtgo10_seed4/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed4/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed4/training_curve.png`
