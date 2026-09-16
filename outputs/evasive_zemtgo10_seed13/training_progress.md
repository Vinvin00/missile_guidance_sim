# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 2718281828
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 101
- Episodes completed total: 101
- First/last quintile mean reward: -3.892483 / 17.634933
- Within-checkpoint reward change: +21.527416
- Fixed-eval hit rate: 6/50 (12.0%)
- Fixed-eval mean/median miss distance: 14.279 / 10.690 m
- Fixed-eval mean episode reward: -11.862796
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -60.116440 / 11.540414
- Fixed-eval mean legacy episode reward: -33.831942
- Fixed-eval mean control effort: 1431735.227949 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 179.913 / 125.144 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/35/6
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 101
- Episodes completed total: 202
- First/last quintile mean reward: 20.688192 / 11.638764
- Within-checkpoint reward change: -9.049428
- Fixed-eval hit rate: 12/50 (24.0%)
- Fixed-eval mean/median miss distance: 8.627 / 7.215 m
- Fixed-eval mean episode reward: 14.668199
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -45.791312 / 23.746281
- Fixed-eval mean legacy episode reward: -13.982720
- Fixed-eval mean control effort: 1213842.176355 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 166.525 / 109.458 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/29/12
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 121
- Episodes completed total: 323
- First/last quintile mean reward: 21.752011 / 75.499636
- Within-checkpoint reward change: +53.747626
- Fixed-eval hit rate: 14/50 (28.0%)
- Fixed-eval mean/median miss distance: 7.732 / 6.401 m
- Fixed-eval mean episode reward: 19.852906
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -44.644198 / 27.783873
- Fixed-eval mean legacy episode reward: -3.069641
- Fixed-eval mean control effort: 1274990.102036 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 173.352 / 109.530 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 5/31/14
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 121
- Episodes completed total: 444
- First/last quintile mean reward: 29.668518 / 87.844376
- Within-checkpoint reward change: +58.175858
- Fixed-eval hit rate: 35/50 (70.0%)
- Fixed-eval mean/median miss distance: 4.942 / 4.381 m
- Fixed-eval mean episode reward: 89.022419
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -17.607217 / 69.916406
- Fixed-eval mean legacy episode reward: 92.237360
- Fixed-eval mean control effort: 815786.991100 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 163.669 / 73.994 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/14/35
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 147
- Episodes completed total: 591
- First/last quintile mean reward: 99.572809 / 66.684946
- Within-checkpoint reward change: -32.887864
- Fixed-eval hit rate: 24/50 (48.0%)
- Fixed-eval mean/median miss distance: 5.951 / 5.082 m
- Fixed-eval mean episode reward: 54.251781
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -30.321903 / 47.860454
- Fixed-eval mean legacy episode reward: 36.090111
- Fixed-eval mean control effort: 1277995.117850 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 188.658 / 94.680 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 4/22/24
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 149
- Episodes completed total: 740
- First/last quintile mean reward: 94.706981 / 95.529071
- Within-checkpoint reward change: +0.822090
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.903 / 3.883 m
- Fixed-eval mean episode reward: 109.018699
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -13.663117 / 85.968586
- Fixed-eval mean legacy episode reward: 129.416720
- Fixed-eval mean control effort: 681240.505128 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 164.411 / 70.863 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/6/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 163
- Episodes completed total: 903
- First/last quintile mean reward: 123.227485 / 129.209810
- Within-checkpoint reward change: +5.982324
- Fixed-eval hit rate: 40/50 (80.0%)
- Fixed-eval mean/median miss distance: 4.116 / 3.791 m
- Fixed-eval mean episode reward: 129.313982
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.961248 / 108.561999
- Fixed-eval mean legacy episode reward: 114.809871
- Fixed-eval mean control effort: 752258.664671 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 163.797 / 72.429 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/7/40
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 152
- Episodes completed total: 1055
- First/last quintile mean reward: 111.179196 / 119.338114
- Within-checkpoint reward change: +8.158919
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.918 / 3.682 m
- Fixed-eval mean episode reward: 141.463401
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.870205 / 115.620376
- Fixed-eval mean legacy episode reward: 128.583340
- Fixed-eval mean control effort: 677660.844724 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 163.728 / 65.740 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/6/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed13/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed13/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed13/training_curve.png`
