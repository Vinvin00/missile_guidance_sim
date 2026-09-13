# Attempt 01 — FAILED lineage (superseded, kept for provenance)

0/50 held-out hits at every checkpoint; mean miss degraded 1231 → 4672 m
while PN scored 78% on the same set. Do not promote or resume from these.

Two defects, both found by the post-run diagnostic and fixed for attempt 02:

1. **Estimator gain mistuned.** `alpha=0.5` (Zarchan's 100 Hz figure) at this
   codebase's 25–50 Hz turned ~18 m of position residual into ~75 m/s of
   velocity error, corrupting LOS rate by ~0.66x its own magnitude. An
   equal-budget ablation with tracking *off* scored 7/20 vs 0/20 with it on.
   Fixed: `alpha=0.2` (velocity error 18 m/s, LOS-rate error 0.16x).
2. **Miss penalty saturated.** `miss_penalty * tanh(min_range / 1000 m)` is
   flat past ~3 km. From a 7 km start an untrained policy misses by 1–5 km,
   so it sat in a zone with ~0.001 gradient and nothing pulled it back --
   hence the monotone degradation. Fixed: scale 3000 m.

Also raised timesteps per checkpoint 20,480 → 204,800: 45 s episodes bought
only ~10 episodes per checkpoint at the inherited cadence.

`pn_baseline.json` here remains valid as the classical reference (it does not
depend on either defect).
