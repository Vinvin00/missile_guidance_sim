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

**Phase 1: 3D physics core + PN baseline — done.**
Built directly in 3D with realistic dynamics from the start (gravity,
drag, an atmosphere model, and airframe-limited maneuverability),
rather than as a 2D kinematic scaffold to be retrofitted later. The
ML component and FastAPI service are scaffolded as empty packages;
see "Roadmap" below.

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
├── ml/               # LSTM trajectory predictor or RL policy (not yet implemented)
├── simulation/
│   └── engine.py       # Simulation, SimulationConfig, SimulationResult
├── api/              # FastAPI /simulate service (not yet implemented)
└── visualization/    # Trajectory plotting / GIF export (not yet implemented)

tests/                # Pytest suite: atmosphere, aerodynamics, dynamics/integration, PN baseline
scripts/run_demo.py   # Manual one-off simulation runner
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
```

## Roadmap

1. ~~3D physics core (gravity + drag + atmosphere + airframe limits) + PN baseline, tested~~ ✅
2. PyTorch component — LSTM trajectory predictor feeding PN (first
   milestone) or an RL policy (PPO via stable-baselines3) trained
   from scratch (stretch goal)
3. FastAPI `/simulate` endpoint returning full trajectories and
   intercept outcomes for both PN and the ML approach
4. Evaluation harness comparing PN vs. ML across target maneuverability
   levels (intercept rate, average miss distance)
5. Visualization: matplotlib 3D trajectory animation exported as GIF
6. Results and benchmarks written up in this README

### Possible later extension (not started)

Right now vehicles are 3-DOF point masses with instantaneously-achieved
lateral acceleration (bounded by dynamic pressure and g-limit). A full
6-DOF rigid-body model — quaternion attitude, angular rates, moments of
inertia, an inner autopilot loop tracking commanded acceleration — is a
substantially larger scope increase (closer to a second project than an
extension) and isn't planned unless there's a specific reason to need it.

## Results (to be filled in as phases complete)

_Baseline PN performance against maneuvering targets, and later the
PN-vs-ML comparison, will be documented here once the evaluation
harness (Roadmap step 4) is built._
