# Superseded Phase 2 run

These checkpoints used the original eight-value observation:

`[LOS unit vector (3), scaled LOS-rate vector (3), scaled range,
scaled closing velocity]`.

The run stopped after checkpoint 3 at 61,440 timesteps. It is retained for
diagnostic provenance but must not be resumed: the environment now appends
pursuer height above ground and altitude rate, producing a ten-value
observation that is incompatible with these saved policies.

Reward-component diagnostics showed that the effort penalty was less than
1.2% of positive progress reward in every fixed evaluation case. The reward
weights were therefore not changed for the replacement run.
