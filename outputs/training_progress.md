# Phase 2 training progress

- Algorithm: recurrent PPO (`MlpLstmPolicy`, 64 hidden units)
- Policy action: normalized `[-1, 1]^3`, rescaled to the unchanged physical 25 g environment action before dynamics
- Fixed budget: 102,400 timesteps in 5 checkpoints of 20,480
- Training seed: 20260909
- Fixed evaluation set: 9 engagements (3 no-maneuver, 3 constant-turn, 3 sinusoidal-weave)

## Checkpoint 1

- Cumulative timesteps: 20,480
- Episodes completed this checkpoint: 16
- Episodes completed total: 16
- First/last quintile mean reward: -73.775322 / -93.423403
- Within-checkpoint reward change: -19.648081
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 2591.095 / 2451.082 m
- Fixed-eval mean episode reward: -69.176999
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_01.zip`
- Evaluation details: `outputs/rl_checkpoint_01_eval.json`
- Training curve: `outputs/training_curve.png`

