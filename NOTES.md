## 2026-09-14 — zem_t_go_max_s root cause + effort8 finished (56%) + seed3 launched

### Root cause of the shaping_gamma / effort_weight failures

Both single-variable follow-ups to the CP1–CP5 evasive lineage (`shaping_gamma`
matched to PPO γ, then `effort_weight` 5→15 on top) failed the same way:
reward kept climbing while hit rate collapsed. Traced it to `RewardConfig.t_go_max_s`
being set to `max_time` (45 s) in `PPOTrainingConfig.reward_config()`. The ZEM
potential extrapolates the *current* relative velocity `t_go` seconds ahead;
whenever closing velocity is near `vc_min` (normal against an evasive target —
the pursuer usually isn't precisely pointed at it), `t_go` clamps to the full
45 s cap. A synthetic sensitivity probe (`src/guidance_sim/rl/zem.py`
functions, representative 6 km engagement) confirmed the leverage:

```
dtheta=0.0°  ZEM(tgo=45)= 862.6m  phi=-0.633    ZEM(tgo=8)=2486.8m  phi=-0.833
dtheta=2.0°  ZEM(tgo=45)=1070.6m  phi=-0.682    ZEM(tgo=8)=2521.1m  phi=-0.833
```

A 2° heading wobble moves phi by ~0.05 at `t_go_max=45` vs ~0.002 at `t_go_max=8`
— 25x more leverage. With `shaping_weight=50` that's up to 2.5 reward/step
from wobbling alone, no actual closure required. This is the real cause of
the `cmd_rms` runaway seen in every prior lineage (30→220 across CP1→CP5),
not effort weight or the discount mismatch — those only changed how cheap
the wobble was, never removed the lever.

Fix: decoupled `t_go_max_s` from `max_time`. Added `PPOTrainingConfig.zem_t_go_max_s`
(default **10.0** — a physically-plausible terminal-guidance timescale,
independent of episode length) and a `--zem-t-go-max` CLI override on
`run_evasive_checkpoint.py`, alongside the existing `--shaping-gamma` /
`--effort-weight` / `--seed` overrides. `miss_tanh_scale_m`, `shaping_gamma`,
`effort_weight` all left at lineage defaults for a clean single-variable test.

### Result: reproduces across three seeds, best result of the project

| lineage | seed | CP3 | CP4 | CP5 | note |
|---|---|---|---|---|---|
| `evasive_zemtgo10` | 20260909 | 21/50 (42%) | 6/50 (12%) | 26/50 (52%) | sawtooth |
| `evasive_zemtgo10_seed2` | 77000001 | 14/50 (28%) | **33/50 (66%)** | 31/50 (62%) | best peak |
| `evasive_zemtgo10_effort8` | 20260909 | 21/50 (42%) | 21/50 (42%) | 28/50 (56%) | effort_weight 5→8; monotonic 11→13→21→21→28, no sawtooth |
| `evasive_zemtgo10_seed3` | 43500777 | 10/50 (20%) | 12/50 (24%) | **37/50 (74%)** | best of all four; p90 miss 8.5 m, max 9.9 m |

Four finished lineages now. Three land their peak checkpoint at 50-66%;
seed3's CP5 reaches **37/50 (74%)**, median miss **4.0 m**, p90 8.5 m, max
9.9 m — right up against information-matched PN's ~78% hit rate / 3.9 m
median on the same held-out set
(`outputs/evasive_delayed_tracking_attempt01/pn_baseline.json`), and with a
far tighter worst-case tail (PN's max miss on this set was in the hundreds
of metres). This is a step change from every earlier lineage (prior best
late-checkpoint hit rate was ~22/50). `effort_weight=8` on top of the
`t_go_max` fix trades a few points of peak hit rate for a much smoother,
monotonic climb (no CP4-style collapse) — worth preferring for
reproducibility even though seed3's raw peak is now the highest overall.

**Still noisy pre-CP5 in every lineage** (seed3: 28%→4%→20%→24%→74%) — the
win is concentrated in the last checkpoint, not a steady climb, so
checkpoint selection matters and CP5 alone is not yet trustworthy as "the"
result without knowing why CP1-CP4 don't predict it.

**Not promoted.** `CURRENT_RL_BASELINE.json` untouched. seed3 CP5 nearly
closes the PN gap but three-of-four peaks (66%, 62%, 56%, 74%) is still a
small sample; worth a held-out re-eval with a couple more seeds, or a look
at why CP5 specifically jumps, before treating any single checkpoint as
promotable.

## 2026-09-14 — evasive_zemtgo10_effort8 aborted mid-CP1; daemon-restarted

Prior launch (~09:22 Rome) died at ~16 384 / 204 800 timesteps with empty
`checkpoints/` (shell-teardown / process-group kill — same mode as effort15
CP2). A plain `nohup` retry at 10:42 also died; fixed with a Python
double-fork (`os.setsid` + second fork, PPID=1) launching
`outputs/evasive_zemtgo10_effort8/run_lineage.sh` at ~10:44 Rome. Confirmed
alive past ~139k/204800 CP1 steps. Lineage runs CP1→CP5
(`zem_t_go_max_s=10`, `effort_weight=8`, seed 20260909). Pidfile:
`outputs/evasive_zemtgo10_effort8/lineage.pid`.
`CURRENT_RL_BASELINE.json` untouched. Do not promote without held-out win vs
seed2 CP4 (33/50) and information-matched PN (~78%).

## 2026-09-14 — evasive_zemtgo10 (+ seed2) finished; best so far, do not promote

Isolated lineages at `outputs/evasive_zemtgo10/` (seed 20260909) and
`outputs/evasive_zemtgo10_seed2/` (seed 77000001). Single variable vs prior
defaults: `zem_t_go_max_s` 45 → **10**. `CURRENT_RL_BASELINE.json` untouched.

### Seed 1 (`evasive_zemtgo10`)

| CP | hits | median miss | cmd_rms | stop |
|---|---|---|---|---|
| 1 | 8/50 (16%) | 10.2 m | 138 | False |
| 2 | 6/50 (12%) | 9.2 m | 160 | True |
| 3 | 21/50 (42%) | 5.2 m | 141 | True |
| 4 | 6/50 (12%) | 10.6 m | 224 | True |
| 5 | **26/50 (52%)** | 4.8 m | 175 | True |

Sawtooth CP3→CP4→CP5. Best: CP5.

### Seed 2 (`evasive_zemtgo10_seed2`) — finished ~09:18 Rome

| CP | hits | median miss | cmd_rms | stop |
|---|---|---|---|---|
| 1 | 4/50 (8%) | 12.5 m | 131 | False |
| 2 | 9/50 (18%) | 9.4 m | 145 | True |
| 3 | 14/50 (28%) | 7.8 m | 147 | True |
| 4 | **33/50 (66%)** | **4.6 m** | 135 | True |
| 5 | 31/50 (62%) | 4.5 m | 167 | True |

Per-maneuver at seed2 CP4: break_turn 6/13, vertical_jink 12/13,
random_jink 7/12, bounded_weave 8/12. CP5 gained break_turn (8/13) but
lost random_jink (4/12); overall slight regression + cmd_rms up 135→167.

### Verdict

**`zem_t_go_max_s=10` is a real win** vs shapinggamma/effort15/misstanh
lineages (prior best late CP ~22/50, effort15 CP1 1/50). Peak across seeds
is seed2 CP4 **33/50 (66%)**, median miss 4.6 m — still below
information-matched PN on the same held-out set (~**78%**,
`outputs/evasive_delayed_tracking_attempt01/pn_baseline.json`). Seed variance
is large (sawtooth on seed1; smoother climb then CP4 peak on seed2).

**Do not promote. Do not continue either lineage past CP5.** Best checkpoint
to keep for comparison: `evasive_zemtgo10_seed2/checkpoints/rl_checkpoint_04.zip`.

Also recorded: `evasive_effort15` died after poor CP1 (1/50, effort −63) —
`effort_weight=15` alone is too harsh.

### Next experiment (started)

`outputs/evasive_zemtgo10_effort8/`: keep `zem_t_go_max_s=10`, raise
`effort_weight` 5 → **8** (mild; not 15). Goal: hold ~66% envelope while
stopping the CP4→CP5 cmd_rms climb. From scratch, seed 20260909.


# NOTES

## 2026-09-13 — evasive_shapinggamma CP1–CP3: stop condition fired

Isolated lineage at `outputs/evasive_shapinggamma/` (`shaping_gamma=0.995` matching
PPO γ; `miss_tanh_scale=3000` unchanged). `CURRENT_RL_BASELINE.json` untouched.

| CP | hits | median miss | cmd_rms | progress_reward | stop |
|---|---|---|---|---|---|
| 1 | **22/50 (44%)** | 5.4 m | 102.8 | 195.4 | False |
| 2 | 2/50 (4%) | 11.6 m | **157.1** | 283.1 | True |
| 3 | 14/50 (28%) | 7.1 m | 152.7 | 222.5 | True |

Per-maneuver CP1 → CP2 → CP3 hits:
- break_turn 7/13 → 0/13 → 5/13
- vertical_jink 9/13 → 0/13 → 5/13
- random_jink 4/12 → 1/12 → 4/12
- bounded_weave 2/12 → 1/12 → 0/12

### Verdict on the discount-mismatch hypothesis

**Partially confirmed, then falsified on the claim that mattered.**
`progress_reward` is no longer the telescoping constant 27.11 — shaping finally
measures something. But `cmd_rms` still climbed 103 → 157 by CP2, the same
runaway both prior lineages showed. Matching γ did not stabilize command effort.

**Do not promote. Do not continue to CP4/CP5.** Best checkpoint in this lineage
is CP1; best late checkpoint across lineages remains elsewhere to compare, but
this CP3 is not a baseline candidate.

### Next experiment (queued)

From-scratch lineage keeping `shaping_gamma=0.995` and raising effort weight to
curb the CP1→CP2 command runaway, rather than resuming this CP3.


## 2026-09-13 — Alpha-beta velocity from the seeker's own rate channels

The filter derived target velocity by differencing noisy Cartesian position
fixes with a `beta/dt` gain. At the tracking rates this project actually
uses (25–50 Hz) that gain is order 4, so ~18 m of position noise became
~75 m/s of velocity error — enough to corrupt the LOS rate the guidance law
depends on.

The seeker was already publishing azimuth/elevation/range *rates* with
~1 mrad/s noise, and the filter used them exactly once, at initialisation,
then threw them away. `AlphaBetaFilter` now takes velocity from those
channels (`use_measured_rates=True`, `velocity_gain=0.3`), falling back to
the `beta/dt` residual term when a seeker reports no rates.

Measured on a break-turn target at 25 Hz / 40 ms latency:

| | position err | velocity err | LOS-rate err |
|---|---|---|---|
| original (alpha=0.5, position differencing) | 12.9 m | 77.8 m/s | 0.66x signal |
| alpha=0.2 only | 12.9 m | 18.3 m/s | 0.16x signal |
| alpha=0.2 + measured rates | 13.0 m | **8.8 m/s** | **0.08x signal** |

Position accuracy is unchanged; this is purely a velocity-channel fix.

### This invalidates a documented Priority-1 result

`test_miss_distance_degrades_with_seeker_noise` asserted that closed-loop
miss degrades by >50 m under seeker noise. With the fixed filter it does
not: PN holds 3.4–4.6 m median miss at *every* noise scale in the sweep.

I checked for truth leakage before accepting this and there is none —
velocity error still scales linearly with noise scale (0 → 27 m/s at
scale 8), just with a ~10x smaller coefficient. The old filter turned the
sweep's noise scales into 69–416 m/s of velocity error, and that is what
actually wrecked the intercepts. **The "miss degrades with seeker noise"
finding was substantially an artifact of the mistuned estimator, not an
intrinsic property of seeker noise at these levels.**

The test is split rather than loosened:

- `test_estimator_velocity_degrades_with_seeker_noise` gates the invariant
  that survives — the *estimate* still degrades monotonically with noise
  (Spearman >= 0.6, exact at zero noise).
- `test_miss_distance_stays_bounded_across_the_noise_sweep` asserts the new
  property — PN holds intercept across the sweep.

**Still outstanding:** `scripts/run_seeker_noise_sweep.py` outputs and any
doc text citing the original degradation figure were produced with the old
filter and need re-running or annotating.

## 2026-09-13 — CP1–CP5 evasive lineage: negative result, stop condition fired

- Ran the full five-checkpoint evasive + delayed-tracking lineage into an
  isolated `outputs/evasive_delayed_tracking/`. `CURRENT_RL_BASELINE.json`
  untouched; no promotion.
- Config: v1 maneuvers (break turn / vertical jink / randomized jink /
  retained bounded weave; Split-S held for CP5 per plan), tracking on,
  `max_time=45 s` with `t_go_max_s` now derived from it, 12-D obs, no
  privileged turn-rate channel.
- **Result: 0/50 held-out hits at every checkpoint**, and mean miss got
  *worse* monotonically: 1231 → 1221 → 4110 → 3989 → 4672 m; mean reward
  −50.8 → −79.7. The `convergence_warning` stop condition fired at CP2,
  CP3, CP4 and CP5.
- **Classical reference on the identical held-out set: PN 78% hits (39/50),
  median miss 3.9 m** (`outputs/evasive_delayed_tracking/pn_baseline.json`,
  PN consuming the same estimator output the policy sees, so it is
  information-matched). Break turn is the discriminator: PN 6/13 there vs
  11–12/13 on the other kinds. So the task is demonstrably solvable in this
  regime — this is an RL training failure, not an impossible environment.
- **Sample-budget problem the spec missed.** Raising the budget to 45 s
  (spec §4) cut episodes per checkpoint roughly in half at the unchanged
  20,480-timestep cadence: `ep_len_mean` ≈ 2010 steps, so CP1 saw only
  ~10 episodes. There is a trap in it — a policy that never intercepts
  runs the *full* 45 s every episode, so it earns less experience per
  timestep than a competent one and is penalised for being bad.
- Compute is not the binding constraint that the "compute-bounded 20,480"
  figure assumed: 20,480 timesteps trains in ~13 s on this machine.
- 40 of 50 held-out episodes end in timeout, the other 10 in ground impact
  — worth a look on its own, since the evasive ICs start at 5.2–6.5 km.
- **CP5 is not a promotable baseline and must not be treated as one.**
  Lineage archived to `outputs/evasive_delayed_tracking_attempt01/` with a
  README recording both defects found below.

### Ablation: tracking was the whole story, the maneuvers were fine

Each arm trained from scratch at 204,800 steps (10x the checkpoint cadence):

| arm | maneuvers | tracking | result |
|---|---|---|---|
| A | evasive | on | 0/20 hits, median 557 m |
| B | evasive | **off** | **7/20 hits, median 8.6 m** |
| C | old | on | 0/9 hits, median 3977 m |
| D | old | **off** | **5/9 hits, median 4.9 m** |

- Arm D reproduces the frozen lineage's known **5/9**, which validates the
  harness. Arm B shows the new evasion maneuvers are learnable. Both
  tracking arms score zero regardless of maneuver difficulty, so the
  maneuver redesign was never the blocker.

### Two defects, both fixed

1. **Estimator gain mistuned for this codebase's rates.** `alpha=0.5` is
   Zarchan's 100 Hz figure; at 25–50 Hz the `beta/dt` velocity gain (~4.2)
   turns ~18 m of position residual into **~75 m/s** of velocity error on a
   ~200 m/s target, corrupting LOS rate by **0.66x its own magnitude**.
   Position error was fine (~14 m) the whole time, which is why CP0's
   position-only check passed it. Sweep: alpha 0.2 gives velocity error
   18 m/s and LOS-rate error 0.16x; 0.05 over-smooths and degrades again.
   **Fixed: `TrackingConfig.alpha` 0.5 → 0.2.** Same class of error as the
   CP0 update-rate finding: a spec constant transplanted from a 100 Hz loop.
2. **Miss penalty saturated.** `miss_penalty * tanh(min_range / 1000 m)` has
   gradient 0.0099 at 3 km and 0.0002 at 5 km. From a 7 km start an
   untrained policy misses by 1–5 km — entirely inside that dead zone, with
   nothing to pull it back. That is why the lineage *degraded* monotonically
   rather than merely stalling. **Fixed: scale → 3000 m** (gradient 0.133 at
   a 5 km miss, ~650x more signal).
3. Also raised `timesteps_per_checkpoint` 20,480 → 204,800 for this lineage.

**Post-fix confirmation (same 204,800-step budget):** evasive + tracking goes
from 0/20 (median 557 m) to **2/20 (median 35.4 m)**. Real improvement, but
still short of the tracking-off arm's 7/20 / 8.6 m — so a residual tracking
cost remains and should not be papered over.

Note the shaping term reporting a constant 27.11 across checkpoints is
expected, not a bug: potential-based shaping telescopes, so its undiscounted
episode sum is policy-independent by construction.

## 2026-09-12 — Re-derived the `weave_3g_055hz` diagnosis (no new runs)

- Forced by the CP0 finding that a phase-0 weave drifts rather than
  mean-reverts. Used only existing `outputs/shadow_comparison/` data plus
  target-only integration; no policy retraining, no eval re-run.
- **The "RL over-drove lateral command" explanation is falsified.** RL's
  mean commanded lateral is 124.9 / 125.3 / 126.3 m/s² on the three weave
  cases — indistinguishable — and it **hits** two of them. Peak command is
  at the shared 245.2 m/s² clamp for every mode on every weave case. An
  attribute equally present in the wins cannot explain the loss.
- **Re-derived cause: a sustained-lead failure.** Weave drift in y is
  `−(A/ω)·cos φ`. `weave_3g_055hz` is the only weave case whose drift moves
  the target *away* from the interceptor's axis (−300 → −438 m) and it has
  the largest drift magnitude (8.51 m/s). The other two drift back toward
  the axis, which helps the intercept.
- Corroborating: PN posts its **tightest** weave miss (0.2 m) on exactly
  that case — expected, since constant lateral drift makes the target a
  constant-velocity target on a rotated heading, PN's ideal geometry. And
  RL converges at essentially the same time as PN on the two it hits
  (17.70 vs 17.62 s; 20.14 vs 20.02 s), so it is not generally slower.
- Untested hypothesis (flagged as such in the doc, not relied on):
  `training_maneuver_factory` samples phase `uniform(0, 2π)`, so `cos φ` is
  symmetric and drift averages out across training — the policy may see
  drift as noise rather than a feature to lead. Needs a phase-stratified
  eval to confirm or kill.
- **Consequence for CP1 — the spec's §5 conclusion inverts.** Retiring
  `SinusoidalWeave` does not retire this weakness: break turn / vertical
  jink / Split-S all open far more sustained separation than an 8.5 m/s
  weave drift, so v1 stresses this failure mode harder. Marked §5
  SUPERSEDED in the spec; CP1 should measure sustained-lead capability
  explicitly rather than treat the question as retired.

## 2026-09-12 — CP0: evasive maneuver library + tracking chain (no training)

- Scope as gated: infrastructure only. No training run, no checkpoint, no
  `CURRENT_RL_BASELINE.json` change. **CP1 not started.**
- New maneuvers in `physics/maneuvers.py`: `BreakTurn` (t_go- or
  time-triggered, commits once fired), `VerticalJink` (ramped pull-up/dive,
  stops at `altitude_delta_m`), `SquareWaveJink` (optionally non-periodic;
  reversal schedule drawn up front so `lateral_accel` stays a pure function
  of `t`), `SplitS` (roll approximated as the lift vector rotating, since the
  point-mass target carries no attitude state), `ManeuverSequence`.
- Added an additive `ManeuverProfile.update_engagement(t, target, pursuer)`
  hook (default no-op) so t_go-triggered maneuvers can see engagement
  geometry without changing the `lateral_accel` signature every profile
  implements.
- `InterceptionEnv` gains `TrackingConfig`: per-episode sampled seeker
  latency (20–80 ms) and update rate, `AlphaBetaFilter` estimate feeding
  `_kinematics`/observations/ZEM shaping, plus two new obs channels
  (`time_since_update_scaled`, `estimate_uncertainty_scaled`).
- **Truth/estimate split enforced:** hit detection, `min_range_m`, and
  `info["range_m"]` stay ground truth (downstream metrics/viz depend on it);
  the estimate feeds observations and shaping only. Observed range is
  reported separately as `observed_range_m`.
- Tracking defaults **off** at the env level (spec said on) — flipping it on
  broke 7 tests by changing the frozen 10-D obs contract that rollout
  capture, shadow compare, live inference and the CP5 checkpoint all depend
  on. CP1 turns it on via `PPOTrainingConfig`.
- `use_target_turn_rate_obs` + tracking now raises: that channel is computed
  from privileged ground-truth target acceleration.
- **CP0 disproved four spec claims** — see the "CP0 results" section added to
  `docs/evasive-tracking-redesign-spec.md`. Most consequential: the weave is
  NOT bounded at every phase. Integrating `A·sin(ωt)` leaves a DC velocity
  offset `A/ω`, so a phase-0 weave drifts (188 m / 20 s at 5 g) while a
  phase-π/2 one stays in a ~14 m corridor. `weave_3g_055hz` — RL's only
  Group A loss to PN — is precisely the phase-0, lowest-frequency, maximum-
  drift case, so the "RL over-reacts to a bounded oscillation" story in
  `docs/rl-justification.md` §3 needs re-deriving before it is reused.
- Also corrected: staleness must be age-of-information (stamped from the
  measurement's sample time), not time-since-delivery, which is identically
  zero when the seeker runs at/above the control rate; and the spec's
  {50, 100} Hz update rates both exceed this codebase's 50 Hz control loop,
  so they are now {25, 50}.
- Tests: `tests/test_evasive_maneuvers.py` (18), `tests/test_tracking_env.py`
  (14). Full suite 134 green, no existing test modified.

## 2026-09-12 — WS scenario picker now runs a live episode, not a canned replay

- Root cause of "the picker doesn't seem to control the target, path is
  always the same, interceptor never misses": `rollout_stream.py` mapped
  all 3 catalog scenarios to just **2** captured RL-rollout files
  (`crossing-intercept`/`head-on-intercept` both replayed
  `no_maneuver_demo`), `guidance_law` was explicitly discarded
  (`del guidance_law`), and live speed sliders were validated/echoed but
  never reshaped the frozen frames. Those 2 files were also both Group A
  checkpoint *wins*, so nothing evasive/hard was ever shown.
- New `src/guidance_sim/api/live_stream.py` replaces it as the
  `/ws/trajectory` data source: each request runs a fresh
  `InterceptionEnv` episode. Scenario → target maneuver family is now
  real (`crossing-intercept`→NoManeuver, `head-on-intercept`→ConstantTurn,
  `evasive-climb`→SinusoidalWeave), randomized in magnitude/direction/
  phase per episode; `guidance_law` (PN/APN/OGL) actually drives the
  interceptor via the same classical-law wrap `shadow_compare.py` uses;
  `interceptor.speed`/`target.speed` overrides reshape the initial
  conditions instead of being cosmetic. No seed pinned by default, so
  replaying the same scenario twice gives two different engagements.
- `rollout_stream.py` and its tests are left in place, unused by
  `main.py` now — read-only fixed-case replay may still be useful for
  debugging against a known captured episode, not deleted outright.
- `guidance_sim.rl` (physics/training/environment) untouched — this only
  rewires which code the WS handler calls and what it's allowed to see.
- Frontend copy updated to stop calling this "synthetic"
  (`AppHeader.jsx`: "SYNTHETIC STREAM"→"LIVE STREAM",
  `SetupScreen.jsx`: "RUN SYNTHETIC PREVIEW"→"RUN LIVE ENGAGEMENT") and
  catalog scenario/guidance descriptions updated to match.
- Tests: rewrote `tests/test_api_stream.py`'s rollout-replay assertions
  (fixed closest-approach value, "overrides don't reshape", "guidance_law
  ignored") for the new contract, added regression tests that two runs
  of one scenario differ and that scenarios drive distinct target
  maneuvers. Full suite green (102 backend, 19 frontend).
- Not done yet: RL is still only reachable via the separate
  `/api/guidance/session` REST endpoint, not wired into this picker; and
  target behavior is still limited to NoManeuver/ConstantTurn/
  SinusoidalWeave — genuinely evasive maneuvers are the separate,
  larger `docs/evasive-tracking-redesign-spec.md` retrain, not touched
  here.

## 2026-09-11 — Evasive tracking redesign spec (scoping only)

- Wrote `docs/evasive-tracking-redesign-spec.md`: scoping document for a
  future RL environment redesign (genuine evasion maneuvers + delayed/
  estimated tracking). No code, environment, or training changes.
- Corrects framing: `Simulation` already wires sensor/estimator end to
  end for classical guidance; `InterceptionEnv`/`shadow_compare.py` do
  not (they step entities directly against ground truth) — so this is
  "route RL/shadow harness through the existing sensor path," not
  net-new estimation infrastructure.
- Proposes v1 maneuver set (break turn, vertical jink, randomized jink,
  Split-S, sequences), demotes `SinusoidalWeave` to a retained
  low-effort perturbation case, flags that `use_target_turn_rate_obs`
  is privileged ground truth and must be dropped or reworked, and
  proposes raising `max_time` 25s → 45s.
- Every checkpoint (CP0–CP5) requires separate explicit sign-off before
  running, same gating as prior CP1–CP5 lineages. No training started.

## 2026-09-11 — RL justification doc (shadow results only)

- Wrote `docs/rl-justification.md` from
  `outputs/shadow_comparison/shadow_comparison_report.md` only — no new
  evals, no physics/guidance/rl edits.
- Claim framed as 2/9 clear wins, 3/9 clear losses, 4/9 comparable; keep
  RL as comparable + narrow 3 g budget-edge arm, not “beats classical.”

## 2026-09-11 — Shadow-mode PN/APN/OGL vs RL baseline

- New read-only harness: `src/guidance_sim/evaluation/shadow_compare.py`
  + `scripts/run_shadow_comparison.py`. Does **not** touch physics/,
  guidance/, rl/ training, or `CURRENT_RL_BASELINE.json`.
- Reuses `FIXED_EVALUATION_CASES` / `_case_*` / `PPOTrainingConfig`
  (25 s, dt=0.02) from `rl.training`, classical action wrap from
  `validate_reward.py`, and RL replay path from `evaluate_policy` /
  `capture_rl_rollout.py`. All four modes step the same
  `InterceptionEnv` so target trajectories match.
- Artifacts: `outputs/shadow_comparison/shadow_comparison_report.md`,
  `.json`, `.csv`.
- Head-to-head (HIT miss-m): Group A classical mostly wins on weave;
  RL sole Group A miss is `weave_3g_055hz` (7.4 m vs PN hit 0.2 m).
  Group B all miss: PN 975/1194/2164 m; RL 832/1453/2515 m — RL beats
  PN only on 3 g; APN/OGL much worse (rotating a_T). Confirms budget
  ceiling diagnosis, not a training gap.
- Tests: `tests/test_shadow_compare.py` (6). Full suite green after add.

## 2026-09-11 — WS data_source label: synthetic → rollout

- `DataSource = Literal["synthetic", "rollout"]`. Live catalog +
  `/ws/trajectory` envelopes set `data_source="rollout"`. Schema defaults
  remain `"synthetic"` for the mock_stream / trial-overlay path.
- Frontend store `activeDataSource` tracks envelope `data_source` (live
  restream gated on `"rollout"`). Frame payload fields unchanged.

## 2026-09-11 — Target B fighter-class re-grounding

- Chose direction **(a)**: Target B stays an ADMIRE-scale fighter/attack
  airframe; speed dropped from missile-class **500 m/s** to **240 m/s**
  (review range **200–300**, step 5). Mass 9,100 kg / wing 45 m² / Cd
  0.035 / Cn_max 1.1 / 9 g unchanged.
- Speed sources: `FOI-ADMIRE-2005`, `AIAA-CLIMB-2024` (242 m/s example →
  240), `GENERIC-MISSILE-1994` (Mach 0.7 aircraft/target),
  `PN-FUZZY-2020` (300 m/s upper edge). Removed `NPS-GUIDANCE-2000` from
  Target B speed (kept only as Interceptor/geometry anchor in the doc).
- Docs + catalog + setup note updated. UI reads catalog dynamically so
  SET/HUD/sliders pick up 240 without hardcoded frontend constants.
- RL rollout stream unchanged: frozen eval kinematics ignore catalog
  speed; assumption confirmed (loader echoes overrides only).
- Guardrails: viz branch only; no physics/guidance/rl/training edits.

## 2026-09-11 — wire RL baseline rollouts into WS stream

- Mock path was `api/mock_stream.build_mock_trajectory` →
  `api/main.trajectory_stream` (`/ws/trajectory`). Replaced that call with
  `api/rollout_stream.build_rollout_trajectory`.
- Capture (read-only vs training worktree): `scripts/capture_rl_rollout.py`
  loads `outputs/CURRENT_RL_BASELINE.json` →
  `rl_checkpoint_05.zip`, runs one fixed-eval episode, writes
  `outputs/rl_rollouts/{case}.json`. Captured Group A hits:
  `no_maneuver_demo` (miss 1.229 m) and `weave_5g_070hz` (miss 4.117 m).
- Scenario map: `crossing-intercept`/`head-on-intercept` →
  `no_maneuver_demo`; `evasive-climb` → `weave_5g_070hz`. ConstantTurn has
  no baseline hit (Group B 0/3), so it reuses the NoManeuver demo.
- Schema unchanged: `pursuer_accel_cmd_m_s2` /
  `pursuer_accel_achieved_m_s2` filled from env `action_commanded_m_s2` /
  `action_achieved_m_s2` (post radial clip / post lag+clamp). Terminal
  sample zeroed to match `SimulationResult` intercept convention.
  `DataSource` remains `Literal["synthetic"]` (no schema edit); health
  root string says `rl_rollout` for operators.
- Live speed overrides still validated/echoed; they no longer reshape the
  path (frozen rollout). Guidance-law selector is protocol-only.
- Left `mock_stream.py` in tree for frontend trial-overlay helpers; WS
  path no longer calls it.
- Gotcha: per-step `|achieved|` can exceed `|commanded|` under autopilot
  lag (achieved tracks a delayed command). Both stay ≤ structural 25 g.
- Verification: capture scripts hit-confirmed; pytest on viz suite after
  swap. Visual smoke: restart `:8000` and RUN PREVIEW NoManeuver.

## 2026-09-10 — visualization scope finalize (speed, labels, accel WS)

- Target B speed reframed as missile-class: catalog **500 m/s** (range
  300–600), primary source NPS ADA378653 / `NPS-GUIDANCE-2000`. Live
  slider step 10. Mass/area/Cd for Target B still cite fighter/transport
  anchors — flagged as remaining incoherence in the sourcing doc.
- Scenario picker labels → **NoManeuver / ConstantTurn / SinusoidalWeave**.
  Ids and `_GEOMETRIES` mock paths unchanged (labeling only).
- `trajectory.frame` now includes `pursuer_accel_cmd_m_s2` and
  `pursuer_accel_achieved_m_s2` (mock lateral; terminal zeros). HUD g-load
  prefers achieved when present.
- Docs: `docs/scenario-parameter-sources.md` rewritten as current spec
  (speed + RL taxonomy table + WS accel caveat), not a decision log.
- Verification: Python **56 passed**; frontend **19 passed**. Manual smoke
  against restarted `:8000`/`:5173`: SET picker shows NoManeuver /
  ConstantTurn / SinusoidalWeave; Target B slider 500 m/s (300–600);
  RUN PREVIEW streams to HUD with Target B SPD ≈500 and intercept lock;
  SinusoidalWeave restream also succeeds. WS frames carry both accel
  fields (terminal zeros).
- Remaining roughness (not blocking this pass): Target B mass/area/Cd
  still fighter/transport-grounded while speed is missile-class; HUD
  consumes achieved for lateral-G but does not yet render a dedicated
  cmd-vs-achieved readout; ConstantTurn is label-only over the old
  head-on mock geometry.
- Guardrails: no physics/RL/guidance edits; stayed on
  `feature/rl-visualization`; checkpoint eval still out of scope.

## 2026-09-09 — mock RL visualization workflows

- Live sliders read `live_control` + `reference_min/max` from `/api/catalog`.
  Only interceptor/target speed are marked live so far; mass/Cd/Cn can be
  promoted later without a frontend rewrite. Slider changes debounce 300 ms
  and restream the synthetic trajectory.
- All-trials overlay is generated by `loadTrialSet()` / `generateMockTrialSet()`
  from the current synthetic path. Opacity rises with episode index; green
  is intercept, pink is miss. This is **not** an RL rollout log.
- Training dashboard and `#/training` consume `loadTrainingLog()` which
  currently fetches `frontend/public/mock/training-log.json`.
- Last-session replay uses `loadTrajectoryLog()` against
  `frontend/public/mock/last-session.json` or a user-selected JSON file, then
  reuses the existing playback store/controls.
- Verification: Python **56 passed** (was 54; catalog/stream override tests);
  frontend **17 passed** (was 4). ESLint clean. Production app chunk
  `index-*.js` 13.05 → 24.99 kB (+11.94 kB; gzip 4.57 → 8.13 kB). `vendor-r3f`
  unchanged at 1,115.07 kB / 306.70 kB gzip.
- Guardrails held: no physics/guidance/RL training edits; stayed on
  `feature/rl-visualization`.

## 2026-09-09 — interactive visualization scaffold

- Added a FastAPI catalog plus `/ws/trajectory` protocol:
  `stream.start` → `stream.started` → ordered `trajectory.frame` messages →
  `stream.completed`. Invalid start messages return `stream.error`.
- The current data source is deliberately and visibly `synthetic`. No
  checkpoint discovery, loading, model import, or evaluation adapter was
  added; that work remains gated on a stable observation-v2 format.
- Added a Vite/React viewer using the portfolio's R3F, Drei, and Zustand
  stack. It maps simulation `[x,y,z]` metres (z-up) to Three `[x,z,-y]`
  kilometres (y-up), supports orbit/pan/zoom, local play/pause/restart,
  scrubbing, playback rate, telemetry, and scenario/guidance selectors.
- Generic `Interceptor A` / `Target B` catalog values are exposed with
  source IDs, source ranges, and `synthesized`/`illustrative` labels.
  Full citations and conventions are in
  `docs/scenario-parameter-sources.md`; no named system is modeled.
- Gotcha: constant `Cd` and `Cn_max` values are reduced-order review
  placeholders. Reference-area conventions differ (interceptor frontal area,
  target wing area), so these values must not be mixed or presented as
  class-wide constants.
- Python 3.14 on this macOS worktree skips the editable install's `.pth`
  file when that file inherits the hidden flag under `.venv`. The documented
  Uvicorn command uses `--app-dir src`, which is deterministic and avoids
  relying on editable-path processing.
- Verification: baseline **42 passed**; final Python suite **54 passed**;
  frontend **4 passed**, ESLint clean, production build successful. Browser
  verification confirmed catalog GET 200, WebSocket acceptance, 101 rendered
  frames, local playback, a 3.2 m synthetic closest approach, and no app error
  overlay.
- Non-blocking build tradeoff: the R3F/Drei vendor chunk is about 1.1 MB
  minified (307 kB gzip), above Vite's default warning threshold. Route-level
  lazy loading can be considered when this viewer is embedded in the wider
  portfolio.
- Guardrails held: no edits under `physics/`, `rl/`, or `guidance/`.
## 2026-09-10 — Priority 1: seeker noise + α-β estimator

Credibility improvements Priority 1 / AGENTS Step 5a–5b (alpha-beta only).

- **Sensor layer** (`sensors/measurement.py`, alias `seeker_model.py`):
  `SeekerNoiseConfig` (az/el/rate/range/range-rate stds) + `SensorConfig`
  (update rate, Pd, latency) + `Sensor.measure` → optional `Measurement`.
  Defaults ~1 mrad angle noise (literature order-of-magnitude; full citations
  deferred to Priority 4 / `REFERENCES.md`).
- **Estimator** (`estimation/alpha_beta.py`, alias `filter.py`): fixed-gain
  α-β with `beta = alpha²/(2-alpha)`. Consumes noisy spherical measurements,
  outputs filtered Cartesian target `State`. Guidance never sees raw noise.
- **Engine wiring**: optional `sensor` + `estimator` + `rng` on `Simulation`.
  Omitted → perfect-information path unchanged (legacy tests).
- **Regression**: `test_miss_distance_degrades_with_seeker_noise` sweeps
  scales `{0,2,5,12}` (7 seeds); requires Spearman(ρ)≥0.6 and high≫low miss.
  Artifact script: `scripts/run_seeker_noise_sweep.py` →
  `outputs/seeker_noise_sweep.{csv,png}`.
- Gotcha: zero-noise α-β still has lag, so median miss can dip slightly at
  mild noise vs the filter floor — hence near-monotonic (Spearman) not
  pairwise-strict.
- Verified: focused seeker tests + full suite **71 passed**. Did not start
  Priority 2 (Monte Carlo harness).

## 2026-09-10 — Eval Group A/B reporting split + CP4


Reporting-only change (no reward / action / obs / max_time / scenario edits).

- **Group A** (feasible-within-budget; drives stop): NoManeuver×3 + Weave×3
- **Group B** (budget-constrained; tracked only): ConstantTurn×3
  Classical PN/APN/OGL all miss Turn under frozen 25 s
  (`outputs/constant_turn_feasibility_diagnostic.json`).
- Progress log now prints Group A/B hit/miss/reward/effort alongside pooled
  9-case metrics. Stop = two consecutive Group-A non-improvements on
  reward + miss + hit together.

### Retroactive CP1–3 (from logged cases)

| CP | A hits | A miss mean/med | A reward | B hits | B miss mean/med |
|---|---|---|---|---|---|
| 1 | 0/6 | 241.0 / 213.6 | +1.0 | 0/3 | 1167 / 1015 |
| 2 | 4/6 | 4.1 / 3.6 | +89.5 | 0/3 | 1473 / 1464 |
| 3 | 4/6 | 5.8 / 4.2 | +83.3 | 0/3 | 1615 / 1440 |

CP2→CP3 Group A did **not** improve (hits flat, miss/reward slightly worse).
Pooled CP3 warning was **not** only Group B noise — Group A also stalled.

### Checkpoint 4 (unchanged training config)

- **81,920 cumulative / 16 new episodes**. Training return −17.70 → +24.10.
- Pooled: **3/9 hits (33.3%)**; miss **529.280 / 6.030 m**; return **+19.138**
  (shaping 25.274 / effort −10.930 / terminal +4.794); effort **197488**.
- **Group A: 3/6** hits, miss 5.759 / 5.186 m, reward +59.888, effort 274847
  — **regressed vs CP3** (lost Weave hits; NoManeuver still 3/3).
- **Group B: 0/3**, miss 1576 / 1414 m, reward −62.364 (still near classical
  ceiling under this budget).
- Per-case miss (m): NoManeuver 4.75 / 4.36 / 3.58 **hit**; Turn 813.9 /
  1413.8 / 2501.3; Weave 5.62 / 10.22 / 6.03 (all miss, near lethal).
- Group-A stop warning: **True** (CP2→CP3 and CP3→CP4 both non-improving
  on Group A). **CP5 not started.**
- Full suite **57 passed**.

## 2026-09-10 — From-scratch retrain CP3 (lateral2 + new reward)

- Resumed CP2 only; reward / action / obs / domain-rand unchanged.
  Effort-weight annealing **not** applied.
- **61,440 cumulative / 16 new episodes**. Training return improved within
  CP3 (−12.352 → +9.796). Fixed-eval vs CP2: hit rate flat 4/9, mean miss
  worsened 493.9 → 542.1 m, eval return worsened +39.92 → +34.39.
  Harness `convergence_warning=True` (streak=1). Per stop rule this is the
  first non-improving joint transition; CP4 not started per instructions.
- New return **+34.387** (shaping 25.274 / effort −6.343 / terminal +15.456);
  legacy **+51.242**. Control effort rose again 29302 → **102900** m²/s³.
  Cmd/achieved RMS **50.10 / 43.50** (still matched); along-track **~0**.
  Outcomes: **0 ground / 5 timeout / 4 hit**.
- Per-case miss CP1 → CP2 → CP3 (m):
  - NoManeuver c/d/o: 113.7→1.4→**0.2 hit**, 219.5→3.2→**4.9 hit**,
    374.7→3.9→**3.4 hit**
  - Weave 3/5/7 g: 207.8→2.0→**3.1 hit**, 202.8→8.3→14.1,
    327.5→5.6→8.9
  - ConstantTurn 3/5/7 g: 431.9→702.2→**877.0**, 1014.8→1464.2→**1440.3**,
    2054.1→2253.9→**2527.3**
- **ConstantTurn: continues diverging** (3 g and 7 g worse than CP2; 5 g
  only −24 m vs CP2 and still far worse than CP1). Lagging class unchanged.

### ConstantTurn diagnostic (CP3 policy, no config changes)

Compared frozen eval `constant_turn_left_3g` vs successful `weave_3g_055hz`.
Artifact: `outputs/constant_turn_diagnostic_cp3.json`.

- Trajectory: Turn still closing at timeout (R 6500→877 m, min at t=25 s).
  Weave intercepts at t≈16.5 s (R→3.1 m). At Turn timeout, separation is
  mostly **along-track** (dx≈869 m) not cross-track (dy≈63 m) — pursuer
  trails the circling target rather than flying past laterally.
- Command character: Turn has **sustained asymmetric bias** (bias energy
  fraction 0.52, mean sign run 3.6 s, ZCR 0.005). Weave is oscillatory /
  near-symmetric (bias ≈0, mean sign run 0.44 s, ZCR 0.045). Failure is
  **not** “policy only knows how to weave.”
- Timing: closing is established early (Vc>0 throughout); failure is
  **never completing intercept within max_time** (still closing at end),
  not a late near-miss that reopens after a close approach.
- Shared-cause flag vs prior APN/ConstantTurn finding: **same scenario
  class, different mechanism.** APN’s issue is constant-a_T; this policy
  already applies sustained lateral bias. Shared factor is that
  ConstantTurn’s rotating accel geometry is harder under the frozen
  observation — not that RL inherited the APN modeling error.

Saved-model reload OK; full suite **56 passed**. **CP4 not started.**

## 2026-09-10 — From-scratch retrain CP2 (lateral2 + new reward)

## 2026-09-10 — From-scratch retrain CP2 (lateral2 + new reward)

- Resumed CP1 only; reward / action / obs / domain-rand unchanged.
  Annealing fallback **not** applied (`effort_weight` stays 5).
- **40,960 cumulative / 16 new episodes**. Within-checkpoint *training*
  return regressed (−13.879 → −43.075), but fixed-eval improved on all
  three stop metrics: hit rate, miss, and eval return.
- Fixed eval: **4/9 hits (44.4%)**; mean/median miss
  **493.862 / 5.604 m** (CP1: 549.644 / 327.484). Mean is outlier-driven;
  median collapsed because four cases are now intercepts.
- New return **+39.915** (shaping 25.274 / effort −2.066 / terminal +16.707);
  legacy **+53.404**. Effort share rose with higher lateral activity
  (control effort 4429 → 29302 m²/s³) but remains secondary.
- Cmd/achieved RMS **31.67 / 28.98** m/s² (matched); along-track fraction
  still **~0**. Outcomes: **0 ground / 5 timeout / 4 hit**.
- Per-case miss CP1 → CP2 (m):
  - NoManeuver center/demo/offset: 113.7→**1.4 hit**, 219.5→**3.2 hit**,
    374.7→**3.9 hit**
  - Weave 3/5/7 g: 207.8→**2.0 hit**, 202.8→8.3, 327.5→5.6
    (5 g / 7 g are just outside the 5 m lethal radius)
  - ConstantTurn 3/5/7 g: 431.9→**702.2**, 1014.8→**1464.2**,
    2054.1→**2253.9** — **lagging class; absolute miss worsened**
- Spread diagnosis: CP1's mean≫median was mixed; CP2's mean≫median is
  specifically ConstantTurn. NoManeuver is solved; Weave is near-hit;
  Turn is the remaining failure mode.
- Convergence warning: False (hit/miss/eval-return all improved vs CP1).
  Saved-model reload OK; full suite **56 passed**. **CP3 not started.**

## 2026-09-10 — From-scratch retrain CP1 (lateral2 + new reward)

## 2026-09-10 — From-scratch retrain CP1 (lateral2 + new reward)

### Annealing clarification (before training)

Frozen `RewardConfig.terminal_weight` is already **1.0**. The earlier
fallback that raised `0.5 → 1.0` would be a no-op under this freeze, and
with 0/9 hits for four prior checkpoints the `<10%` band is the expected
path. Revised fallback (**not applied**; train under current freeze):

- Trigger: two consecutive checkpoints with `hit_rate < 0.10` **and** no
  mean-miss improvement.
- Action: keep `terminal_weight=1.0`; **raise `effort_weight` 5 → 15** so
  wasteful lateral chatter becomes visible; optionally lower
  `shaping_weight` 50 → 35 only if shaping share exceeds ~40% of
  `|reward|` while miss stalls. Do not touch the terminal scale.

### Checkpoint 1

- Fresh run (not a resume). Old world3/v2 artifacts archived under
  `outputs/archive/observation_v2_world3/`.
- Contract: obs v2 (10), `lateral2`, domain randomization OFF, frozen
  9-case eval, seed `20260909`.
- **20,480 steps / 16 episodes.** Train return improved within CP1:
  **-53.655 → -51.662** (+1.993).
- Fixed eval: still **0/9 hits**, but mean/median miss
  **549.644 / 327.484 m** (old v2 CP1 was 2638.7 / 2618.8 m).
- New return **-14.544** (shaping 25.274 / effort −0.364 / terminal −39.454);
  legacy diagnostic **-46.323**.
- Control effort **4429** m²/s³. Commanded/achieved RMS **12.86 / 12.76**
  m/s²; along-track energy fraction **~0** (null space gone).
- Outcomes: **0 ground / 9 timeout / 0 hit**.
- Saved-model reload reproduced metrics; full suite **56 passed**.
  **Checkpoint 2 not started.**

## 2026-09-10 — t_go continuity at closing/receding boundary (no retrain)

## 2026-09-10 — t_go continuity at closing/receding boundary (no retrain)

### Quantification (pre-fix)

Collinear sweep at `Vc = 1 ± ε` with the old branch
(`closing → min(R/Vc, 25)` vs `receding → 5 s`):

| range (m) | \|ΔΦ\| | \|Δ shaping\| (`w=50`) |
|---|---|---|
| 500 | 0.0103 | **0.515** |
| 1000 | 0.0045 | 0.227 |
| 3000 | 0.0008 | 0.041 |
| 7000 | 0.0002 | 0.009 |

Episode shaping ≈ 25 over ~1250 steps ⇒ mean per-step ≈ 0.02. The R=500
jump is ~25× that — material for learning gradients on weaving targets that
cross `Vc ~ 0`. Fixed.

### Formulation

Branch removed. Single continuous horizon:

```
t_go = min(range / max(|Vc|, vc_min), t_go_max)
```

`t_horizon_receding_s` retained on config for dump compatibility, unused.
Post-fix adjacent `|ΔΦ|` at the old boundary is ~1e-11 (float noise).

### Offline validation (corrected gate 2)

All three gates **PASS**:

1. Classical hit ≫ miss — unchanged.
2. CP2/CP3/CP4 new-reward order matches miss order: **CP3 > CP2 > CP4**
   (returns −52.31 / −65.79 / −68.47; misses 1238 / 1787 / 1950 m).
   Supersedes the mis-specified “CP3/CP4 clearly worse than CP2”.
3. Flyby ≫ loiter — unchanged.

### Annealing fallback (proposed, not applied)

If hit rate never exceeds 10%: after two consecutive checkpoints with
`hit_rate < 0.10` and no mean-miss improvement, raise `terminal_weight`
0.5 → 1.0 while keeping `shaping_weight=50`. Do not drop shaping. Current
freeze remains `shaping_weight=50`, `terminal_weight=1`.

Full suite **56 passed**. Artifact updated:
`outputs/reward_redesign_validation.json`.

## 2026-09-10 — Reward redesign + offline validation (no retrain)

## 2026-09-10 — Reward redesign + offline validation (no retrain)

Gate **failed**. No retrain. Weights were not retuned after seeing the
gate.

### 1. Action space (isolated to the RL wrapper)

`GuidanceLaw.compute_command` stays world-frame `(3,)`. `clamp_lateral_command`
and `PointMassEntity.step` were not edited. Training now uses `lateral2`: a
2-vector on an orthonormal basis of the velocity-normal plane, radially
clipped at 25 g, then passed to `entity.step`. Archived 3D policies replay
through `action_layout="world3"`. Frozen PN/APN/OGL code is untouched.

### 2. Reward

- Dense: PBRS `shaping_weight * (γ Φ(s′) − Φ(s))` with `γ = 1` so logged
  undiscounted returns telescope. `Φ = −ZEM / (ZEM + 500 m) ∈ (−1, 0]`,
  identically 0 at hit/miss/timeout/ground. Bounded form is required:
  unbounded `−ZEM/scale` plus Φ=0 at timeout paid out kilometres of residual
  miss as a bonus that beat true intercepts.
- Terminal: `+100` on hit; otherwise
  `−100 * tanh(closest_approach / 1000 m)` using episode-minimum range.
- Effort: `−5 * dt * (||a_achieved|| / a_structural)²` (post-clamp). The
  along-track exploit is removed structurally; this term is intentionally
  small.
- Phase-1 reward is logged in parallel as `legacy_*` / `legacy_episode_reward`.

### 3. ZEM safeguards

Kinematic ZEM only (`r + v t_go`, no target accel, no LOS rate). Closing:
`t_go = min(range/Vc, 25 s)` when `Vc > 1 m/s`. Receding: fixed 5 s horizon.
Range ≤ intercept radius → ZEM = 0. Episode clock is **not** used as a
`t_go` cap (that made Φ a function of `max_time` and inflated ZEM near
timeout). Unit tests: receding target, near-zero range.

### 4. Term shares (representative classical + flyby/loiter set)

| term | mean |abs| | share |
|---|---|---|
| shaping | 25.03 | 21.2% |
| effort | 3.22 | 2.3% |
| terminal | 93.62 | 76.5% |

Effort is still small. That is the 2D-action design, not a guess after the
gate. Proposed annealing (not applied): keep `shaping_weight=50` until hit
rate > 10%, then `terminal_weight` 0.5 → 1.0; after 40% hit rate drop
`shaping_weight` to 15.

### 5. Domain randomization

Implemented (`randomized_initial_conditions` / `randomized_maneuver_factory`),
**default off**. `PPOTrainingConfig.domain_randomization is False`. The 9-case
eval set is unchanged.

### 6. Offline validation

- **Gate 1 PASS.** PN/APN/OGL demo intercepts ~125 vs same-IC forced-timeout
  misses ~−67 to −80.
- **Gate 2 FAIL.** 9-case replay of v2 CP2/3/4 (`world3`): CP2 **−65.79**,
  CP3 **−52.31** (13.48 *better*), CP4 **−68.47** (only 2.68 worse, below the
  10-point “clearly worse” margin). Shaping is identical across the three
  (~25.27) because they share ICs and Φ_T=0; the ranking is closest-approach
  terminal. CP3’s 1238 m mean miss beats CP2’s 1787 m. Achieved-effort is
  ~−0.3 at all three; along-track command waste is not in the new cost.
- **Gate 3 PASS.** Same-IC ballistic flyby **−21.85** (min range 509 m) vs
  max-g turn-away loiter **−95.53** (min range 6070 m).

Stopped here. Do not retrain until the gate is redesigned or explicitly
waived.

Full suite **55 passed**. Artifact:
`outputs/reward_redesign_validation.json`.

## 2026-09-09 — Observation-v2 RL checkpoint 4 (stop condition met)

- Resumed only the ten-value checkpoint-3 model for **20,480 additional
  timesteps**: **81,920 cumulative / 64 episodes**. Training return regressed
  again within checkpoint 4, **-82.705691 → -86.333433** (-3.627741).
- Fixed evaluation: still **0/9 hits**; mean/median minimum separation
  **regressed** from **1238.474 / 1215.545 m** to
  **1950.092 / 1634.616 m** (+57.5% / +34.5%). Mean eval return worsened
  **-53.504263 → -61.134602**.
- Mean control effort grew again, **131902.118 → 150763.023 m²/s³**
  (+14.3%). Null-space characterization is unchanged and continues to grow:
  commanded RMS 72.6 → 77.5 m/s², still ~98% along-velocity
  (parallel 76.4 vs perpendicular 12.6 m/s² RMS), achieved lateral accel
  flat at ~12.3 m/s², DC-dominated (~90%), no reversals, no saturation.
  The policy keeps inflating the physically discarded along-track command.
- Eval outcomes: **0 ground impacts / 9 timeouts / 0 hits** — the
  altitude-observability crash suppression holds at every v2 checkpoint.
- **Stop condition (as redefined for this checkpoint): met.** Across
  checkpoints 3 and 4 jointly: reward shows no improvement (both
  regressed), hit rate shows no improvement (0/9 throughout), and miss
  distance shows no net improvement (CP2 1786.639 → CP4 1950.092; CP3's
  gain was given back). Checkpoint 3's fixed-eval improvement now reads as
  noise on a drifting policy rather than learning progress.
- Saved-model reload reproduced all metrics; full suite **47 passed**.
  **Checkpoint 5 was not started.** Candidate next steps for user decision:
  penalize the along-track (projected-out) component or use achieved-effort
  in the reward, add min-range or closest-approach credit so
  close-then-flyby trajectories are not score-equivalent to loitering, or
  restart from checkpoint 2 with a lower learning rate.

 ## 2026-09-09 — Observation-v2 RL checkpoint 3 (review gate)

- Resumed only the ten-value checkpoint-2 model for **20,480 additional
  timesteps**: **61,440 cumulative / 48 episodes**. Training return regressed
  within checkpoint 3, **-78.718274 → -85.372698** (-6.654424), with a late
  mean **10.443611** below checkpoint 2.
- Fixed evaluation moved in the opposite direction: still **0/9 hits**, but
  mean/median minimum separation improved from
  **1786.639 / 1423.028 m** to **1238.474 / 1215.545 m**
  (-30.7% / -14.6%), and mean eval return improved
  **-58.671985 → -53.504263**.
- Mean control effort rose sharply from **19305.963** to
  **131902.118 m²/s³** (**6.83×, +583%**), so effort growth is accelerating,
  not leveling off. Its mean normalized reward penalty was **-2.194474**
  versus **+48.690211** progress; it remains secondary but is no longer
  negligible.
- Eval outcomes remained **0 ground impacts / 9 timeouts / 0 hits**.
  Altitude observability continues to suppress the old crash pattern.
- The old eight-value run regressed in both reward and fixed-eval miss at
  this transition. That exact regression did **not** repeat: fixed-eval miss
  improved materially here. However, worsening sampled training return plus
  a 6.83× effort jump is a distinct possible recurrent-PPO/LSTM optimization
  instability, not evidence for the former observability root cause. The
  automated convergence warning is therefore retained.
- Saved-model reload reproduced all metrics; full suite **47 passed**.
  **Checkpoint 4 was not started.**

## 2026-09-09 — Observation-v2 RL checkpoint 2 (review gate)

- Resumed only the ten-value checkpoint-1 model for **20,480 additional
  timesteps**: **40,960 cumulative / 32 episodes**. Reward improved within
  checkpoint 2, **-78.815875 → -74.929087** (+3.886787), and its late
  quintile mean was **15.492101** better than checkpoint 1's late mean.
- Fixed evaluation remained **0/9 hits**, but mean/median minimum separation
  improved from **2638.656 / 2618.771 m** to
  **1786.639 / 1423.028 m** (-32.3% / -45.7%). Mean eval return improved
  **-69.585664 → -58.671985**.
- Mean command effort increased from **8716.993** to
  **19305.963 m²/s³** (+121.5%) as the policy became more active; its
  normalized reward penalty remained small (**-0.321196** mean).
- Eval outcomes were again **0 ground impacts / 9 timeouts / 0 hits**.
  Ground-impact cases therefore remain at zero for both observation-v2
  checkpoints, while hit rate is unchanged.
- Updated `outputs/training_progress.md` to persist control effort and
  ground-impact/timeout/hit counts at every checkpoint. Saved-model reload
  reproduced all checkpoint-2 metrics; full suite **47 passed**.
  **Checkpoint 3 was not started.**

## 2026-09-09 — Observation-v2 RL checkpoint 1 (review gate)

- Started the replacement run from scratch with the ten-value observation
  and unchanged reward. Completed **20,480 timesteps / 16 episodes**;
  checkpoint first-to-last reward-quintile mean changed
  **-72.083842 → -90.421188** (-18.337346).
- Fixed nine-case evaluation: **0/9 hits**, mean/median minimum separation
  **2638.656 / 2618.771 m**, and mean command effort
  **8716.993 m²/s³**. Mean reward components were
  **+30.559362 progress / -0.145026 effort / -100 terminal**.
- Eval outcome breakdown: **0 ground-impact misses / 9 timeouts / 0 hits**.
  The prior six-case post-flyby crash pattern is absent at this checkpoint,
  though one checkpoint cannot establish that altitude visibility caused
  the change and intercept performance remains poor. Training episodes
  contained one ground impact and fifteen timeouts.
- Saved and reload-verified `outputs/checkpoints/rl_checkpoint_01.zip`;
  full suite **47 passed**. **Checkpoint 2 was not started.**

## 2026-09-09 — Phase 2 restart prep: observability v2

- Diagnosed checkpoint 3 on the unchanged nine-case fixed set before editing
  the environment. Mean cumulative reward components were
  **progress +45.671857, effort -0.379796, terminal -100.0**. Per-case
  effort was only **0.6–1.2%** of positive progress. For the six geometries
  that had ground-impacted at checkpoint 2, means were
  **+45.605962 / -0.323107 / -100.0**.
- This **contradicts the passivity-is-rewarded hypothesis**: the terminal
  failure term dominates, while effort is two orders of magnitude smaller
  than progress. Reward weights were therefore left unchanged. Full
  breakdown:
  `outputs/archive/observation_v1/checkpoint_03_reward_breakdown.json`.
- Broke the observation contract deliberately from 8 to **10 float32
  values**, preserving the first eight and appending:
  `height_above_ground_scaled = max(z-ground,0) /
  (max(z-ground,0)+5000m)` and
  `altitude_rate_scaled = tanh(pursuer_vz / 200m/s)`.
  Height above the configurable ground plane is more meaningful than raw
  world z for ground avoidance.
- Repository search found no runtime consumer hard-coding the old `(8,)`
  shape outside the environment tests; the remaining mention is historical
  documentation below. Updated all six environment tests, training
  evaluation metadata, per-episode reward-component logging, and an explicit
  resume guard that rejects incompatible observation contracts.
- Archived the incompatible 8-value checkpoints 1–3 and their logs under
  `outputs/archive/observation_v1/`; they are diagnostic provenance only and
  must not be resumed. The active `outputs/checkpoints/` path is clear for a
  from-scratch replacement run.
- Verification: focused environment/training **11 passed**; full suite
  **47 passed**; Stable-Baselines3 environment checker passed (expected
  warning for the public physical action space; PPO still uses its normalized
  wrapper).
- **New training checkpoint 1 has not started: 0 replacement-run timesteps,
  0 episodes, no new checkpoint. Waiting at the review gate.**

## 2026-09-09 — Phase 2 RL checkpoint 3 (convergence stop)

- Pre-checkpoint diagnosis confirmed ground-impact misses and timeouts both
  receive a **-100 terminal term**, but remain distinguishable in Gymnasium
  outcome metadata. All six checkpoint-2 impacts were pursuer impacts in the
  three no-maneuver and three weave cases; every pursuer had already passed
  closest approach and was opening before impact. Constant-turn cases were
  still closing at timeout. This is a structured post-flyby/altitude-control
  pattern, not randomly distributed exploration. Absolute altitude is not in
  the current observation, so reward-only crash tuning may be insufficient.
- Resumed checkpoint 2 for **20,480 timesteps**: **61,440 cumulative /
  48 completed episodes**. Checkpoint 3's first-to-last reward-quintile mean
  was essentially flat/down, **-77.648933 → -78.043640** (-0.394707), and
  its late mean regressed **9.248909** from checkpoint 2.
- Fixed evaluation remained **0/9 hits**. Mean/median minimum separation
  regressed from **1471.504 / 1235.874 m** to
  **1984.544 / 2223.822 m** (+34.9% / +79.9%); mean return worsened from
  **-48.253773** to **-54.707939**.
- Mean command effort did improve again, **47082.088 → 22828.181 m²/s³**
  (-51.5%), and all nine cases now timed out instead of ground-impacting.
  That narrower positive does not offset the reward and miss-distance
  regressions.
- The checkpoint gate therefore flags a **possible convergence problem**.
  Saved and reload-verified `outputs/checkpoints/rl_checkpoint_03.zip`;
  full suite **47 passed**. **Checkpoint 4 was not started.**

## 2026-09-09 — Phase 2 RL checkpoint 2 (review gate)

- Resumed `rl_checkpoint_01.zip` for another **20,480 timesteps**:
  **40,960 cumulative / 32 completed episodes**. Checkpoint 2's
  first-to-last reward-quintile mean improved **-81.063848 → -68.794731**
  (**+12.269117**); its late mean is **+24.628672** above checkpoint 1's
  late mean.
- The fixed evaluation still has **0/9 hits**, but it is not flat:
  mean/median minimum separation improved from **2591.095 / 2451.082 m**
  to **1471.504 / 1235.874 m** (reductions of **43.2% / 49.6%**), and
  mean return improved **-69.176999 → -48.253773**.
- Mean fixed-eval command effort fell from **139167.240** to
  **47082.088 m²/s³** (**66.2%**). Outcomes were six physical
  ground-impact misses and three timeouts, so the policy is closer and less
  wasteful but is not yet producing a sane intercept.
- The two-consecutive-checkpoint convergence concern is **not triggered**
  because both reward and fixed-set miss distance improved materially.
  Checkpoint 3 was not started; the review gate remains in force.
- Saved `outputs/checkpoints/rl_checkpoint_02.zip` plus JSON evaluation and
  metadata; saved-model reload reproduced the metrics exactly. Full suite:
  **47 passed**.

## 2026-09-09 — Phase 2 RL checkpoint 1 (review gate)

- Initialized Git from the verified 42-test Phase-1 baseline
  (`3762d24`), then split work into `feature/rl-training` here and
  `feature/rl-visualization` at `../missile-sim-viz`. Both worktrees were
  clean and independently passed **42 tests** before Phase 2 edits.
- Chose recurrent PPO (`sb3-contrib` 2.9.0, `MlpLstmPolicy`, 64 hidden
  units) because partial observability makes the engagement history useful.
  The compute-bound budget is **102,400 timesteps**, split into five review
  checkpoints of **20,480**. Seed: **20260909**; 4 environments; `dt=0.02 s`.
- Training uses equal seeded sampling of `NoManeuver`, `ConstantTurn`, and
  `SinusoidalWeave` around the existing demo/envelope IC family. The public
  environment remains a physical 25 g action space; PPO uses a standard
  `[-1,1]^3` wrapper rescaled to that physical command before the unchanged
  lag/clamp/dynamics pipeline.
- Checkpoint 1 completed **20,480 timesteps / 16 episodes**. First-to-last
  reward-quintile mean changed **-73.775322 → -93.423403** (change
  **-19.648081**); this first checkpoint is not enough to trigger the
  two-consecutive-checkpoint convergence warning.
- Fixed nine-case evaluation: **0/9 hits**, mean/median minimum separation
  **2591.095 / 2451.082 m**, mean return **-69.176999**. All nine cases
  timed out. This is an honestly poor first checkpoint, not evidence of
  convergence.
- Artifacts: `outputs/checkpoints/rl_checkpoint_01.zip`,
  `outputs/training_curve.png`, `outputs/training_episodes.csv`,
  `outputs/rl_checkpoint_01_eval.json`, and
  `outputs/training_progress.md`. Reloading the saved checkpoint reproduced
  the evaluation exactly.
- Verification after implementation: focused **5 passed**; full suite
  **47 passed**. Checkpoint 2 was not started; waiting at the review gate.

## 2026-09-09 — Step 3: lag + APN + OGL

### 3a Autopilot lag
- `SimulationConfig.autopilot_tau` default **0.2 s** (typical short-range
  interceptor first-order lag; Nesline & Zarchan). `tau=0` bypasses exactly.
- Lag state on entity (`_lag_state`); **clamp after lag**. Achieved history
  still from `last_achieved_lateral_accel` (post-clamp).
- Demo PN miss: tau=0 → 2.993 m; tau=0.2 → 3.027 m (**+0.034 m**). Still hits.
- Miss vs tau monotonic on demo IC for {0, 0.1, 0.2, 0.35, 0.5}.

### 3b APN / 3c OGL
- `AugmentedProportionalNavigation`, `OptimalGuidance`; both take
  `a_target_est: () -> ndarray`. Reuse PN for APN’s PN term.
- OGL = ZEM / t_go² with t_go = R/Vc (floored); PN fallback if not closing.
- OGL(N=3) ≡ APN(N=3) on NoManeuver with shared a_T (bit-level).
- Weave (40 m/s², 0.25 Hz): APN/OGL beat PN on that single IC.
- **ConstantTurn(60) + instantaneous truth a_T: APN/OGL miss ~3.4 km while
  PN hits (~4.4 m).** Constant-accel APN assumption vs rotating turn vector —
  not patched; reported as limitation.

### Comparative sweep (`--compare`, 8×8, tau=0.2)
| Case | Hit rate |
|---|---|
| PN / NoManeuver | 43.8% |
| APN / NoManeuver | 43.8% |
| OGL / NoManeuver | 43.8% |
| PN / Weave | 59.4% |
| APN / Weave | 46.9% |
| OGL / Weave | 46.9% |

→ `outputs/validate_physics_compare.png`. On the coarse lag-on weave
envelope, PN hit rate > APN/OGL (truth a_T + lag can hurt at envelope edges).

## 2026-09-09 — Step 2: envelope sweep

- Axes: **lateral offset (target y) × initial range (target x)** on the
  NoManeuver demo IC family. Chose these over target_g/altitude because
  the prompt asked for a 2D NoManeuver sweep; g and altitude matter more
  once maneuvers + q-limits enter (AGENTS.md Step 2 3-factor note deferred).
- Hit threshold **5.0 m** (= demo `intercept_radius`; Step 1 miss ~3 m).
- Sweep dt=0.02 (vs demo 0.01) so 15×15 finishes ~20 s; demo point still
  classifies as hit. Grid widened to offset 0–8 km × range 2–13 km after
  the first 0–2.4 km×2.5–11 km pass was 100% hit (too small to show the
  miss edge — not a dynamics bug).
- Script: `scripts/validate_physics.py` → `outputs/validate_physics_heatmap.png`.
- Guardrail: mid-envelope miss holes (4-neighborhood) printed as WARNING;
  did not patch physics/guidance.

## 2026-09-09 — Step 1: visualization + accel history

- Deleted unused `PointMassEntity.trajectory` / `record()`; engine owns
  history. Added `last_achieved_lateral_accel` on the entity (updated
  inside `step`) so diagnostics get the post-clamp command without
  changing `step(...) -> None`.
- `SimulationResult` now includes `pursuer_accel_cmd` and
  `pursuer_accel_achieved` (T,3). Terminal intercept sample is zeroed
  (no command after hit).
- `visualization/plotter.py`: 3D trajectory, 2×2 diagnostics (range /
  speed-from-gradient / altitude / cmd vs achieved), GIF via Pillow.
- Demo uses `NoManeuver` so PN lead course is clear; writes under
  `outputs/`.
- Gotcha: speed panel uses `np.gradient` on positions (no velocity
  history in `SimulationResult` — kept API to the two accel fields
  Step 1 asked for).

## 2026-09-09 — Orient + verify + ground rules (no feature work)

- Read full package under `missile_guidance_sim/`; physics is 3-DOF
  point-mass with ISA atmosphere, q-limited lateral accel, RK4 ZOH
  commands, 3D PN. `api/`, `ml/`, `visualization/` are empty stubs.
- Baseline: created local `.venv`, installed `requirements.txt` +
  editable package, ran `pytest` from package root → **18 passed,
  0 failed** (atmosphere 4, aerodynamics 6, dynamics 4, guidance PN 4).
- No `.cursor/rules`; dual identical `AGENTS.md` (repo root + package).
  Prepended **Architecture & Session Ground Rules** to both; did not
  remove Steps 1–12 / API / invariants.
- README vs code: README architecture matches. `pyproject.toml`
  project description still says "2D" though the sim is 3D.
- Explicitly did **not** implement ML, FastAPI, visualization, or any
  new simulation features.

## 2026-09-09 — RL guidance Phase 1 environment (review gate)

- Added `guidance_sim.rl.InterceptionEnv` plus its tests and the required
  `gymnasium>=1.0,<2.0` dependency. Default ICs/vehicles exactly reuse the
  `scripts/run_demo.py` scenario; seeded IC/maneuver factories construct fresh
  states, entities, autopilot state, and maneuver instances each reset.
- Historical/superseded observation `(8,) float32`, exact order:
  `[r_hat_xyz, tanh(omega_los_xyz / 0.1 rad/s),
  range/(range + 10000 m), tanh(closing_velocity / 1000 m/s)]`.
  The 3D LOS unit vector avoids azimuth wrap/elevation-pole singularities.
- Action `(3,)` is a physical world-frame request in m/s². Box component
  bounds are ±25 g (±245.16625 m/s² for the default pursuer); `step` radially
  projects the vector norm to 25 g, then calls the unchanged entity
  lag → velocity-normal/aero/structural clamp → integrator pipeline. `info`
  reports requested, commanded, and achieved vectors.
- Reward:
  `Δrange/100m - 1.0*dt*(||a_commanded||/a_structural_max)^2 + terminal`,
  with terminal `+100` hit, `-100` ground-impact miss, `-100` timeout. Commanded
  (post-interface projection, pre-lag/clamp) effort prevents saturation/lag
  exploitation and `dt` makes the cost timestep-consistent.
- Outcome semantics: sampled range ≤5 m is `terminated=True` hit; pursuer or
  target ground impact is `terminated=True` physical miss; reaching
  `max_time` is `truncated=True` timeout. No closest-approach/non-closing
  heuristic was added, so valid intercept geometry is not ended prematurely.
- Verification: focused **6 passed**; full suite **42 passed**; Gymnasium
  environment checker passed (its expected warning notes that the deliberately
  physical action space is not normalized). Deterministic sanity rollout:
  PN-like direct control **+170.145706**, hit at 2.638 m; constant-25 g
  wandering control **−133.572646**, ground-impact miss at 5064.154 m.
- **Phase 2 was not started due to the review gate:** 0 training episodes,
  0 training timesteps, and no checkpoint.

## 2026-09-10 — Observation experiment: target turn-rate feature (no training)

- Inspected current RL obs: **already includes 3D LOS rate**
  `omega_los = cross(r_rel, v_rel) / |r|^2` as channels 3–5. Hypothesis that
  LOS rate was missing is incorrect. Missing quantity for ConstantTurn is
  **target body turn rate / a_T**, not omega_LOS.
- Added optional `use_target_turn_rate_obs: bool = False` on `InterceptionEnv`
  and `PPOTrainingConfig` (default off → CP1–CP4 contract unchanged).
- New feature (when flag on): append 3 channels
  `tanh(omega_T / 0.2 rad/s)` where
  `omega_T = cross(v_target, a_lat_achieved) / |v|^2`. Analytic from state —
  **no finite-difference filter**.
- **Fallback decision:** at `reset` before any `step`,
  `last_achieved_lateral_accel` is zero → turn-rate obs is `[0,0,0]`. Does
  **not** seed from maneuver command (would leak commanded vs achieved).
- Obs dim: **10** (flag off) / **13** (flag on). Policy input size comes from
  Gymnasium space; SB3 builds layers from env. Resume guard compares
  `config.observation_names` so a turn-rate branch cannot resume CP1–CP4.
- Tests: circular-turn hand check + env append/fallback; CP1–CP3 load under
  flag off. No training run started. Reward/hparams/frozen CP lineage
  untouched.

## 2026-09-10 — Start turn-rate obs experiment CP1 (separate lineage)

- Wired `--use-target-turn-rate-obs` into `scripts/train_rl.py`.
- Launched checkpoint 1 into `outputs/observation_target_turn_rate/`
  with flag on (13-D obs). Does **not** resume or overwrite frozen
  `outputs/checkpoints/` CP1–CP4.
- CP1 finished (20,480 steps, 16 episodes). Obs confirmed 13-D with
  `use_target_turn_rate_obs: true`. Fixed eval **0/9 hits**; Group B
  ConstantTurn mean miss **3296.9 m** (median 2683.1 m). Within-checkpoint
  reward quintile **-55.8 → -76.8**. Frozen CP1–CP4 under `outputs/` untouched.
  Stopped after CP1; CP2+ not started.

## 2026-09-10 — Turn-rate obs experiment CP2–CP4

- Ran CP2–CP4 in `outputs/observation_target_turn_rate/` (flag on).
  Frozen `outputs/checkpoints/` untouched.
- Hits: CP2 **1/9**, CP3 **4/9**, CP4 **3/9**. Group A stop warning at CP4.
- Group B (ConstantTurn) mean miss **improved** across checkpoints:
  CP1 3297 → CP2 2051 → CP3 1886 → CP4 1609 m (still 0/3 hits).
  Contrast with frozen lineage ConstantTurn regression. Control effort rose
  sharply on Group A (CP4 ~346k m²/s³). CP5 not started.

## 2026-09-10 — Turn-rate obs branch: diagnose GA regression + CP5 conclusion

### Step 1 — Group A CP3→CP4 hit regression
- Sole flip: `weave_7g_090hz` HIT→MISS (2.737 → 6.090 m; radius=5 m).
- Frozen 10-D lineage also 4/6→3/6 GA hits CP3→CP4 (`weave_3g_055hz`).
- **Classification (a) noise / intercept-boundary variance.** No code change.
  Detail: `outputs/observation_target_turn_rate/group_a_cp3_cp4_diagnostic.json`.

### Step 3 — CP5 (102,400 timesteps)
- Hits **5/9** (GA **5/6**, GB **0/3**). Mean/median miss **535.8 / 4.1 m**.
- Reward components: shaping **+25.27** / effort **−7.89** / terminal **+26.98**.
- Along-track fraction ~0 (lateral2 intact). cmd/ach RMS **68.5 / 52.6**.
- Group B mean miss **1599.7 m** (CP4 was 1609) — plateau vs prior steep drop.
  Per-case GB: 3g **832**, 5g **1453**, 7g **2515** m.
  Classical PN ceiling: 973 / 1194 / 2165 m (same cases).
- Tests: **66 passed** (`--ignore=tests/test_seeker_noise_miss.py`; seeker
  test is unrelated flake). Commit hash at conclusion time recorded in
  session report (working tree dirty with this branch + unrelated seeker WIP).

### Step 4 — Verdict (no promote / no discard)
- **Group B:** improved CP1→CP4 then **plateaued** at CP5 near (not under)
  the PN time-budget ceiling; 3g case now *beats* PN (832 vs 973), 5g/7g
  still worse. Not converging to hits under this budget.
- **Group A:** recovered to **5/6** at CP5 (above CP3 peak 4/6).
- **Recommendation:** do **not** promote over frozen lineage yet — GB still
  0 hits and ~PN-level misses on hard turns. Signal that turn-rate obs
  reversed frozen GB *regression* is real; further training or estimator-
  free privileged a_T ethics review needed before promotion. Frozen
  lineage left untouched.

## 2026-09-11 — Promote turn-rate obs CP5 as RL baseline

### Seeker-test skip resolution (Step 1)
- CP5 originally used `--ignore=tests/test_seeker_noise_miss.py` because that
  suite **failed** a near-monotonic miss-vs-noise gate
  (`medians [4.48, 3.08, 4.31, 56.18]` — scale 1.0 dipped below 0.0).
- **Unrelated to turn-rate obs:** the test drives classical PN through
  `Sensor` + `AlphaBetaFilter` in `simulation.engine` seeker hooks; it never
  constructs `InterceptionEnv` or reads `use_target_turn_rate_obs`.
- **Pre-existing / WIP relative to frozen lineage:** `tests/test_seeker_*.py`,
  `src/guidance_sim/sensors/`, and `src/guidance_sim/estimation/` were
  **untracked** at promotion time — they do not exist on committed
  `feature/rl-training` HEAD without local WIP. Re-run after stash of
  untracked files: no seeker tests present. Not introduced by this branch.
- At promotion re-check the WIP seeker suite passes (noise scales in the
  local file are now `(0, 2, 5, 12)`). Full suite with **nothing ignored**:
  **71 passed**. Seeker WIP left **uncommitted** (separate from this
  promotion).

### Promotion (Steps 2–3)
- Current baseline pointer: `outputs/CURRENT_RL_BASELINE.json` →
  `outputs/observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip`
  (13-D, `use_target_turn_rate_obs=True`).
- Prior 10-D lineage kept at `outputs/checkpoints/` with README noting
  superseded status — **not deleted**.
- README Status/Results updated to the new baseline.

### Group B ceiling — accepted limit (Step 4)
- ConstantTurn cases **plateau near classical-PN miss** under the current
  **25 s** fixed-eval budget. This is **not** treated as a training
  deficiency: PN itself also **misses all three** ConstantTurn cases at
  this budget (≈973 / 1194 / 2165 m). Turn-rate CP5 GB: ≈833 / 1453 /
  2515 m (3g beats PN; 5g/7g still worse; 0/3 hits).
- **Open item (deferred):** extend `max_time` so 3g/5g can convert to
  hits — requires its **own from-scratch retrain**; not pursued in this
  promotion pass.
