# AGENTS.md — Implementation Spec

Implementation contract for agents working on this 3D pursuer/target
interception simulation. Read **Architecture & Session Ground Rules**
plus §1–§3 always. Then implement your assigned step from §5.

**Task protocol**
1. `pytest` before you touch anything — confirm green baseline.
2. Implement only your assigned step. Do not refactor adjacent modules.
3. Write tests alongside code. `pytest` must pass in full at the end.
4. Append decisions + gotchas to `NOTES.md`.
5. Report: files changed, what you verified, what you did not verify.

---

## Architecture & Session Ground Rules

Keep this section accurate to the codebase. Do not invent APIs.

### Where the code lives

Canonical package root: `missile_guidance_sim/`.
Import package: `guidance_sim` under `src/guidance_sim/`.
Run `pytest` from `missile_guidance_sim/` (see `pyproject.toml`).

```
missile_guidance_sim/
├── src/guidance_sim/
│   ├── physics/       # atmosphere, aerodynamics, dynamics, entities,
│   │                  # integrator, maneuvers
│   ├── guidance/      # GuidanceLaw ABC + ProportionalNavigation
│   ├── simulation/    # Simulation, SimulationConfig, SimulationResult
│   ├── api/           # empty stub (__init__.py only) — not implemented
│   ├── ml/            # empty stub — not implemented
│   └── visualization/ # plotter (3D, diagnostics, GIF)
├── tests/             # atmosphere, aerodynamics, dynamics, PN, …
└── scripts/run_demo.py
```

### Architecture summary (Phase 1 — implemented)

- **3D from the ground up.** Axis: `z` up (altitude); gravity
  `[0, 0, -9.80665]` in `dynamics.GRAVITY_VECTOR`.
- **Point-mass entities** (`State`, `VehicleParams`, `PointMassEntity`).
  No attitude, quaternions, or angular rates — except
  `AttitudeAugmentedEntity` (target-only `CobraManeuver`: rate-commanded
  θ/φ, thrust along body, post-stall CL/CD; still not 6-DOF).
- **Forces:** gravity + aerodynamic drag (ISA density → `q = ½ρV²`) +
  lateral accel command. Integration is RK4 (Euler available) over
  `accel_fn(position, velocity)`; command is zero-order-held across
  RK4 stages; gravity/drag recomputed per stage.
- **Clamping:** `clamp_lateral_command` projects command ⊥ velocity,
  then caps magnitude to `min(aero limit, structural g-limit)` via
  `available_lateral_accel`.
- **Guidance:** `ProportionalNavigation` is full 3D vector PN:
  `a_cmd = N * Vc * (ω_LOS × R̂)`.
- **Maneuvers:** `NoManeuver`, `ConstantTurn`, `SinusoidalWeave` —
  each takes `(t, state)` and a reference axis to pick the turn plane.
- **Engine:** `Simulation.run()` steps target maneuver then pursuer
  guidance until intercept radius or timeout; records trajectories plus
  pursuer command/achieved lateral accel histories.
- **Visualization:** `plot_trajectory_3d`, `plot_diagnostics`,
  `animate_3d` under `visualization/plotter.py`.
- **Out of scope unless explicitly requested:** 6-DOF rigid-body
  dynamics (attitude, MoI, inner autopilot tracking). Autopilot lag
  (Step 3a) is the planned stand-in, not 6-DOF.

Module boundaries to preserve (do not collapse or invent new patterns):

| Module | Responsibility |
|---|---|
| `atmosphere` | ISA T/P/ρ (and speed of sound) vs altitude |
| `aerodynamics` | `q`, drag deceleration, available lateral accel |
| `dynamics` | clamp command; net accel = g + drag + frozen lateral |
| `integrator` | generic Euler/RK4 over `accel_fn` |
| `entities` | state/params; clamp once then integrate |
| `maneuvers` | target lateral profiles |
| `guidance` | pursuer command laws |
| `simulation` | time loop + result packaging |

### Session conventions (always)

1. **Physics changes require tests in the same change.** Any edit under
   `physics/` (or behavior that depends on it) must add or update
   tests under `tests/`. No exceptions.
2. **No large rewrites in one pass.** If a proposed change would touch
   more than ~2 modules, stop, flag the scope, and wait for
   confirmation before proceeding.
3. **6-DOF rigid-body is out of scope** unless the user explicitly
   requests it.
4. **Match existing style.** Keep the RK4 ZOH command pattern, the
   atmosphere → aerodynamics → dynamics → entities layering, and the
   `GuidanceLaw` / `ManeuverProfile` subclass extension points. Prefer
   small additive changes over new frameworks or pattern rewrites.
5. Keep root `AGENTS.md` and `missile_guidance_sim/AGENTS.md` in sync
   when editing this file.

---

## 1. Existing API (do not change these signatures)

```python
# physics/entities.py
@dataclass
class State:
    position: np.ndarray   # (3,) [x, y, z] metres, z = altitude
    velocity: np.ndarray   # (3,) [vx, vy, vz] m/s
    def speed(self) -> float
    def altitude(self) -> float        # == position[2]
    def copy(self) -> State

@dataclass
class VehicleParams:
    mass: float                          # kg
    reference_area: float                # m^2
    drag_coefficient: float              # Cd
    max_normal_force_coefficient: float  # Cn_max
    max_load_factor: float               # structural g-limit

@dataclass
class PointMassEntity:
    name: str
    state: State
    vehicle: VehicleParams
    last_achieved_lateral_accel: np.ndarray  # (3,) set in step()
    def step(self, dt: float, lateral_accel_cmd: np.ndarray,
             integrator: IntegratorType = RK4) -> None

# guidance/base.py
class GuidanceLaw(ABC):
    def compute_command(self, pursuer_state: State, target_state: State,
                        dt: float) -> np.ndarray   # (3,) world-frame m/s^2
    def reset(self) -> None

# physics/maneuvers.py
class ManeuverProfile(ABC):
    def lateral_accel(self, t: float, state: State) -> np.ndarray  # (3,)

# simulation/engine.py
@dataclass
class SimulationConfig:
    dt: float = 0.01
    max_time: float = 60.0
    intercept_radius: float = 5.0
    integrator: IntegratorType = IntegratorType.RK4
    autopilot_tau: float = 0.2  # s; 0.0 disables lag exactly

@dataclass
class SimulationResult:
    hit: bool
    miss_distance: float
    time_to_intercept: Optional[float]
    final_time: float
    pursuer_trajectory: np.ndarray   # (T, 3)
    target_trajectory: np.ndarray    # (T, 3)
    times: np.ndarray                # (T,)
    pursuer_accel_cmd: np.ndarray    # (T, 3)
    pursuer_accel_achieved: np.ndarray  # (T, 3)

class Simulation:
    def __init__(self, pursuer, target, guidance_law, target_maneuver,
                 config: Optional[SimulationConfig] = None)
    def run(self) -> SimulationResult
```

Helper functions available: `physics.atmosphere.isa_density(alt_m)`,
`physics.aerodynamics.available_lateral_accel(...)`,
`physics.aerodynamics.dynamic_pressure(rho, speed)`,
`physics.dynamics.clamp_lateral_command(...)`,
`physics.dynamics.net_acceleration(...)`.

**New guidance laws subclass `GuidanceLaw`. New maneuvers subclass
`ManeuverProfile`. Neither the engine nor entities should need edits to
accept them.**

---

## 2. Invariants (breaking these is a bug, not a design choice)

| Invariant | Enforced where | Failure symptom |
|---|---|---|
| z is up; gravity `[0,0,-9.80665]` | `dynamics.GRAVITY_VECTOR` | flat altitude trace |
| Guidance commands ⊥ velocity | `clamp_lateral_command` projects out along-track | speed changes from steering |
| Commands clamped to `min(aero limit, structural limit)` | `available_lateral_accel` | vehicle pulls impossible g |
| Aero limit scales with `q = ½ρV²` | `aerodynamics` | maneuverability constant with altitude |
| Command frozen across RK4 stages; gravity/drag recomputed per stage | `entities.step` | — |
| Entities are mutable and stateful | — | reuse across runs corrupts results |

Do not recompute guidance inside the integrator. Zero-order hold is
intentional (models a digital autopilot sampling once per control tick).

---

## 3. Scope boundary

Abstract point-mass simulation at the level of public GNC/estimation
coursework. All vehicle parameters are **generic illustrative values**.

Do not add: real sensor/seeker hardware specs, real vehicle performance
data, countermeasure engineering, warhead/lethality modeling. "Sensor
noise" means an abstract Gaussian error on an angle measurement — the same
model used for a robot camera. Keep it there.

---

## 4. Failure modes to check for

| Symptom | Cause |
|---|---|
| Pursuer curves in behind target (tail chase) | Pursuit, not PN. LOS-rate sign or `N` wrong. |
| Speed rises with no thrust | Drag sign error |
| Altitude flat | Gravity not reaching integrator |
| Sawtooth trajectory | `dt` too coarse / integration instability |
| Predictor output tracks *current* target position with lag | Degenerate "output ≈ input" solution. Loss looks fine. Useless. |
| Command chatters against clamp after adding predictor | Prediction noise amplified into loop. Smooth prediction or shorten horizon — not more training. |
| API: first request right, later ones garbage | Entities constructed at module scope |
| Bearings-only EKF diverges | Cartesian coords. Use modified-polar or UKF. |
| RMSE below CRLB | Bug. The bound is a floor. |
| NEES above chi-square bound | Overconfident filter, usually too little process noise |
| RL reward rises, trajectories look wrong | Reward hacking. Trust trajectories, not curves. |

---

## 5. Steps

Each step: one agent session, fresh context.

---

### Step 1 — `visualization/plotter.py`

```python
def plot_trajectory_3d(result: SimulationResult, out_path: str,
                       title: str = "") -> None
def plot_diagnostics(result: SimulationResult, out_path: str) -> None
def animate_3d(result: SimulationResult, out_path: str, fps: int = 30) -> None
```

`plot_diagnostics` = 2×2 panel: range vs t, speed vs t, altitude vs t,
commanded vs achieved lateral accel vs t.

`SimulationResult` currently lacks command history. **Add fields**
`pursuer_accel_cmd: np.ndarray (T,3)` and
`pursuer_accel_achieved: np.ndarray (T,3)`, populate them in
`Simulation.run()`, and update existing tests. Also resolve the unused
`PointMassEntity.trajectory` / `record()` — wire up or delete.

Accept when: `scripts/run_demo.py` scenario shows pursuer flying a
near-straight **lead** course, monotonic range decrease to intercept,
gradual speed bleed, altitude sag.

---

### Step 2 — `scripts/validate_physics.py`

Sweep `launch_offset × target_g × altitude`, output hit/miss heatmap.

Accept when: envelope boundary is smooth; higher target g shrinks it;
higher altitude shrinks it (lower `q` → lower aero limit). Holes mid-
envelope or altitude having no effect = bug.

---

### Step 3 — Autopilot lag + APN/OGL

**3a. Lag.** Achieved accel is a first-order lag of commanded:

```
da_achieved/dt = (a_cmd - a_achieved) / tau
```

Add `autopilot_tau: float = 0.2` to `SimulationConfig`. Hold lag state per
entity. `tau = 0.0` must bypass the filter exactly (existing tests depend
on this). Clamp *after* the lag, not before.

**3b. `guidance/augmented_pn.py`**

```
a_cmd = N * Vc * (omega_los × r_hat) + (N/2) * a_target_est
```

**3c. `guidance/optimal_guidance.py`**

```
ZEM   = r_rel + v_rel * t_go + 0.5 * a_target_est * t_go**2
a_cmd = N * ZEM / t_go**2
t_go  = range / closing_velocity
```

Both take `a_target_est` via constructor injection — a callable
`() -> np.ndarray` so Step 5 can swap truth for an estimate. Start with
truth (perfect-knowledge upper bound). Reuse `ProportionalNavigation` for
the PN term; do not reimplement.

Guard `t_go` against division by zero near intercept.

Accept when:
- `test_ogl_equals_apn_at_n3`: OGL(N=3) and APN(N=3) produce identical
  trajectories to within float tolerance.
- Miss distance increases monotonically over `tau ∈ {0.0, 0.1, 0.2, 0.35, 0.5}`.
- APN with perfect knowledge has lower peak-g near intercept than PN.

---

### Step 4 — `evaluation/harness.py`

```python
@dataclass
class Tier:
    name: str
    maneuver_factory: Callable[[np.random.Generator], ManeuverProfile]
    ic_sampler: Callable[[np.random.Generator], tuple[State, State]]

@dataclass
class CellResult:
    intercept_rate: float
    miss_median: float
    miss_p95: float
    cep: float                  # radius containing 50% of misses
    mean_time_to_intercept: float
    control_effort: float       # mean ∫|a|² dt
    n_runs: int

def run_cell(tier, guidance_factory, n_runs=500, seed=0) -> CellResult
def run_grid(tiers, guidance_factories, ...) -> dict
```

Randomize per run: initial heading error, target maneuver magnitude,
maneuver onset time, weave phase, noise seed. **Seeds must be explicit and
stored** — identical seeds across all compared guidance laws.

Maneuver tiers (implement missing profiles in `physics/maneuvers.py`,
subclassing `ManeuverProfile`):

| Tier | Profile | Params |
|---|---|---|
| A0 | `NoManeuver` | — |
| A1 | `ConstantTurn` | 3–10 g |
| A2 | `StepManeuver` *(new)* | 3–10 g, onset ~ U(0, t_flight) |
| A3 | `SinusoidalWeave` | **0.5–1.0 Hz**, 3–10 g |
| A4 | `BarrelRoll` *(new)* | high g, 3D roll |
| A5 | `BangBangEvasion` *(new)* | max g, switch at tuned t_go |

0.5–1.0 Hz is the documented resonant band for fast-response loops.
Expect a miss-distance peak there; its absence indicates a bug.

**Calibration gate — mandatory before proceeding.** If PN intercept rate
is ≈100% across all tiers, harden them (raise target g, push weave into
0.5–1 Hz, worsen launch geometry, lower pursuer `max_load_factor`, raise
`autopilot_tau`) until PN sits in **40–80%** on mid tiers. Then freeze tier
definitions and seeds. Every later comparison uses this frozen set.

---

### Step 5 — Observability

**5a. `sensors/measurement.py`**

```python
@dataclass
class SensorConfig:
    angle_noise_std: float = 1e-3     # rad (~1 mrad)
    range_available: bool = True
    update_rate_hz: float = 100.0
    detection_probability: float = 1.0
    latency_s: float = 0.0

@dataclass
class Measurement:
    t: float
    azimuth: float
    elevation: float
    range_: Optional[float]
    valid: bool

class Sensor:
    def measure(self, t, pursuer_state, target_state,
                rng: np.random.Generator) -> Optional[Measurement]
```

Returns `None` on missed detection or between updates. Latency = deliver
the measurement taken `latency_s` ago.

**5b. `estimation/`** — implement in this order, each with the interface:

```python
class Estimator(ABC):
    def update(self, measurement: Optional[Measurement],
               pursuer_state: State, dt: float) -> None
    def estimate(self) -> tuple[State, np.ndarray]  # (target state, accel est)
    def covariance(self) -> np.ndarray
```

1. `alpha_beta.py` — fixed gain, `beta = alpha**2 / (2 - alpha)`
2. `kalman.py` — linear KF, CV and CA models
3. `ekf_polar.py` — bearings-only EKF **in modified-polar coordinates**
   (Cartesian diverges structurally; this is not a tuning issue)
4. `imm.py` — IMM over CV + CA + coordinated-turn, Markov switching

Singer maneuver model for process noise: acceleration as first-order
Markov, `r(τ) = σ_m² · e^(−α|τ|)`, `α = 1/τ_maneuver`, `τ_maneuver` 5–20 s.

Wire estimator output into the `a_target_est` callable from Step 3. Keep a
perfect-information mode for upper-bound comparison.

Observability tiers: B0 perfect state · B1 +angle noise · B2 bearings-only
· B3 +dropouts (`detection_probability < 1`) · B4 +latency.

**5c. `evaluation/consistency.py`** — validation is mandatory:

```python
def nees(estimates, covariances, truth) -> np.ndarray
def nis(innovations, innovation_covariances) -> np.ndarray
def chi_square_bounds(dof, n_runs, alpha=0.05) -> tuple[float, float]
def posterior_crlb(...) -> np.ndarray
```

Accept when: average NEES ≈ state dimension and inside chi-square bounds;
NIS passes its own test (NIS consistency does **not** imply NEES
consistency — test both); RMSE approaches but never beats CRLB.

---

### Step 6 — `ml/` trajectory predictor

```python
# ml/dataset.py
def generate_dataset(tiers, sensor_config, n_trajectories, seed
                     ) -> tuple[np.ndarray, np.ndarray]  # (N, hist_len, F), (N, 3)
# ml/lstm.py
class TrajectoryPredictor(nn.Module):
    def forward(self, history: Tensor) -> Tensor   # (B, hist_len, F) -> (B, 3)
```

Train on **noisy/intermittent measurements from Step 5**, not clean truth.
Normalize inputs (raw metres/m/s trains badly). Input features: relative
position, relative velocity, measurement-valid flag. Predict target
position at `t + k·dt`.

**Mandatory baseline in every report:** constant-velocity extrapolation
`p + v·k·dt`. Print both RMSEs side by side. If the network doesn't
clearly beat it, it has learned nothing — do not proceed to Step 7.

---

### Step 7 — `guidance/lstm_guidance.py`

Subclass `GuidanceLaw`. Predict target state at `t + k·dt`, feed into the
APN/OGL math from Step 3. Reuse those classes.

Cold start: before `hist_len` samples exist, fall back to plain PN.

Accept when: same-seed side-by-side plots show cleaner path and lower
command oscillation than PN on a weaving target. Chatter against the clamp
= prediction noise; smooth or shorten horizon.

---

### Step 8 — Comparison run

Run the frozen Step 4 harness over the full `maneuver × observability`
grid for PN, APN, OGL, learned.

Fairness, enforced in code:
- Identical IC distributions and seeds for every method.
- **Information-matched**: if the learned method sees only noisy angles,
  the classical baselines see only noisy angles. A baseline given less
  information is the standard criticism of results in this area.
- ML evaluated on **held-out** maneuver profiles and parameter ranges.
- Report control effort alongside miss.

Expected shape: classical wins in B0–B1 × A0–A2; learned matches or wins
in B2–B4 × A3–A5 where the acceleration estimate degrades.

**The learned method may lose. Report it.** Classical APN/OGL with a good
estimate are near-optimal in well-observed conditions. A large unexplained
improvement is a cue to hunt for leakage. Include at least one cell where
ML loses.

---

### Step 9 — `api/main.py`

FastAPI. Pydantic request/response. `POST /simulate` takes initial
conditions, maneuver profile, guidance law list; returns trajectories +
outcomes per law.

**Construct entities per request inside the handler.** Module-scope
entities produce a correct first response and garbage after.

Accept when: a scenario run through `/docs` matches the same scenario run
directly in Python.

---

### Step 10 — Demo artifact

Animated 3D GIF (rotating view, trajectories drawing in) or a light front
end on `/simulate`, showing PN vs learned on one scenario. Label axes,
mark intercept, caption which is which.

---

### Step 11 — RL (optional, after 1–10)

Gymnasium env wrapping `Simulation`; PPO via stable-baselines3.
Observations = **estimated/noisy** state, matching what classical baselines
receive. Use a recurrent policy (GRU/LSTM) — under partial observability
this is formally a POMDP.

Reward must penalize control effort, or the policy oscillates. Accept only
on rising reward **and** sane trajectories **and** competitive frozen-
benchmark results.

---

### Step 12 — README results

Fill the benchmark grid, embed the GIF, write the where/why analysis.
State plainly: 3-DOF point-mass study; autopilot lag stands in for the
attitude dynamics a 6-DOF model would resolve; all vehicle parameters
generic.

---

## 6. Deferred

- **6-DOF rigid body** — only if attitude/autopilot design becomes the
  object of study. 3-DOF is correct for comparing guidance laws and
  estimators, and far cheaper for thousands of Monte Carlo runs.
- **Adjoint method** for linearized miss sensitivity vs. time-to-go.
  Consider after Step 8.
- Mach-dependent `C_D(M)` with drag divergence → induced drag
  `C_D = C_D0 + K·C_L²` → boost-coast with mass depletion →
  q-dependent AoA limit. Add in that order.

---

## 7. Reference formulas

```
q            = 0.5 * rho * V**2
omega_los    = cross(r_rel, v_rel) / |r_rel|**2
Vc           = -dot(r_rel, v_rel) / |r_rel|
t_go         = |r_rel| / Vc
PN           = N * Vc * cross(omega_los, r_hat)
APN          = PN + (N/2) * a_target_est
OGL          = N * ZEM / t_go**2,  ZEM = r_rel + v_rel*t_go + 0.5*a_T*t_go**2
accel ratio  = N / (N - 2)          # steady state; 3:1 at N=3, 2:1 at N=4
miss scaling = a_target * tau**2 * f(N, t_flight/tau)
alpha-beta   = beta = alpha**2 / (2 - alpha)
Singer       = r(τ) = sigma_m**2 * exp(-alpha * |τ|),  alpha = 1/tau_maneuver
```

`N` must exceed 2 to intercept a maneuvering target; practical 3–5. Larger
`N` lowers peak miss but demands more early acceleration and amplifies
measurement noise.

Sources: Zarchan *Tactical and Strategic Missile Guidance*; Shneydor
*Missile Guidance and Pursuit*; Bar-Shalom *Estimation with Applications to
Tracking and Navigation*; Nesline & Zarchan JGCD 4(1) 1981 (APN/OGL);
Gaudet/Furfaro/Linares arXiv:1906.02113 (partial-observability RL).
