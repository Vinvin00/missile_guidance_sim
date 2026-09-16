# evasive_shapinggamma — archived, not promoted

Tested `shaping_gamma=0.995` (match PPO γ) with otherwise lineage defaults.

- CP1: 22/50 (44%) — best CP1 of any lineage; progress_reward became informative
- CP2: 2/50 (4%) — cmd_rms ran away 103→157; stop fired
- CP3: 14/50 (28%) — partial recovery, cmd_rms still ~153; stop still true

Hypothesis that γ-match would stop the effort runaway: **falsified**.
Do not promote. Do not resume CP4/CP5 from this lineage.
