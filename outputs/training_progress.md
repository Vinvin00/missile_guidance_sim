# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Observation: 10 values (`los_unit_x, los_unit_y, los_unit_z, los_rate_x_scaled, los_rate_y_scaled, los_rate_z_scaled, range_scaled, closing_velocity_scaled, height_above_ground_scaled, altitude_rate_scaled`)
- Policy action: normalized `[-1, 1]^3`, rescaled to the unchanged physical 25 g environment action before dynamics
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -72.083842 / -90.421188
- Within-checkpoint reward change: -18.337346
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 2638.656 / 2618.771 m
- Fixed-eval mean episode reward: -69.585664
- Fixed-eval mean reward components (progress/effort/terminal): 30.559362 / -0.145026 / -100.000000
- Fixed-eval mean control effort: 8716.992925 m²/s³
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `outputs/rl_checkpoint_01_eval.json`
- Training curve: `outputs/training_curve.png`

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: -78.815875 / -74.929087
- Within-checkpoint reward change: +3.886787
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 1786.639 / 1423.028 m
- Fixed-eval mean episode reward: -58.671985
- Fixed-eval mean reward components (progress/effort/terminal): 41.649211 / -0.321196 / -100.000000
- Fixed-eval mean control effort: 19305.963494 m²/s³
- Fixed-eval outcomes (ground impact/timeout/hit): 0/9/0
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `outputs/rl_checkpoint_02_eval.json`
- Training curve: `outputs/training_curve.png`
