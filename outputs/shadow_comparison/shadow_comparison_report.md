# Shadow-mode guidance comparison

Head-to-head on the frozen RL fixed-eval matrix (Group A = NoManeuver + SinusoidalWeave; Group B = ConstantTurn).

- Scenarios: **9**
- Modes: PN, APN, OGL, RL
- Time budget: **25 s** (dt = 0.02 s)
- Eval seed base: `91000` (case seed = base + index)
- RL baseline pointer: `outputs/CURRENT_RL_BASELINE.json`
- RL model: `outputs/observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip`

## Hit / miss + miss distance

| Scenario | Group | PN | APN | OGL | RL |
|---|---|---|---|---|---|
| `no_maneuver_center` | A | HIT / 3.4 m | HIT / 3.4 m | HIT / 0.6 m | HIT / 3.0 m |
| `no_maneuver_demo` | A | HIT / 2.6 m | HIT / 2.6 m | HIT / 3.0 m | HIT / 1.2 m |
| `no_maneuver_offset` | A | HIT / 4.6 m | HIT / 4.6 m | HIT / 1.7 m | HIT / 3.2 m |
| `constant_turn_left_3g` | B | MISS / 974.7 m | MISS / 2099.8 m | MISS / 1942.0 m | MISS / 831.8 m |
| `constant_turn_right_5g` | B | MISS / 1193.9 m | MISS / 3853.3 m | MISS / 3733.3 m | MISS / 1452.8 m |
| `constant_turn_left_7g` | B | MISS / 2164.4 m | MISS / 5296.5 m | MISS / 5198.1 m | MISS / 2514.6 m |
| `weave_3g_055hz` | A | HIT / 0.2 m | HIT / 4.5 m | HIT / 1.5 m | MISS / 7.4 m |
| `weave_5g_070hz` | A | HIT / 2.1 m | HIT / 3.2 m | HIT / 4.5 m | HIT / 4.1 m |
| `weave_7g_090hz` | A | HIT / 3.6 m | HIT / 1.9 m | HIT / 4.3 m | HIT / 4.1 m |

## Detailed metrics

| Scenario | Mode | Hit | Miss (m) | Time (s) | Peak |a_cmd| | Mean |a_cmd| | Peak |a_ach| |
|---|---|---|---|---|---|---|---|
| `no_maneuver_center` | PN | yes | 3.395 | 16.32 | 14.1 | 1.6 | 5.4 |
| `no_maneuver_center` | APN | yes | 3.395 | 16.32 | 14.1 | 1.6 | 5.4 |
| `no_maneuver_center` | OGL | yes | 0.613 | 16.32 | 161.9 | 2.1 | 27.7 |
| `no_maneuver_center` | RL | yes | 3.034 | 16.42 | 156.1 | 6.1 | 54.1 |
| `no_maneuver_demo` | PN | yes | 2.649 | 17.74 | 25.0 | 3.2 | 11.0 |
| `no_maneuver_demo` | APN | yes | 2.649 | 17.74 | 25.0 | 3.2 | 11.0 |
| `no_maneuver_demo` | OGL | yes | 2.982 | 17.72 | 108.7 | 3.7 | 25.9 |
| `no_maneuver_demo` | RL | yes | 1.229 | 17.90 | 119.8 | 8.2 | 98.9 |
| `no_maneuver_offset` | PN | yes | 4.556 | 20.36 | 44.1 | 4.7 | 17.1 |
| `no_maneuver_offset` | APN | yes | 4.556 | 20.36 | 44.1 | 4.7 | 17.1 |
| `no_maneuver_offset` | OGL | yes | 1.656 | 20.34 | 245.2 | 5.7 | 58.6 |
| `no_maneuver_offset` | RL | yes | 3.210 | 20.60 | 107.0 | 5.5 | 83.2 |
| `constant_turn_left_3g` | PN | no | 974.722 | 25.00 | 34.1 | 15.7 | 34.0 |
| `constant_turn_left_3g` | APN | no | 2099.780 | 25.00 | 66.0 | 35.6 | 64.5 |
| `constant_turn_left_3g` | OGL | no | 1941.965 | 25.00 | 44.0 | 22.9 | 43.9 |
| `constant_turn_left_3g` | RL | no | 831.826 | 25.00 | 86.5 | 22.7 | 68.4 |
| `constant_turn_right_5g` | PN | no | 1193.873 | 25.00 | 41.3 | 18.1 | 40.9 |
| `constant_turn_right_5g` | APN | no | 3853.294 | 25.00 | 92.8 | 68.3 | 91.9 |
| `constant_turn_right_5g` | OGL | no | 3733.282 | 25.00 | 73.2 | 33.0 | 71.5 |
| `constant_turn_right_5g` | RL | no | 1452.783 | 25.00 | 62.9 | 34.2 | 52.9 |
| `constant_turn_left_7g` | PN | no | 2164.434 | 25.00 | 39.0 | 18.0 | 38.6 |
| `constant_turn_left_7g` | APN | no | 5296.495 | 25.00 | 118.0 | 95.5 | 116.7 |
| `constant_turn_left_7g` | OGL | no | 5198.142 | 25.00 | 102.2 | 37.6 | 96.6 |
| `constant_turn_left_7g` | RL | no | 2514.585 | 25.00 | 135.6 | 52.9 | 107.3 |
| `weave_3g_055hz` | PN | yes | 0.206 | 16.38 | 245.2 | 10.4 | 146.3 |
| `weave_3g_055hz` | APN | yes | 4.508 | 16.36 | 245.2 | 37.2 | 95.5 |
| `weave_3g_055hz` | OGL | yes | 1.454 | 16.36 | 245.2 | 27.6 | 73.0 |
| `weave_3g_055hz` | RL | no | 7.413 | 25.00 | 245.2 | 124.9 | 235.5 |
| `weave_5g_070hz` | PN | yes | 2.060 | 17.62 | 245.2 | 11.1 | 166.7 |
| `weave_5g_070hz` | APN | yes | 3.170 | 17.62 | 245.2 | 55.2 | 146.7 |
| `weave_5g_070hz` | OGL | yes | 4.518 | 17.60 | 245.2 | 41.5 | 180.7 |
| `weave_5g_070hz` | RL | yes | 4.117 | 17.70 | 245.2 | 125.3 | 201.3 |
| `weave_7g_090hz` | PN | yes | 3.608 | 20.02 | 245.2 | 10.8 | 112.0 |
| `weave_7g_090hz` | APN | yes | 1.870 | 20.04 | 245.2 | 65.1 | 147.0 |
| `weave_7g_090hz` | OGL | yes | 4.289 | 20.00 | 245.2 | 48.0 | 95.6 |
| `weave_7g_090hz` | RL | yes | 4.096 | 20.14 | 245.2 | 126.3 | 217.1 |

## Summary

### Where RL beats classical

- **no_maneuver_demo**: both hit; RL miss 1.23 m < best classical (PN) 2.65 m.
- **constant_turn_left_3g**: all miss; RL 831.8 m vs best classical (PN) 974.7 m.

### Where classical beats RL

- **no_maneuver_center**: both hit; best classical (OGL) 0.61 m < RL 3.03 m.
- **no_maneuver_offset**: both hit; best classical (OGL) 1.66 m < RL 3.21 m.
- **constant_turn_right_5g**: all miss; best classical (PN) 1193.9 m vs RL 1452.8 m.
- **constant_turn_left_7g**: all miss; best classical (PN) 2164.4 m vs RL 2514.6 m.
- **weave_3g_055hz**: classical hit (PN) vs RL miss (7.4 m).
- **weave_5g_070hz**: both hit; best classical (PN) 2.06 m < RL 4.12 m.
- **weave_7g_090hz**: both hit; best classical (APN) 1.87 m < RL 4.10 m.

### Ties / near-ties

- None on this matrix.

### Group B (ConstantTurn) — time-budget ceiling

Under the frozen **25 s** fixed-eval budget, ConstantTurn cases are a shared ceiling for all guidance modes (not an RL-only training gap). Every mode misses every Group B case below.

- `constant_turn_left_3g`: PN 975 m; APN 2100 m; OGL 1942 m; RL 832 m.
- `constant_turn_left_7g`: PN 2164 m; APN 5296 m; OGL 5198 m; RL 2515 m.
- `constant_turn_right_5g`: PN 1194 m; APN 3853 m; OGL 3733 m; RL 1453 m.

PN is the strongest classical baseline on these turns. APN/OGL with perfect instantaneous `a_T` are *worse* than PN here because ConstantTurn acceleration rotates with velocity (direction = up × v̂) — the constant-`a_T` assumption baked into APN/OGL does not hold. RL beats PN on the 3 g case (~832 m vs ~975 m) but is still behind PN on 5 g / 7 g; none convert to hits inside 25 s.

Interpretation: extending `max_time` (and retraining under that horizon) would be required to convert these geometries into hits — out of scope for this shadow comparison.

---

*Read-only evaluation against frozen classical laws and `CURRENT_RL_BASELINE.json`. No retraining.*
