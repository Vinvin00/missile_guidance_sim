# Frozen RL interface contract — 6-DOF core (`feature/6dof-rigid-body`)

Status: **FROZEN 2026-09-15**, written before any 6-DOF dynamics code.
Consumer: `feature/rl-training`. That branch was not modified. This doc is
the handoff.

## Decision: I/O contract unchanged, but the policy does NOT transfer

The 6-DOF work changes the *plant*, not the policy's inputs or outputs. The
checkpoint loads and runs unchanged. **Measured zero-shot transfer is 0/300**
(below). Treat the next step as a substantial retrain-from-warm-start with
reward changes, not a light fine-tune. The original prediction in this doc
was a light fine-tune, and that prediction was wrong.

### Zero-shot transfer, measured 2026-09-15

| Guidance | Plant | Hits (n=300) | Median miss | p90 miss | bounded_weave | break_turn | random_jink | vertical_jink |
|---|---|---|---|---|---|---|---|---|
| RL CP6 (frozen) | point mass | **242** (80.7%) | 4.2 m | 6.6 m | 59 | 51 | 62 | 70 |
| RL CP6 (frozen) | 6-DOF | **0** (0%) | 913 m | 2,350 m | 0 | 0 | 0 | 0 |
| PN N=4 (same estimator) | point mass | 218 (72.7%) | 4.0 m | 40 m | 69 | 41 | 41 | 67 |
| PN N=4 (same estimator) | 6-DOF | 227 (75.7%) | 3.9 m | 321 m | 74 | 20 | 64 | 69 |

Per-maneuver columns are hits out of 75. Point-mass rows reproduce the published
`outputs/evasive_largeeval_300/` numbers exactly (242 and 218), so the harness is
the same. Raw data: `outputs/6dof_transfer/`, `scripts/eval_6dof_transfer.py`.

**Why RL collapses when PN doesn't:**
- **Effort profile.** The policy commands ~140 m/s² RMS (~14 g) on the
  point mass, about 3× PN's ~45 m/s². Only ~62 m/s² was achieved: the
  0.2 s lag low-pass-filtered away its bang-bang jitter, and point-mass
  g was free. On the rigid body every g costs induced drag
  (CD_i = CN²/CNα). Speed bleeds from 350 to ~50 m/s within ~10 s, and
  the missile falls.
- **Ablation (20 cases).** Point mass 19/20; 6-DOF 0/20; 6-DOF with
  induced drag zeroed 13/20. Induced drag is the dominant cause. The
  rest is airframe/autopilot dynamics (α overshoots its 24.5° limit to
  28–35° on full-scale reversals).
- **Action-basis singularity.** `rl/actions.py::lateral_basis` uses
  up × v̂. Once the drained missile falls vertical, a constant action
  maps to a world command that whips 90–180° between steps. The point
  mass never flew there.
- **PN on 6-DOF.** Break turns get worse (41 → 20: late, hard reversals
  now cost energy and have real lag). Random jinks get better
  (41 → 64: the airframe filters the estimator noise PN chases).

**Recommendations for `feature/rl-training`:**
1. Train on the 6-DOF plant. The warm start is fine as initialisation,
   but expect the effort habit to have to be unlearned.
2. Put a price on energy. Either raise `effort_weight`, or penalise
   commanded-accel *rate* (jitter) rather than achieved accel, since
   achieved accel hides the jitter.
3. Fix the `lateral_basis` pole (e.g. a velocity-frame basis carried
   continuously from the previous step) before the policy can reach
   vertical flight.
4. Re-baseline PN on 6-DOF (227/300 above) as the bar to beat. The
   point-mass 218/300 is no longer the relevant comparison.

| Contract item | Before (point mass) | After (6-DOF) | Changed? |
|---|---|---|---|
| Action layout `lateral2` | 2 coefficients on the velocity-normal basis (`rl/actions.py::lateral_basis`), m/s², boxed at `max_load_factor * g0` | identical | no |
| Action layout `world3` | world-frame `(3,)` m/s² | identical | no |
| Action meaning | lateral **specific aero force** ⊥ velocity, gravity *not* included | identical. It is now the *outer-loop command* to the autopilot, not the applied accel | semantics same, realization new |
| Clamp | `clamp_lateral_command` (⊥v projection, `min(q·S·Cn_max/m, n_max·g0)`) | same function, applied to the command before the autopilot | no |
| Observation (10-D default, 13-D turn-rate, +2 tracking) | `rl/environment.py` docstring order and scalings | identical; computed from `entity.state` (world-frame `State`) exactly as today | no |
| `entity.state` | world `State(position, velocity)` | world `State` view kept in sync after every step (body-frame velocity is internal) | no |
| `entity.last_achieved_lateral_accel` | post-clamp command | **measured** aero+thrust specific force ⊥ velocity, world frame | value differs (now lags/saturates physically), type same |
| `entity.step(dt, lateral_accel_cmd, integrator, autopilot_tau)` | — | same signature | no |
| `SimulationConfig.autopilot_tau` | first-order lag stand-in | accepted and **ignored** by `RigidBodyEntity` (lag is emergent from inertia + actuators) | effect only |
| Control rate | env `dt` (0.02 s training) | same; the autopilot runs once per env step (ZOH), RK4 inside | no |

### What the policy must NOT be given (breaking change if added)

Attitude (quaternion / Euler), body rates `p, q, r`, α, β, surface
deflections. None of these reach the observation. If a later branch adds
any of them, the observation shape changes and the checkpoint cannot load.
**Treat that as a from-scratch retrain.** Do not assume a fine-tune will
converge.

## Expected distribution shift (written before measurement; #2 dominated)

1. **Emergent lag.** The fixed `tau = 0.2 s` first-order lag is replaced by
   airframe rotation, actuator rate/position limits and autopilot
   bandwidth. The interceptor's step response is second-order-ish, with
   overshoot.
2. **Induced drag.** Pulling g now costs speed (`CD = CD0 + K·CL²`). The
   point-mass model had no induced drag, so sustained high-g commands
   bleed more energy than the policy has seen.
3. **Achieved ≠ commanded at saturation.** The reward's effort term and the
   turn-rate observation read `last_achieved_lateral_accel`, which is now
   measured from forces. Near the α limit it undershoots the command.

## Handoff steps for `feature/rl-training`

1. Construct `RigidBodyEntity.from_state(state, INTERCEPTOR_6DOF)` where
   `InterceptionEnv.reset` builds `PointMassEntity` for the pursuer
   (and the target, if desired; `F16_6DOF` is the fighter-class target).
   Nothing else in the env changes.
2. The zero-shot gap is already measured (0/300, above). Do not re-add a
   lag on top: `autopilot_tau` is ignored by the rigid body. `dt = 0.02 s`
   is covered by the PN regression in `tests/test_rigid_body.py`.
3. Apply the reward/basis recommendations above before training.
4. Budget for throughput: a 6-DOF step costs ~0.6 ms, against ~0.03 ms
   for a point mass (numpy, single core). Env-steps/sec during fine-tuning
   will drop accordingly. The upgrade path, if it matters, is
   numba/hand-inlining `rigid_body_derivative`. It has not been done.

## Known, measured behaviour changes (not hypothetical)

- PN weave case (5 g, 0.5 Hz): peak achieved interceptor accel is
  ~155 m/s², against 245 m/s² for the point mass. That is the α-limit and
  induced-drag saturation showing up. It still hits.
- Live Cobra scenario at catalog defaults: PN still misses (≈22 m).
  APN and OGL now **hit** (≈4–5 m); on the 3-DOF+attitude model all
  three missed. The RL policy on the Cobra was not re-evaluated.
