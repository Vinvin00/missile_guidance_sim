# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 10 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled`)
- Policy action: normalized `[-1, 1]^2`, rescaled to the physical 25 g environment action before dynamics
- Action layout: `lateral2`
- Domain randomization: False (must remain false for this retrain)
- Reward: ZEM PBRS shaping (w=50) + closest-approach terminal + achieved-effort; legacy Phase-1 reward logged in parallel
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -53.654772 / -51.661530
- Within-checkpoint reward change: +1.993243
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 549.644 / 327.484 m
- Fixed-eval mean episode reward: -14.543541
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -0.363732 / -39.453720
- Fixed-eval mean legacy episode reward: -46.322670
- Fixed-eval mean control effort: 4429.417390 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 12.861 / 12.761 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `outputs/rl_checkpoint_01_eval.json`
- Training curve: `outputs/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: -13.878959 / -43.075211
- Within-checkpoint reward change: -29.196252
- Fixed-eval hit rate: 4/9 (44.4%)
- Fixed-eval mean/median miss distance: 493.862 / 5.604 m
- Fixed-eval mean episode reward: 39.915466
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -2.065677 / 16.707233
- Fixed-eval mean legacy episode reward: 53.403675
- Fixed-eval mean control effort: 29301.870236 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 31.666 / 28.975 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/4
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `outputs/rl_checkpoint_02_eval.json`
- Training curve: `outputs/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 16
- Episodes completed total: 48
- First/last quintile mean reward: -12.351924 / 9.796340
- Within-checkpoint reward change: +22.148264
- Fixed-eval hit rate: 4/9 (44.4%)
- Fixed-eval mean/median miss distance: 542.122 / 8.899 m
- Fixed-eval mean episode reward: 34.386850
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -6.343175 / 15.456115
- Fixed-eval mean legacy episode reward: 51.242140
- Fixed-eval mean control effort: 102900.445065 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 50.102 / 43.498 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/5/4
- Possible convergence warning: True
- Model: `outputs/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `outputs/rl_checkpoint_03_eval.json`
- Training curve: `outputs/training_curve.png`

## Reporting split (retroactive CP1–3)

Group A = NoManeuver + Weave (feasible within 25 s; drives stop).
Group B = ConstantTurn (budget-constrained; tracked only).

- CP1 Group A: 0/6 hits, miss 240.991/213.622 m, reward 1.015742, effort 5714.991
- CP1 Group B: 0/3 hits, miss 1166.950/1014.826 m, reward -45.662107, effort 1858.270
- CP2 Group A: 4/6 hits, miss 4.076/3.586 m, reward 89.531516, effort 28688.840
- CP2 Group B: 0/3 hits, miss 1473.433/1464.221 m, reward -59.316635, effort 30527.930
- CP3 Group A: 4/6 hits, miss 5.763/4.155 m, reward 83.327981, effort 134522.592
- CP3 Group B: 0/3 hits, miss 1614.842/1440.323 m, reward -63.495412, effort 39656.152

- CP1→CP2: Group A improved (hits 0/6→4/6, miss 241→4.1 m).
- CP2→CP3: Group A did **not** improve (hits flat 4/6, miss 4.1→5.8 m, reward 89.5→83.3). Pooled CP3 warning was therefore **not** only Group B noise — Group A also stalled under the same joint criteria (though absolute Group A performance remained strong).

## Checkpoint 4

- Cumulative timesteps: 81,920
- Episodes completed this checkpoint: 16
- Episodes completed total: 64
- First/last quintile mean reward: -17.697392 / 24.097405
- Within-checkpoint reward change: +41.794797
- Fixed-eval hit rate: 3/9 (33.3%)
- Fixed-eval mean/median miss distance: 529.280 / 6.030 m
- Fixed-eval mean episode reward: 19.137620
- Fixed-eval mean reward components (shaping/effort/terminal): 25.273910 / -10.930051 / 4.793761
- Fixed-eval mean legacy episode reward: 24.900412
- Fixed-eval mean control effort: 197488.238608 m²/s³
- Fixed-eval mean commanded/achieved RMS accel: 69.209 / 56.197 m/s²
- Fixed-eval mean commanded along-track energy fraction: 0.000000
- Fixed-eval outcomes (ground impact/timeout/hit): 0/6/3
- Group A (NoManeuver+Weave) hit rate / mean/median miss / mean reward / mean effort: 3/6 / 5.759 / 5.186 m / 59.888424 / 274846.621824 m²/s³
- Group B (ConstantTurn) hit rate / mean/median miss / mean reward / mean effort: 0/3 / 1576.322 / 1413.770 m / -62.363988 / 42771.472175 m²/s³
- Possible convergence warning (Group A stop): True
- Model: `outputs/checkpoints/rl_checkpoint_04.zip`
- Evaluation details: `outputs/rl_checkpoint_04_eval.json`
- Training curve: `outputs/training_curve.png`
