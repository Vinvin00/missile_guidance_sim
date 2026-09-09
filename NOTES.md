# NOTES

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
- Observation `(8,) float32`, exact order:
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
