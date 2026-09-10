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
