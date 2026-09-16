# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 12 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled, time_since_update_scaled, estimate_uncertainty_scaled`)
- use_target_turn_rate_obs: False
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 1,024,000 timesteps in 5 checkpoints of 204,800
- Training seed: 3141592653
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)
- Reporting split: Group A = NoManeuver+Weave (stop condition); Group B = ConstantTurn (tracked only; budget-constrained)

## Checkpoint 1

- Cumulative timesteps: 204,800
- Episodes completed this checkpoint: 96
- Episodes completed total: 96
- First/last quintile mean reward: -25.324949 / 17.671715
- Within-checkpoint reward change: +42.996664
- Fixed-eval hit rate: 9/50 (18.0%)
- Fixed-eval mean/median miss distance: 10.645 / 7.964 m
- Fixed-eval mean episode reward: 12.400918
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -41.980469 / 17.668156
- Fixed-eval mean legacy episode reward: -18.002237
- Fixed-eval mean control effort: 1081397.474914 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 154.164 / 103.967 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 8/33/9
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): False
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_01_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 409,600
- Episodes completed this checkpoint: 103
- Episodes completed total: 199
- First/last quintile mean reward: 11.889504 / 44.503597
- Within-checkpoint reward change: +32.614093
- Fixed-eval hit rate: 12/50 (24.0%)
- Fixed-eval mean/median miss distance: 8.308 / 7.520 m
- Fixed-eval mean episode reward: 17.167516
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -43.301088 / 23.755374
- Fixed-eval mean legacy episode reward: -8.808038
- Fixed-eval mean control effort: 1167952.356401 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 160.504 / 104.981 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 9/29/12
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_02_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 614,400
- Episodes completed this checkpoint: 117
- Episodes completed total: 316
- First/last quintile mean reward: 25.384534 / 47.017372
- Within-checkpoint reward change: +21.632838
- Fixed-eval hit rate: 30/50 (60.0%)
- Fixed-eval mean/median miss distance: 5.422 / 4.657 m
- Fixed-eval mean episode reward: 67.873615
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -28.732900 / 59.893285
- Fixed-eval mean legacy episode reward: 75.833036
- Fixed-eval mean control effort: 705867.867555 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 130.063 / 85.396 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 6/14/30
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_03_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 4

- Cumulative timesteps: 819,200
- Episodes completed this checkpoint: 128
- Episodes completed total: 444
- First/last quintile mean reward: 56.017083 / 57.692001
- Within-checkpoint reward change: +1.674918
- Fixed-eval hit rate: 39/50 (78.0%)
- Fixed-eval mean/median miss distance: 4.371 / 4.066 m
- Fixed-eval mean episode reward: 95.401088
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -19.254623 / 77.942482
- Fixed-eval mean legacy episode reward: 113.223565
- Fixed-eval mean control effort: 639298.291940 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 143.613 / 74.927 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 3/8/39
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_04_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 5

- Cumulative timesteps: 1,024,000
- Episodes completed this checkpoint: 150
- Episodes completed total: 594
- First/last quintile mean reward: 63.759126 / 85.824682
- Within-checkpoint reward change: +22.065556
- Fixed-eval hit rate: 46/50 (92.0%)
- Fixed-eval mean/median miss distance: 3.907 / 3.687 m
- Fixed-eval mean episode reward: 118.277721
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -10.412160 / 91.976651
- Fixed-eval mean legacy episode reward: 145.080507
- Fixed-eval mean control effort: 505249.703421 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 144.427 / 63.518 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/3/46
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_05.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_05_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 6

- Cumulative timesteps: 1,228,800
- Episodes completed this checkpoint: 169
- Episodes completed total: 763
- First/last quintile mean reward: 95.577075 / 103.891533
- Within-checkpoint reward change: +8.314459
- Fixed-eval hit rate: 42/50 (84.0%)
- Fixed-eval mean/median miss distance: 3.943 / 3.756 m
- Fixed-eval mean episode reward: 106.528665
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -14.149553 / 83.964987
- Fixed-eval mean legacy episode reward: 125.868143
- Fixed-eval mean control effort: 675098.676959 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 160.623 / 71.909 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/6/42
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_06.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_06_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 7

- Cumulative timesteps: 1,433,600
- Episodes completed this checkpoint: 163
- Episodes completed total: 926
- First/last quintile mean reward: 140.455234 / 120.102721
- Within-checkpoint reward change: -20.352513
- Fixed-eval hit rate: 44/50 (88.0%)
- Fixed-eval mean/median miss distance: 4.192 / 4.058 m
- Fixed-eval mean episode reward: 141.280029
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -12.430827 / 116.997626
- Fixed-eval mean legacy episode reward: 134.629518
- Fixed-eval mean control effort: 627354.647207 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 158.569 / 69.801 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 1/5/44
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_07.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_07_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`

## Checkpoint 8

- Cumulative timesteps: 1,638,400
- Episodes completed this checkpoint: 154
- Episodes completed total: 1080
- First/last quintile mean reward: 113.969392 / 102.307270
- Within-checkpoint reward change: -11.662122
- Fixed-eval hit rate: 43/50 (86.0%)
- Fixed-eval mean/median miss distance: 3.880 / 3.849 m
- Fixed-eval mean episode reward: 136.302240
- Fixed-eval mean reward components (shaping/effort/terminal): 36.713230 / -15.493921 / 115.082931
- Fixed-eval mean legacy episode reward: 129.149783
- Fixed-eval mean control effort: 702816.180191 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 166.552 / 75.051 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 2/5/43
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/0 / 0.000 / 0.000 m / 0.000000 / 0.000000 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `evasive_zemtgo10_seed14/checkpoints/rl_checkpoint_08.zip`
- Evaluation details: `evasive_zemtgo10_seed14/rl_checkpoint_08_eval.json`
- Training curve: `evasive_zemtgo10_seed14/training_curve.png`
