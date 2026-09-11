# Archived: reward-redesign 10-D observation lineage

These checkpoints (`rl_checkpoint_01.zip` … `_04.zip`) are the **previous**
RL training lineage under the ten-value observation contract
(`use_target_turn_rate_obs=false`). They remain for comparison and
diagnostics.

**Current baseline (promoted 2026-09-11):**

See [`../CURRENT_RL_BASELINE.json`](../CURRENT_RL_BASELINE.json) →
`outputs/observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip`
(13-D observation with target turn-rate channels).

Do not resume training from these zips into the turn-rate branch — the
observation contracts are incompatible.
