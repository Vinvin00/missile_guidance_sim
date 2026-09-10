# Visualization scenario parameter grounding

`Interceptor A` and `Target B` are generic illustrative point-mass
surrogates synthesized from public, generic simulation literature. They do
not represent or claim the performance of any real system.

**Engagement framing.** Interceptor A is a missile-class pursuer. Target B
is also framed as a **missile-class** target for engagement kinematics
(speed class ~500 m/s per NPS ADA378653), not a subsonic fighter. Other
Target B mass/aero scalars in the catalog still cite fighter/transport
generic models and remain review metadata until a separately approved
re-grounding pass.

The API catalog exposes the selected value, review range, source IDs, and
basis for every vehicle parameter. `S` means a conservative range synthesized
from multiple public examples; `I` means a reduced-order scalar that remains
explicitly illustrative because the real quantity varies with flight
condition.

| Parameter | Interceptor A: reference range → selected | Target B: reference range → selected | Basis |
|---|---:|---:|---|
| Initial speed | 600–1,000 m/s → **700 m/s** | 300–600 m/s → **500 m/s** | S: [1–4] (Target B speed: [2]) |
| Mass | 50–300 kg → **200 kg** | 9,000–27,200 kg → **9,100 kg** | S: [1–3], [6–7] |
| Reference area | 0.04–0.08 m² → **0.05 m² frontal** | 45–50 m² → **45 m² wing** | S: [2–3], [6–7] |
| Constant drag coefficient | 0.20–0.40 → **0.30** | 0.03–0.05 → **0.035** | S/I: [2–3], [5], [7] |
| Maximum normal-force coefficient | 4–6 → **5** | 1.0–1.2 → **1.1** | I: [5], [8] |
| Maneuver/load limit | 20–30 g → **25 g** | 3–9 g → **9 g** | S: [1–3], [6] |
| Initial altitude | 2–6 km → **3.3 km** | 2–6 km → **3.3 km** | S: [1–3], [6] |
| Initial separation | 4–7 km → **6 km shared** | 4–7 km → **6 km shared** | S: [1–4] |

## Scenario picker (RL taxonomy labels)

Catalog scenario **labels** match the RL track maneuver taxonomy. Stable
scenario **ids** and the synthetic geometry behind each id are unchanged;
only the names shown in the viewer picker differ.

| Catalog id | Picker label | Role in preview |
|---|---|---|
| `crossing-intercept` | **NoManeuver** | Non-maneuvering target path |
| `head-on-intercept` | **ConstantTurn** | Label aligned to ConstantTurn tier |
| `evasive-climb` | **SinusoidalWeave** | Bounded climbing weave path |

## Public anchors

1. [NASA TM-109057, *The Analysis of a Generic Air-to-Air Missile
   Simulation Model*](https://ntrs.nasa.gov/api/citations/19940031931/downloads/19940031931.pdf):
   56.7 kg launch mass, 30 g maximum acceleration, 4.02 km range, 6 km
   test altitude, and Mach 0.7 aircraft/target examples.
2. [Naval Postgraduate School, *Missile Terminal Guidance and Control
   Against Evasive Targets*](https://apps.dtic.mil/sti/tr/pdf/ADA378653.pdf)
   (ADA378653): generic 300 kg body, 0.0707 m² frontal area, `Cd=0.2`,
   1,000 m/s interceptor, **500 m/s target**, 6–6.5 km separation,
   20 g/9 g limits, and 2 km altitude. Primary anchor for Target B
   missile-class speed.
3. [*Improvements in Classical Proportional Navigation Guidance Using
   Fuzzy Logic*](https://doi.org/10.61653/joast.v72i4.2020.190):
   generic 204.32 kg model, 0.0408 m² reference area, `Cd0=0.300`,
   984/300 m/s initial speeds, 20 g/9 g limits, and 3.3 km altitude.
4. [*Trajectory Modeling Calculation and Maneuverability Analysis of
   Proportional Navigation Method*](https://ceur-ws.org/Vol-3206/paper11.pdf):
   academic 600/300 m/s example with 7 km initial separation.
5. [Army ARL-TR-2318, *CFD Analysis of a Generic Missile With Grid
   Fins*](https://www.govinfo.gov/content/pkg/GOVPUB-D101-PURL-gpo5165/pdf/GOVPUB-D101-PURL-gpo5165.pdf):
   base-area axial coefficients 0.1895–0.4677 at Mach 2.5 and measured
   normal coefficients 3.543–5.465 at 20° angle of attack.
6. [FOI-R--1624--SE, *ADMIRE—The Aero-Data Model in a Research
   Environment*](https://www.foi.se/rest-api/report/FOI-R--1624--SE):
   public generic small-fighter model with 9,100 kg mass, 45 m² wing
   area, sub-Mach-1.2/below-6-km envelope, and −3 to +9 g constraint.
7. [AIAA-2024-3194, *Climb Performance of High Thrust-to-Weight Ratio
   Airframes*](https://labs.engineering.asu.edu/aircraft-design/wp-content/uploads/sites/115/2024/07/AIAA-2024-3194-ClimbAtHighTW.pdf):
   generic 15.9–27.2 t cases, 46.45 m² wing, `Cd0≈0.025`,
   induced-drag factor `k≈0.053`, and 242 m/s example speed.
8. [*Aerodynamic Modeling for Post-Stall Flight Simulation of a
   Transport Airplane*](https://doi.org/10.2514/1.C034790):
   generic-transport CFD cases with maximum normal coefficients of
   0.971 and 1.17 at two Reynolds numbers.

## Review caveats

- Reference-area conventions are intentionally different: frontal
  cross-section for Interceptor A and wing planform for Target B.
- A fixed `Cd` and a single maximum normal-force coefficient are
  reduced-order placeholders. They must not be presented as universal
  class-wide constants; a later physics connection should use
  Mach/angle-of-attack-dependent data.
- Range and altitude are scenario settings, not intrinsic vehicle
  performance claims.
- Target B **speed** is missile-class ([2]); Target B **mass / wing area /
  Cd** still cite fighter/transport generics ([6–7]) and should not be
  read as a single coherent airframe.
- The current WebSocket preview is synthetic. It uses speed, altitude,
  and separation to shape display data; mass, area, coefficients, and
  g-limits are review metadata until a separately approved simulation
  adapter is added. Each `trajectory.frame` carries
  `pursuer_accel_cmd_m_s2` and `pursuer_accel_achieved_m_s2` as mock
  lateral vectors so the commanded/achieved contract is frozen before
  checkpoint loading.
