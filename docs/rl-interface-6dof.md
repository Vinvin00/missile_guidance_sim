# Frozen RL interface contract — 6-DOF core (`feature/6dof-rigid-body`)

Status: **FROZEN 2026-09-15**, written before any 6-DOF dynamics code.
Consumer: `feature/rl-training`. That branch was not modified. This doc is
the handoff.

## Decision: I/O contract unchanged → warm-start fine-tune, not a retrain

The 6-DOF work changes the *plant*, not the policy's inputs or outputs.

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

## Expected distribution shift (why fine-tune rather than drop-in)

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
2. Warm-start from `outputs/CURRENT_RL_BASELINE.json` with a reduced LR.
   Re-run the frozen eval set on the *unmodified* checkpoint first. That
   gives the zero-shot transfer gap, which is the number that justifies
   (or refutes) the fine-tune.
3. If zero-shot hit rate collapses (< 50% of the point-mass baseline),
   check the obvious first. `autopilot_tau` is ignored by the rigid body,
   so no code should re-add a lag on top. And `dt = 0.02 s` is covered:
   the PN regression in `tests/test_rigid_body.py` runs at 0.02 s and
   still hits within 10 m of the point-mass trajectory.
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
