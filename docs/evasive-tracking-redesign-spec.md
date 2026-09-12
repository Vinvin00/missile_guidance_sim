# RL environment redesign: genuine evasion + delayed/estimated tracking

**Status: scoping only.** No code, environment, or training changes in this
document or alongside it. Every checkpoint below requires separate explicit
sign-off before it runs, identical to the gating used for the CP1–CP5
retrains in `NOTES.md`.

**Inputs:** `evasion-maneuvers-spec.md` (maneuver library),
`src/guidance_sim/physics/maneuvers.py` (current 3-class implementation),
`src/guidance_sim/sensors/measurement.py` + `src/guidance_sim/estimation/alpha_beta.py`
(existing, currently-optional sensor/estimator chain on `Simulation`),
`src/guidance_sim/rl/environment.py`, `src/guidance_sim/rl/training.py`,
`src/guidance_sim/guidance/{proportional_navigation,augmented_pn,optimal_guidance}.py`,
`outputs/shadow_comparison/shadow_comparison_report.md`, `docs/rl-justification.md`.

---

## 0. Correction to the framing this spec was requested under

The request describes the sensor/estimator layer as "optional hooks on
`Simulation`, currently unused by both RL and classical guidance." That's
half right and worth stating precisely, since it changes how much of this
is new infrastructure vs. rewiring:

- `Simulation` (`simulation/engine.py`) **already** wires `sensor` +
  `estimator` end to end: `_target_state_for_guidance(t)` calls
  `sensor.measure(...)` → `estimator.update(...)` → `estimator.estimate()`
  and falls back to ground truth only pre-cold-start. `scripts/run_seeker_noise_sweep.py`
  and `tests/test_seeker_noise_miss.py` exercise this path today, against
  **classical guidance (PN)** run through `Simulation`.
- What's actually true is narrower: **`InterceptionEnv` (RL) and
  `evaluation/shadow_compare.py` don't go through `Simulation` at all.**
  They step `PointMassEntity` directly and read `self.target.state`
  (ground truth) in `_kinematics()`/`_observation()`. So classical guidance
  *can* already run against delayed/estimated state (goal 2's fairness
  requirement is half-built), but RL and the shadow harness cannot, because
  they don't use the class that owns the hook.

Implication for scope: this redesign is not "add sensors to RL," it's
"route `InterceptionEnv` and `shadow_compare.py` through the same
sensor/estimator path `Simulation` already has, and flip the default from
off to on for both." That's a smaller, more contained change than net-new
estimation infrastructure, but it does mean `shadow_compare.py`'s current
architecture (raw entity stepping, no `Simulation`) needs to change or be
duplicated.

---

## 1. Target maneuvers: what actually displaces vs what just perturbs

### 1.1 Displacement analysis of the existing library

Current implementation is `NoManeuver`, `ConstantTurn`, `SinusoidalWeave`
(`physics/maneuvers.py`). Only `SinusoidalWeave` is in scope for
replacement — `NoManeuver` and `ConstantTurn` stay as they are useful
baseline/Group-B cases and aren't being sold as "evasion."

`SinusoidalWeave`'s failure mode as evasion: `lateral_accel` returns a
magnitude that swings through zero every half-period. Integrated twice,
a zero-mean sinusoidal acceleration produces a bounded, zero-mean
positional oscillation around the unperturbed straight-line path — the
target returns arbitrarily close to where it would have been with
`NoManeuver` every period. At 0.5–1.5 Hz (the training/randomized-factory
ranges) and 3–7g, that's a path corridor a few tens of meters wide, not a
divergence. It perturbs intercept geometry (adds LOS-rate noise for the
guidance law to reject) but never opens separation the way a real evader
does. This is consistent with the shadow-comparison finding that
`weave_3g_055hz` is the one case where RL (which apparently over-reacts to
the perturbation) loses to PN (which correctly treats it as a rejectable
disturbance around a still-basically-straight path) — see §5.

Evaluating `evasion-maneuvers-spec.md`'s library against "real displacement
over the engagement window" (order-of-magnitude, using representative
target speed ~240 m/s per `docs/scenario-parameter-sources.md`'s Target B
grounding, and the current pursuer-favorable engagement geometry):

| Maneuver | Mechanism | Net displacement over ~10–20 s | Verdict |
|---|---|---|---|
| Jink (square-wave/randomized period) | Reversing lateral accel, non-periodic | Same zero-mean-oscillation problem as `SinusoidalWeave` **unless** combined with forward translation — the spec's own §2.1 calls it "the single most important maneuver to implement first," but only the *unpredictability* (randomized period defeats prediction), not the displacement, is doing real work here | **Keep, but only as a component**, not a standalone displacement mechanism |
| Vertical jink / altitude change | Step change in flight-path angle + pull-up | Real, sustained displacement in the vertical axis (climb/dive is not mean-reverting like a sinusoid) — meaningfully changes intercept-plane geometry | **In v1** |
| Break turn | Turn at/near target's max-g, timed to missile time-to-go | Large sustained heading change → genuine lateral displacement that grows, not oscillates; explicitly designed to open angle and defeat PN's assumption of a roughly-fixed engagement geometry | **In v1** — highest-value single maneuver for goal 1 |
| Barrel roll / displacement roll | Helical offset superimposed on baseline path | Radius-bounded (`helix_radius` caps peak lateral offset) and the helix is itself periodic — visually the most dramatic of the six, but the spec's own formula shows the lateral offset saturates at `2*helix_radius` and doesn't grow; net displacement is *whatever the underlying baseline translation was*, roll adds little beyond a bounded corridor with some in-plane/out-of-plane coupling | **Defer** — geometrically closer to `SinusoidalWeave` (bounded oscillation) than to a break turn (open-ended separation), despite being visually the most dramatic |
| Split-S | Half-roll + dive, altitude loss | Real displacement (altitude loss + heading reversal), but it's a *terminating* maneuver in the source doctrine (used to disengage/reverse, typically loses significant energy) — over a 15–25 s intercept window with a target starting at ~3.3 km altitude (current scenario grounding), the dive has real room to run and this is a genuine geometry-breaker | **In v1**, gated on altitude budget (needs enough starting altitude that the dive doesn't hit `ground_altitude_m` mid-maneuver) |
| Herbst maneuver | *(Not present in `evasion-maneuvers-spec.md` — confirmed by full-text read of both copies; this is a supersonic/post-stall pointing maneuver from real air-combat literature, not sourced from the existing spec doc)* | Herbst (J-turn) is a rapid nose-pointing reversal at high AoA with large velocity-vector/heading decoupling — for a point-mass target model (no AoA state, no post-stall aerodynamics) it degenerates to "very fast heading reversal," which the break-turn model with tight `trigger_time_to_go` already covers at this level of fidelity | **Defer to v2+** — implementing it distinctly from break-turn requires modeling velocity-vector vs. body-axis decoupling that the current point-mass target entity doesn't carry, and would be cosmetic without that (see §7) |

### 1.2 v1 maneuver set (proposed)

1. **Break turn** (`evasion-maneuvers-spec.md` §2.3) — new primary
   evasion maneuver. Timing trigger (`trigger_time_to_go`, relative to the
   target's own estimate of missile time-to-go — for a v1 scripted target
   this can just use the true geometry, since the target is not the entity
   whose observability we're degrading) is exactly the mechanism that lets
   this "plausibly defeat a naive pursuit" per goal 1: a late break forces
   the guidance law to react to a heading change that invalidates its
   current LOS-rate-based prediction.
2. **Vertical jink** (`evasion-maneuvers-spec.md` §2.2) — second axis of
   genuine displacement, orthogonal to break turn; combining both
   (`axis="combined"` per the jink spec) is what stops the pursuer from
   fully compensating with a single-plane correction.
3. **Randomized/non-periodic jink** (`evasion-maneuvers-spec.md` §2.1,
   square-wave variant, `randomize_period=True`) — kept specifically as
   the *unpredictability* layer on top of (1)/(2), not as a standalone
   displacement source. Sinusoidal jink is dropped as its own maneuver
   class (it's what `SinusoidalWeave` already is).
4. **Split-S** — kept as a "hard" v1 case gated on sufficient starting
   altitude, explicitly to stress-test whether delayed tracking (§2)
   causes the interceptor to lose the target through a large, fast
   geometry change.
5. **Maneuver *sequences*** (goal 1's "maneuver sequences," not in the
   source spec doc as a distinct maneuver type but implied by its §3
   phase framing): a scripted composition — e.g. break turn at
   `t=trigger`, followed by vertical jink at `t=trigger+Δ` — built by
   chaining `ManeuverProfile` instances with time-windowed activation.
   This is new orchestration logic, not a new maneuver primitive.

**Deferred to v2+:** barrel roll (bounded-corridor problem above), Herbst
(needs target attitude/AoA state the point-mass entity doesn't have),
sinusoidal weave *as a standalone class* (superseded — see §5 on whether
this resolves the regression).

`SinusoidalWeave` itself is not deleted from the codebase (existing tests
and any archived checkpoints reference it), but it is demoted from "the
evasion maneuver" to a low-effort perturbation case retained mainly for
backward-compatible testing/regression coverage, sitting alongside the new
`ConstantTurn`-style Group-B-analog for the new maneuvers.

---

## 2. Delayed/imperfect target tracking

### 2.1 What exists vs. what needs to change

`sensors/measurement.py` (`Sensor`, `SensorConfig`, `SeekerNoiseConfig`)
and `estimation/alpha_beta.py` (`AlphaBetaFilter`) are complete and tested
for the `Simulation`-mediated path. Nothing here needs new estimation
math for v1. What changes:

- **Default, not optional.** `InterceptionEnv` gains a `sensor`/`estimator`
  pair constructed by default in `__init__`/`reset()` (mirroring how
  `Simulation` already does it), instead of reading `self.target.state`
  directly. A perfect-truth mode should remain available (for ablations
  and for reproducing old checkpoints' conditions), but it stops being the
  default for new training.
- **Classical baselines run the same path.** `evaluation/shadow_compare.py`
  currently steps raw entities to keep all four modes (PN/APN/OGL/RL) on
  identical target trajectories. The fairness requirement in goal 2 means
  PN/APN/OGL need the *same* delayed/estimated `target_state` input RL
  gets, at the *same* simulated timesteps. Two ways to get there:
  (a) route `shadow_compare.py` through `Simulation` for all four modes
  (reuses existing, tested wiring, but the harness currently doesn't use
  `Simulation` for a documented reason — worth confirming that reason
  still holds before switching); or (b) construct one shared
  `Sensor`+`AlphaBetaFilter` pair per episode and feed its output into
  both `InterceptionEnv`'s observation builder and the classical
  `compute_command(...)` calls, independent of `Simulation`. (b) is
  probably lower-risk since it doesn't touch the harness's existing entity
  timestep loop, only what state gets handed to each guidance law/policy.
  This is an implementation decision, not a scoping one — flagging both
  options here so the follow-up plan doesn't have to re-derive them.

### 2.2 Grounding the delay/noise parameters

The existing `SeekerNoiseConfig` defaults (`azimuth_std=1e-3 rad`,
`update_rate_hz=100.0` in `SensorConfig`) and `AlphaBetaFilter`'s default
`alpha=0.5` (with `beta = alpha**2/(2-alpha)`, the Benedict–Bordner
relation) are **not arbitrary** — they already match a standard textbook
reference point almost exactly: Zarchan's *Tactical and Strategic Missile
Guidance* uses a representative seeker/filter configuration of **100 Hz
sampling, α=0.5 with the same β relation, ~1 mrad RMS angle noise, and a
0.1 s gimbal time constant**, alongside a 0.2 s autopilot time constant
(which matches this codebase's `autopilot_tau=0.2` independently) [1].
That's a strong anchor for the *noise* side of this redesign — no change
needed there, just documenting that the existing defaults are already
literature-grounded, contrary to the framing that this needs to be sourced
from scratch.

**Delay is the new piece.** `SensorConfig.latency_s` exists but defaults
to `0.0` and is not currently exercised by any test or script at a
nonzero value. Grounding for a nonzero default:

- A general radar tracker-loop time constant of **~0.05 s** (≈20 Hz
  effective update, a stated compromise between response speed and noise
  rejection in tracking-loop design) is a commonly cited figure for
  fire-control-class tracking loops [2].
- Dedicated single-target military tracking radars run at **~10
  observations/second** for typical targets, with reported rates as low as
  **~1.4 Hz for non-maneuvering targets** up to **~8.4 Hz for a 9g target
  at short range** — i.e., track data rate is itself target-dynamics
  dependent, faster against a maneuvering target, slower against a benign
  one [3]. This is a useful secondary anchor precisely because it
  motivates *why* update rate/delay might reasonably be randomized rather
  than fixed (see below) — a real fire-control loop's effective rate isn't
  constant across the engagement.
- Track-while-scan (surveillance-radar, not dedicated-tracker) revisit
  times of **4–12 s** are also documented [3], but that regime (≤0.25 Hz)
  is a different sensor class than a missile seeker/dedicated tracker and
  is **not** the right anchor for this interceptor — noted here only to
  rule it out explicitly, since "radar update rate" without qualification
  is ambiguous in the literature.

Proposed v1 defaults, reusing the existing `Sensor`/`AlphaBetaFilter`
machinery:

- `update_rate_hz`: keep the existing **100 Hz** default (already
  literature-anchored per [1]) as the seeker-class figure — this
  represents the interceptor's own onboard tracker, not an off-board
  radar, so the faster figure is the right regime.
- `latency_s`: new nonzero default in the **20–50 ms** range, i.e. roughly
  the 1–3 sample periods at 100 Hz that a real processing/filter-settling
  chain would add on top of the raw update rate — grounded qualitatively
  by the ~0.05 s tracker-loop time-constant figure in [2] as "the same
  order of magnitude as the loop's own settling time," not read off it
  precisely (no source gives a clean, isolated latency number in ms; this
  is stated as an estimate, not a citation-backed constant, and should be
  labeled `I` (illustrative) in the same basis notation
  `docs/scenario-parameter-sources.md` uses for reduced-order scalars).
- `alpha`: keep **0.5** (directly matches [1]).
- `SeekerNoiseConfig`: keep existing defaults (directly matches [1]).

**Fixed vs. randomized per episode:** randomize the *effective* rate, not
the filter's `alpha`/noise-std constants. Concretely: sample
`latency_s ~ Uniform(0.02, 0.08)` and/or `update_rate_hz` from a small
discrete set (e.g. `{50, 100}` Hz) per episode, while keeping
`SeekerNoiseConfig` and `alpha` fixed. Rationale: [3]'s own finding is
that *real* tracker data rate already varies with target dynamics within
a single engagement, so randomizing rate/delay across episodes is closer
to the cited behavior than fixing it — and it directly serves goal 2's
"interceptor has to extrapolate, not just react to a fixed-lag ground
truth." Keeping noise-std and `alpha` fixed avoids conflating two
different kinds of imperfect information (measurement noise vs. staleness)
in one randomization, which would make failure-mode diagnosis (§6)
harder later.

### 2.3 Observation space: new features or just delayed values?

**Needs new features, not just substitution.** Feeding
`estimator.estimate()[0]` in place of `self.target.state` into the
existing observation pipeline (LOS unit, LOS rate, range, closing
velocity — see §2.4) silently changes what those features *mean* without
telling the policy anything about *how stale or uncertain* the estimate
is. A policy trained on delayed-but-unflagged state has no way to
distinguish "the target hasn't moved" from "my estimate hasn't updated
recently," which is exactly the ambiguity real missile guidance filters
are designed around (and exactly why `AlphaBetaFilter.covariance()`
exists as an interface point, even though it's currently a documented
proxy, not a real covariance).

Proposed additions to the observation vector:
- `time_since_last_update_scaled` — wall-clock (sim) time since the last
  accepted measurement, `tanh(dt_since/latency_reference)`. Cheap, directly
  available from `Sensor`'s internal state, and is the single most
  informative addition: it tells the policy when to trust vs. discount the
  position/LOS-rate features.
- A scalar estimate-quality proxy derived from `AlphaBetaFilter.covariance()`
  — even though that method is currently a residual-norm-based proxy
  rather than a true covariance, its trend (growing between updates,
  shrinking on a fresh update) is still informative and cheap to expose.
  This should be treated as a placeholder feature: if/when the estimator
  is upgraded to a true Kalman filter with a real covariance, this feature
  slot doesn't need to change shape, just its underlying computation.

Both are scalar additions (2 new obs channels), small relative to the
existing 10–13-D space, and both are computed from information the
sensor/estimator objects already expose — no new estimation math, just new
plumbing from existing state into the observation builder.

### 2.4 `use_target_turn_rate_obs` under delayed/estimated state

(Correcting the request's naming: the codebase has no `use_los_rate_obs`
flag. Base LOS rate is *always* in the 10-D observation, unconditionally.
The actual optional flag is `use_target_turn_rate_obs`, which adds target
turn-rate channels computed from the target's **post-clamp achieved**
lateral acceleration — i.e., today it's computed from privileged
ground-truth target acceleration, not from anything a real seeker could
measure. This section answers the request's question against that real
flag.)

**This is the single riskiest existing-behavior interaction in the whole
redesign, and needs explicit attention, not a one-line answer:**

- LOS rate (`cross(rel_pos, rel_vel)/range**2`) computed from a **delayed**
  `target_state` is a delayed LOS rate — during a fast target maneuver
  (break turn, vertical jink), the true LOS rate can swing substantially
  within one estimator update interval. At the proposed 20–50 ms latency
  plus up to 20 ms inter-update gap (50–100 Hz), the interceptor's LOS-rate
  observation can lag true LOS rate by up to ~100 ms during the onset of a
  break turn — which is exactly the regime where PN-family laws are most
  sensitive to LOS-rate accuracy (this is precisely the "over-drove
  lateral command" failure mode already seen on `weave_3g_055hz`, see §5,
  and a stale LOS rate during a sharper maneuver risks making it worse,
  not better).
- `use_target_turn_rate_obs` is **more** exposed than base LOS rate, not
  less: it's currently computed from privileged ground-truth achieved
  acceleration. Under this redesign, that channel either (a) has to be
  removed/reworked, since a real seeker cannot observe target acceleration
  directly and keeping it as ground truth would make the "delayed/imperfect
  tracking is the default" claim false for this one channel, or (b) has to
  be derived from finite-differencing the *estimated* velocity across
  updates, which will be noisy and further delayed (a derivative of a
  delayed, noisy signal). (a)'s honest version is: drop the ground-truth
  turn-rate observation entirely in the new default, and let the two new
  staleness/quality features from §2.3 carry the "the target might be
  turning and I don't fully know it" information instead. This is a
  meaningful behavior change for the currently-promoted baseline
  (`outputs/observation_target_turn_rate/`), which was specifically
  promoted *because* that channel helped — flagging this now since it's a
  direct contradiction goal 2 forces: the currently-best checkpoint's key
  feature is privileged information under the new default.
- **What breaks concretely:** any guidance law or policy that
  differentiates a stale, piecewise-constant estimate (the α-β filter
  free-runs on constant-velocity prediction between updates — see
  `AlphaBetaFilter.update`) will see LOS-rate/turn-rate features that are
  artificially smooth between updates and then jump at each update,
  rather than the true continuously-varying signal. That jump pattern is
  itself a learnable feature (which is arguably fine — it's honest
  information), but it means naive numerical differentiation for any new
  derived feature must operate on estimator update boundaries, not
  simulation timesteps, or it will manufacture spurious high-frequency
  content out of the stale-value plateaus.

---

## 3. Reward shaping and action space under delayed observation

- **ZEM/`t_go`-based shaping (`rl/zem.py`, `compute_reward`)**: the
  potential function `Φ(s)` is computed from `predicted_miss_m`, itself a
  function of the *observed* (now delayed/estimated) relative
  position/velocity. This is actually fine in principle — reward shaping
  is allowed to use the same imperfect information the policy acts on, and
  potential-based shaping's theoretical guarantee (policy invariance) does
  not require the potential to be computed from ground truth. **But** the
  terminal reward and the episode-minimum-range miss penalty should
  continue to use **ground truth** relative position, not the estimate —
  otherwise a policy could be rewarded for converging its *estimate* of
  miss distance to zero while the true miss distance is large (a filter
  that's lagging during a break turn could show a deceptively small
  estimated miss right as the true target has displaced). This needs to be
  an explicit, stated design choice in the reward config (shaping uses
  estimate, terminal/hit-detection uses truth+physical intercept radius,
  which is already how hit detection works today via true entity
  positions) rather than something that falls out implicitly.
- **Effort penalty**: unaffected — it's computed from the pursuer's own
  achieved acceleration, not target state.
- **Action space (`lateral2`)**: no structural change needed. `lateral2`'s
  basis (`e1, e2` perpendicular to pursuer velocity) depends only on the
  pursuer's own velocity, which remains perfectly known (self-state is not
  the thing being degraded). The concern under delayed observation isn't
  the action parametrization, it's that the *policy's ability to pick a
  good action* now depends on extrapolating stale state — that's an
  observation-space and training-difficulty question (§2, §4), not an
  action-space one. No change proposed here.

---

## 4. Time budget

The current `max_time=25.0` (`PPOTrainingConfig`) is described in
`docs/rl-justification.md` as a shared ceiling that specifically prevents
`ConstantTurn` (Group B) cases from ever converting — an estimated
**~35–40 s** of phase catch-up is needed, a number already on record, not
newly derived here. The new evasion maneuvers in §1.2 (break turn,
vertical jink, Split-S) are, if anything, harder geometry problems than a
sustained constant turn, since they combine a heading change with either
altitude change or deliberately mistimed onset. Extending the budget is
necessary for goal 1 to mean anything (an evasion maneuver the interceptor
structurally cannot ever catch up from, regardless of policy quality, is
not testing evasion-handling, it's testing budget).

Proposed: raise `max_time` to **45 s**, matching the closest existing
grounded figure in the codebase — `scripts/run_seeker_noise_sweep.py`'s
own `SimulationConfig(max_time=45.0, ...)` — rather than inventing a new
number. `RewardConfig.t_go_max_s` must be updated together with
`max_time` (currently both independently set to 25.0 — this coupling is
already a documented footgun per §4 of the research pass and should be
fixed as part of this change, e.g. by having one config derive the other,
though that's an implementation detail for the follow-up plan, not this
spec).

Extending the budget changes the meaning of every existing timeout-based
outcome in the fixed eval set (§6) and is one of the concrete reasons the
old 9-case results don't carry over unchanged.

---

## 5. Does this resolve `weave_3g_055hz`?

**Likely yes, as a side effect, but stated carefully:** `weave_3g_055hz`
is one of the frozen `FIXED_EVALUATION_CASES`, built from `SinusoidalWeave`
via `_case_maneuver`. If v1's maneuver library demotes standalone
`SinusoidalWeave` (§1.2) and the fixed eval set is rebuilt around the new
maneuver taxonomy (§6), then `weave_3g_055hz` **as a named scenario**
ceases to exist in the new eval set — the regression can't be "fixed" in
the sense of the same scenario now passing, because the scenario itself is
retired.

That's not evasion — it's worth being explicit that this is a
side-effect resolution, not a targeted fix, and it could look like
avoidance if not stated plainly. Two things support treating it as a
legitimate resolution rather than dodging the finding:
1. The root-cause diagnosis already on record (`docs/rl-justification.md`
   §3: RL "over-drove lateral command... and never closed inside 5 m")
   is a policy behavior specific to a bounded, mean-reverting oscillation
   that a well-tuned PN gain rejects and an undertrained/overreacting RL
   policy chases. That failure mode is a property of `SinusoidalWeave`
   specifically (§1.1's displacement analysis), not of "evasion" in
   general — so retiring the maneuver that caused it is consistent with
   §1's broader finding that this maneuver class doesn't represent real
   evasion, not a post-hoc excuse invented to explain away one bad number.
2. It should **not** be allowed to just quietly vanish. The v1 fixed/
   randomized eval set (§6) must include at least one bounded, mean-
   reverting perturbation case in the same spirit as `SinusoidalWeave`
   (kept as the "low-effort" retained case per §1.2) specifically so that
   "does the new policy still overreact to small bounded perturbations"
   remains a directly checkable question under the new baseline, even
   though the exact named case is gone.

---

## 6. Evaluation methodology

### 6.1 Randomized target-maneuver test set

A held-out, seeded distribution over the v1 maneuver space (§1.2):
maneuver type (break turn / vertical jink / randomized jink / Split-S /
composed sequence / retained bounded-weave), onset timing
(`trigger_time_to_go` or `trigger_time`), magnitude (turn-g, dive angle,
etc.), and axis, each drawn from a documented range analogous to how
`randomized_maneuver_factory` already works — but held out from the
training distribution's own RNG stream (distinct seed range) so it's a
genuine generalization test, not a resample of training conditions. This
should be large enough (suggest **≥50 seeded cases**, up from 9) to report
a hit-rate distribution with a meaningful confidence interval per
maneuver type, not just per-case pass/fail.

### 6.2 Do the old 9 fixed cases remain meaningful?

**Partially, and only with caveats stated up front, not silently:**
- `no_maneuver_*` (3 cases) and `constant_turn_*` (3 cases) are
  unaffected by the maneuver-library change (§1 only touches
  `SinusoidalWeave`/evasion) and remain directly comparable **except**
  that extending `max_time` to 45 s (§4) changes whether `constant_turn_*`
  (Group B) converts to hits at all — so even these 6 cases need
  re-running under the new budget before any "still meaningful" claim, and
  their historical numbers under the 25 s budget should be kept as a
  labeled "old budget" reference rather than deleted.
- `weave_*` (3 cases) stay runnable (the maneuver class isn't deleted,
  just demoted, per §1.2) but should be **re-labeled**, not silently
  reused as if unchanged — e.g. "retained bounded-perturbation case,"
  making explicit that they're no longer standing in for "the evasion
  test," per §5.
- Net: the 9 fixed cases become a **regression/continuity subset**
  (did we break something the old baseline could already do), not the
  primary evaluation surface. The randomized set in §6.1 becomes primary
  for the new goal (evasion + delayed tracking).

### 6.3 Re-evaluating PN/APN/OGL fairly under delayed tracking

Per §2.1, this requires PN/APN/OGL to consume the same
sensor/estimator-mediated `target_state` RL gets, at matching episode
seeds/timesteps, so the shadow comparison stays apples-to-apples. Concrete
requirement for the follow-up plan: whichever of the two options in §2.1
is chosen, the same estimator instance (same `alpha`, same per-episode
sampled `latency_s`/`update_rate_hz`) must be shared across all four
guidance modes within one episode — not four independently-seeded
estimators — so that a bad estimate in one mode isn't an artifact of RNG
draw rather than of the guidance law's sensitivity to staleness.

### 6.4 An honest disruption estimate

Stated explicitly, as requested, rather than assumed away:

- **Old checkpoints** (`outputs/checkpoints/`, `outputs/observation_target_turn_rate/`,
  and whatever `outputs/CURRENT_RL_BASELINE.json` currently points to) were
  trained against perfect-truth, `SinusoidalWeave`-based, 25 s-budget
  episodes with (for the current baseline) a privileged ground-truth
  turn-rate observation channel. None of those four conditions hold under
  this redesign. These checkpoints are **not** valid initializations to
  resume training from (the existing `_validate_previous_observation_contract`
  check in `training.py` would and should reject resuming across this
  change — the observation contract is genuinely different) and are not
  meaningfully comparable in a shadow-mode sense either, since the
  scenario distribution they were evaluated against no longer represents
  what's being asked of the new policy. They should be kept archived
  (already the existing pattern for superseded lineages) with a note that
  they predate this redesign, not deleted.
- **`outputs/shadow_comparison/shadow_comparison_report.md`** is built
  from `FIXED_EVALUATION_CASES` under perfect truth and the old budget —
  needs a full re-run under the new eval methodology (§6.1–6.3) once a new
  baseline exists. The old report should be kept as a historical artifact,
  labeled as pre-redesign.
- **`docs/rl-justification.md`** is derived entirely from that shadow
  report (per its own header) and will need a new version once the new
  shadow comparison exists. Its core finding (RL is a narrow, comparable
  arm, not a uniform win) may or may not still hold under harder evasion +
  delayed tracking — that's an open empirical question this redesign
  exists to test, not something to assume either way.
- Net: this is a **from-scratch retrain**, not a fine-tune, and every
  downstream artifact that cites the old baseline's numbers needs an
  explicit "superseded by [new doc], as of [new redesign]" note rather
  than being updated in place, consistent with how the turn-rate-obs
  lineage was kept alongside the frozen CP1–CP4 lineage rather than
  overwriting it.

---

## 7. Checkpoint plan for the retrain

Same CP1–CPn gated structure as the existing lineages in `NOTES.md`
(one dated entry per checkpoint, explicit stop-condition evaluation,
explicit "CPn+1 not started" statement, review gate before continuing).
Proposed as a **new, isolated output directory**
(`outputs/evasive_delayed_tracking/checkpoints/`), leaving all existing
lineages untouched, promotion to `CURRENT_RL_BASELINE.json` deferred to a
separate, later, explicitly-logged step — matching the turn-rate-obs
precedent.

Because this redesign changes more axes at once than any previous
retrain (maneuver library, observation contract, time budget, reward's
information source), the checkpoint plan front-loads validation
checkpoints before any real training budget is spent, rather than jumping
straight into the usual 5×20,480-timestep PPO cadence:

- **CP0 — infrastructure validation (no training).** Confirm: new
  maneuver classes produce the expected displacement (numerically check
  break-turn/vertical-jink/Split-S trajectories against the §1.1
  divergence claim, not just "it runs"); `InterceptionEnv` with
  default sensor/estimator produces a stable, non-NaN observation stream
  across a scripted rollout; the two new staleness/quality features (§2.3)
  vary sensibly across an episode; PN run through the shared
  estimator path (§2.1/§6.3) still intercepts on the retained
  no-maneuver/constant-turn cases (i.e., the estimator isn't so degraded
  it breaks a guidance law that worked fine under perfect truth). **Stop
  condition:** any of the above fails → fix and re-run CP0, do not
  proceed to CP1 under a known-broken environment.
- **CP1 — first training checkpoint**, new maneuver factory (break turn +
  vertical jink + randomized jink + retained bounded-weave, Split-S
  excluded initially to isolate its altitude-budget risk), new default
  sensor/estimator, 45 s budget, turn-rate-obs channel removed per §2.4.
  Report format identical to existing `training_progress.md` entries,
  plus the new randomized held-out set (§6.1) alongside the retained
  6 non-evasion fixed cases (§6.2). **Stop condition:** same Group-A-style
  rule as existing lineages (no joint improvement in held-out-set hit
  rate/mean-miss/reward across the checkpoint) triggers a review-gate
  pause, not an automatic CP2.
- **CP2–CP4 — continuation**, same cadence and stop rule as CP1, following
  the existing convention of running a targeted diagnostic (per the CP3
  precedent in the from-scratch `lateral2` lineage) rather than blind
  continuation whenever a stop-condition warning fires — e.g. if a
  non-improvement streak correlates with the estimator-staleness features
  specifically (§2.3/§2.4's stated risk), that's the first diagnostic to
  run before deciding whether to adjust reward shaping, extend budget
  further, or roll back the observation contract.
- **CP5 — Split-S introduced**, gated behind CP1–CP4 showing the policy
  handles break-turn/vertical-jink/randomized-jink reasonably (per §1.2's
  ordering, Split-S is the hardest/most altitude-constrained case and
  isn't worth spending budget on until the easier evasion axes are
  working). **Stop condition:** if Split-S cases show a qualitatively
  different failure mode (e.g. ground-impact terminations from the
  interceptor chasing a diving target too aggressively) rather than a
  simple hit-rate shortfall, that's a diagnostic trigger, not just a
  "needs more training" signal.
- **Promotion** is a distinct, later, separately-logged step (pointer
  flip in `CURRENT_RL_BASELINE.json`, old lineage kept with a superseded
  note), exactly as done for the turn-rate-obs baseline, and only after
  the new shadow comparison (§6.3) and `rl-justification.md` rewrite
  (§6.4) both exist.

Each checkpoint still requires separate explicit user sign-off before it
runs — this plan states the intended sequence and stop conditions, it does
not pre-authorize any of it.

---

## Public anchors

1. P. Zarchan, *Tactical and Strategic Missile Guidance* — representative
   seeker/tracker configuration: 100 Hz filter sampling, α=0.5 with
   β=α²/(2−α) (Benedict–Bordner relation), ~1 mrad RMS seeker angle noise,
   0.1 s gimbal time constant, 0.2 s autopilot time constant, 30 g
   structural limit. Referenced via course/secondary summaries of the
   text's standard worked example (ATI Courses summary;
   [aticourses.com/courses-2/342-tactical-and-strategic-missile-guidance-3-days](https://aticourses.com/courses-2/342-tactical-and-strategic-missile-guidance-3-days/)).
   **Basis: S** (standard textbook worked example, cited generally across
   the missile-guidance literature) — this is also, independently, almost
   exactly what `SeekerNoiseConfig`/`AlphaBetaFilter`'s existing defaults
   already encode, which is why §2.2 treats the noise side as already
   grounded rather than newly sourced.
2. General radar tracking-loop design discussion: tracker loop time
   constant of ~0.05 s as a stated compromise between response speed and
   noise rejection (secondary/survey source on gimbaled-radar tracking
   loops; [researchgate.net/publication/282306124](https://www.researchgate.net/publication/282306124_Air-to-Air_Tracking_of_a_Maneuvering_Target_with_Gimbaled_Radar)).
   **Basis: I** (order-of-magnitude anchor for the new `latency_s`
   default, not a precise sourced constant).
3. Track-data-rate figures for dedicated single-target military tracking
   radar (~10 Hz typical, ~1.4–8.4 Hz range depending on target dynamics)
   vs. track-while-scan revisit times (4–12 s) — general radar-tracking
   reference material ([sciencedirect.com/topics/engineering/track-while-scan](https://www.sciencedirect.com/topics/engineering/track-while-scan),
   [radartutorial.eu/02.basics/Fire-control%20radar.en.html](https://www.radartutorial.eu/02.basics/Fire-control%20radar.en.html)).
   **Basis: S/I** — used only to (a) rule out track-while-scan rates as
   the wrong regime for this interceptor and (b) motivate randomizing
   update rate/delay per episode, per §2.2.

## CP0 results (2026-09-12) — corrections this spec needs

CP0 ran as scoped: maneuver library implemented, tracking chain wired into
`InterceptionEnv`, no training budget spent. **Gate passed** — but four
claims above did not survive contact with integrated trajectories, and are
corrected here rather than left standing.

1. **§1.1 is wrong that `SinusoidalWeave` is bounded for every phase.**
   Integrating `a(t) = A·sin(ωt)` once gives `v(t) = (A/ω)(1 − cos ωt)` — a
   velocity with a **non-zero mean `A/ω`**. A weave starting at zero
   acceleration (phase 0) therefore *drifts cross-track indefinitely*, it is
   not mean-reverting. Measured over 20 s at 5 g: **188 m** at phase 0 vs
   **14 m** at phase π/2, and the drift scales as `A/ω` exactly as that
   algebra predicts (239 m at 0.55 Hz, 146 m at 0.9 Hz).
   **Consequence for §5:** `weave_3g_055hz` — the single Group A case where
   RL loses to PN — is the *phase-0, lowest-frequency* case, i.e. the
   maximum-drift member of the eval set (`phase_rad=0.0`, 0.55 Hz). The
   other two weave cases use phase π/3 and 2π/3. So RL's one Group A
   regression is against the weave case carrying the largest steady
   cross-track drift, not against a purely oscillatory perturbation. §5's
   "RL over-reacts to a bounded mean-reverting oscillation" diagnosis is
   built on a false premise for that specific case and should be re-derived
   before it is cited again.
2. **Not even the phase-π/2 weave is strictly mean-reverting.** Because the
   command direction is recomputed from the *current* velocity each step,
   the system is coupled rather than a clean double integral, leaving a slow
   residual drift (9 m → 14 m across a 20 s window). The decision-relevant
   comparison survives intact: a held break turn opens **>50×** the weave's
   corridor, which is what justifies the §1.2 demotion.
3. **§2.3's staleness feature must be age-of-information, not time since
   delivery.** Timing from the delivery instant makes the channel
   identically zero whenever the seeker runs at or above the control rate —
   it never reports the latency the policy actually has to cover. It is now
   stamped from the delivered measurement's own sample time, so it
   sawtooths between a latency floor and a latency + update-gap ceiling.
4. **§2.2's `{50, 100}` Hz update-rate set is wrong for this codebase.**
   Those figures assume a 100 Hz control loop; training runs `dt=0.02`
   (50 Hz), so both choices deliver a measurement every single step and the
   update-gap half of staleness carries no information. Now `{25, 50}` Hz,
   bracketing the control rate.

Two further implementation decisions that depart from the text above:

- **Tracking defaults to *off* at the `InterceptionEnv` level**, not on as
  §2.1 proposed. Defaulting it on changes the observation contract for every
  existing consumer of the frozen baseline (rollout capture, shadow compare,
  the live-inference endpoint, the 10-D CP1–CP5 checkpoints) and broke seven
  tests when tried. New training opts in explicitly via `PPOTrainingConfig`
  at CP1; the capability ships now, the regime change is gated.
- **§2.4 option (a) is implemented as a hard error:** combining
  `use_target_turn_rate_obs` with tracking raises, rather than silently
  serving one privileged ground-truth channel alongside a degraded estimate.

**CP0 stop-condition checks, all passing:** new maneuver classes displace as
claimed (break turn / vertical jink / Split-S all >1 km separation vs the
straight-line baseline, weave <50 m); the tracking observation stream is
finite and in-bounds across full episodes; staleness and uncertainty both
vary within [0, 1] across an episode; and PN still intercepts a
non-maneuvering target through the estimator, with ConstantTurn miss
distance staying within an order of magnitude of its perfect-truth value.
**CP1 is not started** and requires separate explicit sign-off.

## Review caveats

- The Zarchan-derived figures in [1] are from secondary/course-summary
  sources, not a direct page citation into the book itself (not available
  for direct excerpt here) — flagged so a reviewer with access to the
  primary text can verify the exact worked-example numbers before this
  is treated as final grounding, consistent with how
  `docs/scenario-parameter-sources.md` flags its own basis codes.
- The `latency_s` default (§2.2) is explicitly **not** a citation-backed
  number — it's an order-of-magnitude estimate justified by proximity to
  the cited tracker-loop time constant, labeled `I` accordingly. If a
  reviewer wants a tighter number, that likely requires a source that
  isolates processing/data-link latency separately from loop settling
  time, which the sources gathered here don't cleanly provide.
- §1's displacement analysis (SinusoidalWeave/jink/barrel-roll bounded vs.
  break-turn/vertical-jink/Split-S unbounded) is derived analytically from
  each maneuver's own kinematic formula, not from a numerical simulation
  run — CP0 (§7) is exactly where that analytical claim gets checked
  against actual trajectories before any training budget is spent on it.
