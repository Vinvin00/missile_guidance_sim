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

## Checkpoint 2

- Cumulative timesteps: 40,960
- Episodes completed this checkpoint: 16
- Episodes completed total: 32
- First/last quintile mean reward: -81.063848 / -68.794731
- Within-checkpoint reward change: +12.269117
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 1471.504 / 1235.874 m
- Fixed-eval mean episode reward: -48.253773
- Possible convergence warning: False
- Model: `outputs/checkpoints/rl_checkpoint_02.zip`
- Evaluation details: `outputs/rl_checkpoint_02_eval.json`
- Training curve: `outputs/training_curve.png`

## Checkpoint 3

- Cumulative timesteps: 61,440
- Episodes completed this checkpoint: 16
- Episodes completed total: 48
- First/last quintile mean reward: -77.648933 / -78.043640
- Within-checkpoint reward change: -0.394707
- Fixed-eval hit rate: 0/9 (0.0%)
- Fixed-eval mean/median miss distance: 1984.544 / 2223.822 m
- Fixed-eval mean episode reward: -54.707939
- Possible convergence warning: True
- Model: `outputs/checkpoints/rl_checkpoint_03.zip`
- Evaluation details: `outputs/rl_checkpoint_03_eval.json`
- Training curve: `outputs/training_curve.png`

