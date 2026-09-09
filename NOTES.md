# NOTES

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
