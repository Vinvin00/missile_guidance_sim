# Missile/Drone Guidance Simulation — Classical vs. Learned Approaches

A 3D pursuit-and-guidance simulation comparing the classical
**Proportional Navigation (PN)** guidance law against a PyTorch-based
learned approach, under realistic force-based flight dynamics
(gravity, aerodynamic drag, and a g-limited, dynamic-pressure-aware
airframe), benchmarked against each other over a range of target
maneuverability levels.

This is an applied control-theory + ML portfolio project: the physics
is standard point-mass flight dynamics (the same simplified model
used in introductory GNC coursework and drone/aircraft simulation),
the guidance law is the textbook one, and the ML component is layered
on top for comparison. No sensor/seeker hardware, propulsion, or
warhead engineering is modeled — everything here operates at the same
level of abstraction as a public GNC textbook problem or research
paper.

## Status

**Current RL baseline (promoted 2026-09-11):** recurrent PPO with a
**13-D** observation (`use_target_turn_rate_obs=True`) — base LOS
kinematics plus target turn-rate channels. Checkpoint:

`outputs/observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip`

Pointer file: [`outputs/CURRENT_RL_BASELINE.json`](outputs/CURRENT_RL_BASELINE.json).

Fixed-eval at promotion: **5/9 hits** (Group A NoManeuver+Weave **5/6**;
Group B ConstantTurn **0/3**, miss plateau near classical PN under the
25 s budget). Shadow comparison vs PN/APN/OGL:
[`outputs/shadow_comparison/shadow_comparison_report.md`](outputs/shadow_comparison/shadow_comparison_report.md).
The prior **10-D** reward-redesign lineage remains under
`outputs/checkpoints/` for comparison (see that directory's README).

**Phase 1: 3D physics core + PN baseline — done.**
Built directly in 3D with realistic dynamics from the start (gravity,
drag, an atmosphere model, and airframe-limited maneuverability),
rather than as a 2D kinematic scaffold to be retrofitted later.

**Interactive visualization — done.** A FastAPI WebSocket streams
captured RL baseline evaluation rollouts (`data_source=rollout`) into a
Vite + React Three Fiber viewer with orbit controls, scenario/guidance
selection, live parameter sliders, telemetry, and local playback.
Target B is fighter-class grounded at **240 m/s**. Trial-overlay and
training-dashboard surfaces still use isolated mock loaders.

## Architecture

```
src/guidance_sim/
├── physics/
│   ├── entities.py      # State (3D), VehicleParams, PointMassEntity
│   ├── atmosphere.py    # ISA standard atmosphere (density/temp/pressure vs altitude)
│   ├── aerodynamics.py  # Dynamic pressure, drag, available lateral accel (aero + structural limits)
│   ├── dynamics.py      # Combines gravity + drag + clamped guidance command into net acceleration
│   ├── integrator.py    # Generic RK4/Euler integrator over a real acceleration function
│   └── maneuvers.py     # NoManeuver, ConstantTurn, SinusoidalWeave (3D vector commands)
├── guidance/
│   ├── base.py                      # GuidanceLaw abstract interface (returns a 3D vector)
│   └── proportional_navigation.py   # Classical PN, full 3D vector form
├── rl/
│   └── environment.py  # Gymnasium wrapper (training remains on its own branch)
├── simulation/
│   └── engine.py       # Simulation, SimulationConfig, SimulationResult
├── api/              # FastAPI catalog + rollout WebSocket stream
└── visualization/    # Matplotlib trajectory plotting / GIF export

tests/                # Pytest suite: atmosphere, aerodynamics, dynamics/integration, PN baseline
scripts/run_demo.py   # Manual one-off simulation runner
frontend/             # Vite + React + R3F/Drei/Zustand interactive viewer
docs/                 # Scenario parameter source review
```

## Physics model

**Axis convention:** z is up (altitude); gravity acts along -z.

Each entity is a point mass integrated under the sum of three forces:

1. **Gravity** — constant `[0, 0, -g]`.
2. **Aerodynamic drag** — `F_drag = q · Cd · A`, opposing the velocity
   vector, where `q = 1/2 · ρ(altitude) · V²` is dynamic pressure and
   `ρ(altitude)` comes from a simplified ISA standard-atmosphere model
   (troposphere + lower stratosphere).
3. **Guidance/maneuver command** — projected onto the plane
   perpendicular to velocity (steering doesn't change speed directly)
   and clamped to `min(aerodynamic limit, structural g-limit)`, where
   the aerodynamic limit itself scales with dynamic pressure. This is
   why maneuverability realistically collapses at low speed/altitude
   even for an airframe rated for high g.

Integration is real RK4 over `[position, velocity]`, with the
guidance command held fixed for one step (zero-order hold, matching
how a real digital autopilot samples a command once per control-loop
tick) while gravity and drag are recomputed correctly at each RK4
stage since they depend on the evolving altitude and speed.

## The guidance law: Proportional Navigation (3D)

```
a_cmd = N · Vc · (ω_LOS × R̂)
```

- **N** — navigation constant (typically 3–5, dimensionless)
- **Vc** — closing velocity, the rate at which range is shrinking
- **ω_LOS** — line-of-sight angular rate *vector*, `(R × Vr) / |R|²`
- **R̂** — unit vector along the line of sight

This is the direct 3D generalization of the classical scalar PN
formula `a_cmd = N · Vc · λ̇`: the cross product supplies the correct
maneuver *direction* in 3D, where the 2D version could rely on there
being only one possible perpendicular direction.

Reference: Zarchan, *Tactical and Strategic Missile Guidance* (AIAA),
ch. 2, and Shneydor, *Missile Guidance and Pursuit*, for the vector
form — standard GNC coursework material.

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## Running

```bash
# Run the test suite (atmosphere, aerodynamics, integration, PN baseline)
pytest

# Run a one-off demo simulation
python scripts/run_demo.py

# Start the visualization API
uvicorn --app-dir src guidance_sim.api.main:app --reload

# In a second terminal, start the interactive viewer
cd frontend
npm install
npm run dev
```

## Roadmap

1. ~~3D physics core (gravity + drag + atmosphere + airframe limits) + PN baseline, tested~~ ✅
2. RL policy training and frozen checkpoint evaluation
3. ~~FastAPI trajectory WebSocket contract with synthetic preview~~ ✅
4. Evaluation harness comparing PN vs. ML across target maneuverability
   levels (intercept rate, average miss distance)
5. ~~Interactive R3F visualization with orbit/playback controls~~ ✅
6. Results and benchmarks written up in this README

## Visualization mock data

The live stream uses captured RL rollout sources:

- `/api/catalog` plus `/ws/trajectory` — live rollout preview, including
  catalog-bounded interceptor/target speed overrides
- `frontend/public/mock/last-session.json` — saved-session replay sample
- `frontend/public/mock/training-log.json` — `{episode, reward, success}`
  training dashboard sample
- `loadTrialSet()` — seeded mock overlay of 20–50 PN-like trials

Swap `loadTrajectoryLog()`, `loadTrialSet()`, or `loadTrainingLog()` when a
real RL episode log exists. Do not treat overlay colors or dashboard
curves as trained-policy results.

### Cobra evasion: 3-DOF + attitude (target only)

`CobraManeuver` (post-stall pitch-up → hang → spiral → recovery) runs on
a **3-DOF + attitude** model. It is **not 6-DOF**: pitch θ and bank φ
are extra integrated states driven by an idealized rate autopilot
(clamped pitch/roll rates). There are no moments, no inertia tensor, no
control surfaces, and no quaternions. Thrust acts along the body axis,
and lift/drag come from a sigmoid-blended linear → flat-plate CL/CD(α)
curve with α = θ − γ. The hang and the fall come from the force balance
(q → 0 kills aero, gravity stays). Nothing about them is scripted.
Near-zero airspeed needs a climbing entry. From level flight, drag
alone only bleeds the vehicle to roughly 50–80 m/s.

In the viewer, the **Cobra** scenario is a tail chase over 3 km. The
target cruises level at 240 m/s on a trim autopilot
(`hold_level_until_trigger`), then triggers late, at 1.5 s time-to-go. The
pitch-up zooms it about 200 m while the slowed interceptor overshoots.
PN, APN, and OGL all miss (20–34 m), but the frozen RL policy still hits.
At 150 m/s entry, or with a trigger earlier than about 2 s, every law
hits. The jet model is oriented by the streamed `body_axis` / `body_up`,
so the nose-up and the spiral bank are both visible.

Touches: `physics/aerodynamics.py` (`post_stall_coefficients`),
`physics/dynamics.py` (`attitude_net_acceleration`, rate clamps),
`physics/integrator.py` (`integrate_state`, generic flat-vector RK4),
`physics/entities.py` (`AttitudeAugmentedEntity`),
`physics/maneuvers.py` (`CobraManeuver`), `tests/test_cobra_maneuver.py`.

Isolation: the interceptor and all other maneuvers still use the
unchanged `PointMassEntity` path. An inactive `AttitudeAugmentedEntity`
matches it bit for bit (tested). The engine, guidance interface, RL
action/observation space, and the `feature/rl-training` branch are
untouched.

### Possible later extension (not started)

Right now vehicles are 3-DOF point masses with instantaneously-achieved
lateral acceleration (bounded by dynamic pressure and g-limit). A full
6-DOF rigid-body model — quaternion attitude, angular rates, moments of
inertia, an inner autopilot loop tracking commanded acceleration — is a
substantially larger scope increase (closer to a second project than an
extension) and isn't planned unless there's a specific reason to need it.

## Results (to be filled in as phases complete)

**RL baseline (turn-rate obs CP5, 2026-09-11):** see
`outputs/CURRENT_RL_BASELINE.json` and
`outputs/observation_target_turn_rate/training_progress.md`.
Group A **5/6** hits; Group B ConstantTurn remains a known
time-budget ceiling near classical PN (not a training bug — PN
also fails all three ConstantTurn cases at `max_time=25 s`).

**Shadow comparison (2026-09-11):** PN / APN / OGL / RL on the same
nine fixed-eval cases — report at
[`outputs/shadow_comparison/shadow_comparison_report.md`](outputs/shadow_comparison/shadow_comparison_report.md)
(raw: `.json` / `.csv`). Run:
`python scripts/run_shadow_comparison.py`. Headline: classical wins
most Group A weave/miss-distance cells; RL beats PN on ConstantTurn
3 g (832 vs 975 m) but all modes still miss Group B inside 25 s;
APN/OGL degrade on ConstantTurn vs PN (rotating `a_T`).
