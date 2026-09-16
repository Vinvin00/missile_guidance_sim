# Missile/Drone Guidance Simulation — Classical vs. Learned Approaches

A 3D pursuit-and-guidance simulation comparing the classical
**Proportional Navigation (PN)** guidance law against a PyTorch-based
learned approach, under realistic force-based flight dynamics
(gravity, aerodynamic drag, and a g-limited, dynamic-pressure-aware
airframe), benchmarked against each other over a range of target
maneuverability levels.

This is an applied control-theory + ML portfolio project: the physics
core is 6-DOF rigid-body flight dynamics (quaternion attitude, Euler's
equations, aero moments, rate-limited control surfaces and thrust
vectoring behind a cascaded autopilot), with the original point-mass
model kept as its regression reference,
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
│   ├── entities.py      # State, VehicleParams, RigidBodyEntity (6-DOF) + F16_6DOF / INTERCEPTOR_6DOF data, PointMassEntity (reference)
│   ├── rotational_dynamics.py  # Quaternions (Hamilton), Euler's equations, frame transforms
│   ├── aero_moments.py  # Roll/pitch/yaw moments: stability, rate damping, surfaces, thrust vectoring
│   ├── controls.py      # Deflection layout + actuator lag/rate/position limits
│   ├── atmosphere.py    # ISA standard atmosphere (density/temp/pressure vs altitude)
│   ├── aerodynamics.py  # q, drag, lateral limits, post-stall CL/CD, body-axis aero force
│   ├── dynamics.py      # Point-mass net accel; 13-state rigid-body derivative; cascaded autopilot
│   ├── integrator.py    # Generic RK4/Euler integrator
│   └── maneuvers.py     # NoManeuver, ConstantTurn, SinusoidalWeave, ..., CobraManeuver
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

The 6-DOF rigid body (next section) is the core. The point-mass model
below is what it is regression-tested against, and what the RL env on
`feature/rl-training` still builds. Each point mass is integrated
under the sum of three forces:

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

### Run everything with Docker Compose

The viewer's **ASK** screen ("Spec grounding") queries a separate
retrieval-grounded Q&A service, [aero-spec-rag](https://github.com/Vinvin00/aero-spec-rag),
that answers questions about guidance/aerospace parameters — drag
coefficients, ISA atmosphere values, PN gains — with a cited, bounds-checked
value pulled from a small document corpus, not a generated guess. It's a
standalone project and repo; `docker-compose.yml` here wires it in as a third
service alongside the sim backend and the viewer, so the whole demo starts
with one command and needs nothing installed but Docker.

Clone `aero-spec-rag` as a sibling of this repo:

```
Physics Sim Project/
  missile-sim-viz/      <- this repo
  aero-spec-rag/
```

Then, from this repo's root:

```bash
docker compose up --build
```

Open `http://localhost:5173`. The sim backend serves `:8000`, the
spec-grounding backend serves `:8001`; both are health-checked before the
frontend container starts. If `aero-spec-rag` lives somewhere else, point at
it with `AERO_SPEC_RAG_DIR`:

```bash
AERO_SPEC_RAG_DIR=/path/to/aero-spec-rag docker compose up --build
```

The containerized `aero-spec-rag` runs its default, fully offline
configuration (deterministic embeddings, no LLM, no API key, no Ollama) —
see [that repo's README](https://github.com/Vinvin00/aero-spec-rag) if you
want to point it at a local Ollama install instead.

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

### 6-DOF rigid-body core (supersedes the point-mass core and the old "6-DOF deferred" note)

`RigidBodyEntity` integrates 13 states with RK4:
`[position_W, velocity_B, quaternion_NB, body rates p q r]`.

- **Frames.** Position lives in the project's z-up world frame. Velocity
  is in body FRD axes. Attitude is a Hamilton, scalar-first quaternion,
  body → NED-style local frame (`N = (x_W, −y_W, −z_W)`). The quaternion
  is renormalised explicitly after every step, and a test holds `|q|`
  within 1e-12 over 10k tumbling steps. `euler_angles()` and
  `rotation_matrix_world()` are for telemetry and the viewer. See
  `physics/rotational_dynamics.py` for the one place conventions are
  defined.
- **Forces and moments.** Lift, drag and side force come from the
  post-stall CL/CD blend, now per-vehicle rather than Cobra-only. There
  are aero moments from static stability, rate damping (Clp, Cmq, Cnr)
  and surface deflections, plus thrust and thrust-vector moments. Euler's
  equations solve `I·ω̇ + ω×Iω = M`.
- **Controls.** Elevator, aileron, rudder, TVC pitch and TVC yaw each
  get a first-order lag, then a rate limit, then a position limit.
- **Autopilot.** Guidance (PN, APN, OGL or RL) still outputs a clamped
  lateral acceleration. An inner cascade turns it into body-rate
  commands (feedforward path rate plus α/β loops; skid-to-turn for the
  missile, bank-to-turn for the fighter). Inverse dynamics turns those
  into a required moment. A limit-weighted pseudo-inverse allocates
  deflections, so TVC takes over automatically as dynamic pressure
  vanishes.
- **Superset check.** With zero command, the 6-DOF interceptor matches
  the point-mass ballistic arc to under 3 m over 10 s. On the PN demo
  intercept it hits at the same time, within 0.1 s, with under 10 m of
  trajectory deviation over 7 km (`tests/test_rigid_body.py`).
- **Cost.** About 0.6 ms per step, against 0.03 ms for a point mass.

**Cobra, now genuinely 6-DOF.** `CobraManeuver` commands only throttle
and body rates. The pull-up saturates the elevator. In the hang
(~30 m/s, no q) pitch authority comes from thrust vectoring. The spiral
is flown on aileron and rudder. Climb → hang → spiral → recovery is
checked end to end (`tests/test_cobra_maneuver.py`).

Viewer scenario, re-tuned for the 6-DOF airframe: a 7 km tail chase with
the pull triggered 2.0 s after launch. Full thrust is held only through the
finite-rate pitch-up (`pitch_up_throttle=1.0`), then reduced to idle so the
target reaches an apex and falls into its spiral instead of climbing
vertically forever. At catalog defaults PN, APN, and OGL all miss while the
complete climb–apex–descent remains visible in the 25 s playback. The frozen RL
policy, still flying the same point-mass interceptor it was trained on,
misses all 12 locked seeds against this earlier complete maneuver. This is
not an instantaneous attitude shortcut: the 6-DOF target remains limited by
actuator rate, inertia, aerodynamics, and thrust-vector authority. Locked in
[`tests/test_api_stream.py`](tests/test_api_stream.py).

**Reference data and placeholders** (full citations inline in
`physics/entities.py`):

| Vehicle | Sourced | Derived / placeholder |
|---|---|---|
| Fighter target `F16_6DOF` | Mass, S, b, c̄, Ixx/Iyy/Izz/Ixz; CYβ, CYδr, CZδe; damping Clp/Cmq/Cnr at α=0; surface limits, rates and actuator lag. All from Stevens & Lewis, *Aircraft Control and Simulation*, and NASA TP-1538. F100-PW-229 max thrust. | Cmα (from an assumed CG shift), Cmδe (assumed tail arm), Clβ, Cnβ, Clδa, Clδr, Cnδr (order-of-magnitude), stall/CD0/Cn_max, all TVC figures (no stock F-16 TVC), engine gyro effects ignored. Aero digits were transcribed from memory of the textbook: verify before quoting. |
| Interceptor `INTERCEPTOR_6DOF` | None, by design (AGENTS.md §3: no real missile data). | Inertia from solid-cylinder formulas on the existing generic 50 kg airframe with an assumed 2.5 m length. CNα, static margin, fin effectiveness and Cmq from slender-body/fin estimates. Actuator figures placed in typical published ranges. |

**RL impact (measured):** the action/observation contract did not
change (frozen in [`docs/rl-interface-6dof.md`](docs/rl-interface-6dof.md)),
so the current checkpoint loads and runs. But it **does not transfer**.
Zero-shot on the 300-case held-out evasive set it scores **0/300** on the
6-DOF interceptor, against 242/300 on the point mass. Classical PN with
the same estimator scores 227/300 on 6-DOF (218 on the point mass).

| Guidance | Plant | Hits (n=300) | Median miss | p90 miss | bounded_weave | break_turn | random_jink | vertical_jink |
|---|---|---|---|---|---|---|---|---|
| RL CP6 (frozen) | point mass | **242** (80.7%) | 4.2 m | 6.6 m | 59 | 51 | 62 | 70 |
| RL CP6 (frozen) | 6-DOF | **0** (0%) | 913 m | 2,350 m | 0 | 0 | 0 | 0 |
| PN N=4 (same estimator) | point mass | 218 (72.7%) | 4.0 m | 40 m | 69 | 41 | 41 | 67 |
| PN N=4 (same estimator) | 6-DOF | 227 (75.7%) | 3.9 m | 321 m | 74 | 20 | 64 | 69 |

Per-maneuver columns are hits out of 75. Point-mass rows reproduce the published
`outputs/evasive_largeeval_300/` numbers exactly (242 and 218), so the harness is
the same. Raw data: `outputs/6dof_transfer/`, `scripts/eval_6dof_transfer.py`.

The cause is the policy's ~14 g RMS bang-bang command habit. It was free
on the point mass: lag-filtered, no induced drag. On the rigid body it
bleeds the missile from 350 to ~50 m/s. With induced drag ablated it
recovers to 13/20. Plan a warm-started retrain with an energy/jitter
cost, not a light fine-tune. Details and recommendations are in the
spec. Exposing attitude or body rates to the policy would additionally
break the observation shape. Env step cost rises ~20×.

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
