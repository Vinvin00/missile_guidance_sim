# evasive_effort15 — in progress

Follow-up to `evasive_shapinggamma` (stop at CP3).

Hypothesis: matching shaping_gamma to PPO γ made progress informative but did
not stop cmd_rms runaway (103→157). Raising effort_weight 5→15 while keeping
shaping_gamma=0.995 should keep CP1-quality hits without the CP2 collapse.

From scratch. Do not resume shapinggamma checkpoints.
