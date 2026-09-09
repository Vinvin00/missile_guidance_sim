# Evasive Maneuver Module — Implementation Spec

**Audience:** AI coding agent implementing this directly in the guidance sim codebase.
**Goal:** Add a target-maneuver module that generates realistic evasive trajectories, so the PN baseline and the PyTorch (LSTM/RL) component can be trained and benchmarked against non-trivial target behavior instead of straight-line/constant-turn targets.

---

## 1. Where this fits in the sim

Current target motion model (assumed): a target following a fixed or constant-turn trajectory that the interceptor tracks via Proportional Navigation, with the PyTorch component predicting target trajectory / correcting PN's line-of-sight-rate assumption.

**What to add:** a `TargetManeuverController` (or equivalent module) that:
1. Takes the target's current state (position, velocity, heading) each timestep.
2. Applies one of several parametrized acceleration profiles (maneuver classes below) on top of the target's baseline motion.
3. Exposes maneuver type + parameters as part of the episode/scenario config, so trajectories can be generated in bulk for training data and swept over for evaluation.

Suggested interface:

```python
class TargetManeuverController:
    def __init__(self, maneuver_type: str, params: dict, seed: int | None = None):
        ...

    def get_acceleration(self, t: float, state: TargetState) -> np.ndarray:
        """Returns the commanded acceleration vector (lateral/vertical) at time t,
        to be applied on top of/instead of baseline target motion."""
        ...
```

Each maneuver type below should be implemented as one strategy behind this interface (e.g. `JinkManeuver`, `BreakTurnManeuver`, `BarrelRollManeuver`, `SplitSManeuver`), selectable by name + params, so a scenario file can just say `maneuver_type: "jink", params: {...}`.

---

## 2. Maneuver classes to implement

For each: mechanism (why it defeats PN), the parameters to expose, and a rough formula to start from.

### 2.1 Jink
**Mechanism:** high-rate, quasi-random lateral acceleration that breaks PN's assumption of a smoothly varying line-of-sight rate. This is the single most important maneuver to implement first — it's the direct stress test for PN vs. ML.

**Parameters:**
- `period` (s) — time between direction reversals
- `amplitude` (m/s²) — lateral acceleration magnitude
- `axis` — `"horizontal"`, `"vertical"`, or `"combined"`
- `onset_delay` (s) — delay after missile detection before jink starts
- `randomize_period` (bool) — jitter the period each cycle instead of fixed-frequency (real jinking is deliberately non-periodic to defeat prediction — this flag matters for realism)

**Starting formula:**
```
a_lateral(t) = amplitude * sign(sin(2*pi*t / period))   # square-wave jink
# or, for randomized:
a_lateral(t) = amplitude * random_sign_flip_every(period ± jitter)
```

Implement two variants: sinusoidal (smooth, easier for PN to partially anticipate) and square-wave/randomized (harder — this is closer to real "why the jink" doctrine, which favors unpredictability over smoothness).

### 2.2 Vertical jink / altitude change
**Mechanism:** exploits missile energy/drag asymmetry — diving into denser air increases drag on a pursuer, climbing forces the missile to bleed energy pulling lead into thinner air.

**Parameters:**
- `dive_angle` / `climb_angle` (deg)
- `pullup_g` (g's)
- `altitude_delta` (m)
- `trigger_time` (s, relative to detection or intercept time-to-go)

**Starting formula:** a step change in flight-path angle at `trigger_time`, ramped over a realistic transition time (~0.5–1s) using pilot/airframe g-limit, then a pull-up defined by `pullup_g`.

### 2.3 Break turn
**Mechanism:** forces the missile into a turn rate beyond its max-g capability.

**Parameters:**
- `turn_g` (g's)
- `bank_angle` (deg)
- `trigger_time_to_go` (s) — timed relative to estimated missile time-to-go, since timing (not just magnitude) determines effectiveness

**Starting formula:** commanded turn rate `ω = g*9.81 / v_target`, applied as a coordinated turn once `time_to_go <= trigger_time_to_go`.

### 2.4 Barrel roll / displacement roll
**Mechanism:** helical path that continuously changes heading and angular offset while trying to keep the threat in sight — displaces the aircraft off the missile's predicted intercept point.

**Parameters:**
- `roll_rate` (deg/s)
- `helix_radius` (m)
- `forward_decel` (m/s², optional — real barrel rolls trade some forward speed)

**Starting formula:** parametrize as a helix: lateral position offset `= helix_radius * (1 - cos(roll_rate * t))`, vertical offset `= helix_radius * sin(roll_rate * t)`, superimposed on the baseline forward trajectory.

### 2.5 Split-S
**Mechanism:** half-roll + dive, rapid direction reversal + altitude loss.

**Parameters:**
- `roll_time` (s)
- `dive_g`
- `altitude_loss` (m)

**Starting formula:** a scripted two-phase maneuver — instantaneous 180° roll over `roll_time`, followed by a pull-through dive at `dive_g` until `altitude_loss` is reached.

---

## 3. Pre-launch vs. post-launch scenario flag

Add a `phase` field (`"pre_launch"` / `"post_launch"`) to scenario configs. Pre-launch maneuvers should be evaluated on whether they prevent the interceptor from ever reaching a valid launch condition (e.g. simulate an abort/no-fire threshold). Post-launch maneuvers should be evaluated purely on miss distance / intercept success given a missile already in flight. Keep these as separate evaluation modes — don't conflate the metrics.

---

## 4. Data generation for ML training

1. For each maneuver type, sweep parameter ranges (e.g. jink period × amplitude grid) to generate a labeled trajectory dataset.
2. Include a `"none"` / baseline (no maneuver) class for contrast.
3. Store per-trajectory: target state history, maneuver label + params, and (once integrated) PN miss distance and ML-corrected miss distance.
4. Use this dataset to train the LSTM/RL component to anticipate acceleration changes rather than just extrapolate straight-line closure — this is the mechanism by which the ML term should outperform pure PN specifically against jinking targets.

---

## 5. Evaluation harness

Add a benchmark script that runs PN-only vs. PN+ML across:
- all maneuver types
- a range of parameter values per type
- both `pre_launch` and `post_launch` phases

Report: miss distance distribution and intercept probability, broken out by maneuver type and phase. This becomes the headline result for the portfolio writeup (PN alone vs. PN+ML against realistic evasive targets).

---

## 6. Suggested implementation order

1. `JinkManeuver` (square-wave + randomized variants) — highest priority, most direct PN stress test.
2. `BreakTurnManeuver` — simple, high-value second maneuver.
3. Data generation pipeline + baseline ("none") class.
4. `BarrelRollManeuver`, `SplitSManeuver`, vertical jink — round out the maneuver library.
5. Evaluation harness + benchmark report.

*(Flares/chaff/sensor countermeasures are out of scope unless a seeker/sensor-fusion layer is added later — they're not trajectory maneuvers and don't affect a pure kinematic PN/LSTM model.)*
