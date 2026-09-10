# Superseded observation-v2 / world3 run

These checkpoints used the ten-value observation-v2 contract with a
three-component world-frame action (`[-1,1]^3`) and the Phase-1 range-
telescope / commanded-effort reward. The run stopped after checkpoint 4
(81,920 timesteps) with 0/9 hits and along-track null-space waste.

Retained for diagnostic provenance. Must not be resumed: the environment
now defaults to `lateral2` actions and the ZEM PBRS + closest-approach
reward. The replacement from-scratch retrain lives under `outputs/`.
