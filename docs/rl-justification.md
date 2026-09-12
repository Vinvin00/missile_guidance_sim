# Why RL remains in this project

**Data source:** [`outputs/shadow_comparison/shadow_comparison_report.md`](../outputs/shadow_comparison/shadow_comparison_report.md)
(frozen PN / APN / OGL / RL matrix on the nine fixed-eval cases; no new
runs for this document). Intercept radius is 5 m; time budget is 25 s.

## 1. The claim, stated plainly

RL is **not** a uniform improvement over classical PN. On the nine-scenario
shadow matrix it wins clearly on **2 of 9** cases (`no_maneuver_demo`:
1.2 m vs PN 2.6 m; `constant_turn_left_3g`: 832 m vs PN 975 m), loses
outright on **3 of 9** (`weave_3g_055hz`: RL misses at 7.4 m while PN hits
at 0.2 m; `constant_turn_right_5g` and `constant_turn_left_7g`: PN beats RL
by roughly 26–30% on miss distance — 1194 vs 1453 m and 2164 vs 2515 m),
and is roughly comparable on the remaining **4 of 9** (all hits on both
sides for `no_maneuver_center`, `no_maneuver_offset`, `weave_5g_070hz`, and
`weave_7g_090hz`, with classical often slightly tighter). That mix — two
clear wins, three clear losses, four near-ties — is the result. It is not
“RL beats classical guidance.”

## 2. The ConstantTurn 3 g win (narrow, not general)

On `constant_turn_left_3g`, every mode **misses** and every mode exhausts
the full **25 s** budget (shadow detailed metrics: PN/APN/OGL/RL all
`time_s = 25.00`). Closest approaches are hundreds of metres (PN 975 m,
RL 832 m), not near-intercept. That matches the existing Group B
diagnosis: against a sustained turn that needs on the order of
**~35–40 s** of phase catch-up to convert, the frozen eval horizon is a
**shared time-budget ceiling**, not an RL-specific training failure.

Within that ceiling, RL’s 832 m vs PN’s 975 m is a real but **narrow**
edge — graded on closest-approach shaping rather than PN’s fixed
geometry. It does **not** generalize: on `constant_turn_right_5g` and
`constant_turn_left_7g`, PN remains clearly better (1194 vs 1453 m;
2164 vs 2515 m), and neither mode hits. APN/OGL are worse still on all
three turns (constant-`a_T` assumption vs rotating turn acceleration);
that classical comparison is orthogonal to the RL-vs-PN 3 g claim.

## 3. The `weave_3g_055hz` loss is a real finding

Across the full nine-scenario hit/miss table, every recorded **hit** has
miss distance **under 5 m** (the intercept radius). Every **genuine
timeout miss** on Group B sits in the **hundreds to thousands** of metres
(832–5296 m in this report). RL’s `weave_3g_055hz` result — **7.4 m**,
outcome miss — sits in **neither** cluster: it is past the hit gate, yet
far closer to the hit band than to a flyby. That placement is why this is
treated as a real miss / control failure relative to classical, not
intercept-boundary noise around a would-be hit.

Evidence already in the shadow detailed metrics (no new simulation):
classical PN/APN/OGL all **hit at ~16.4 s** (miss 0.2 / 4.5 / 1.5 m),
while RL runs to **timeout at 25.00 s** with miss 7.4 m. RL’s mean
commanded lateral accel on that case is **124.9 m/s²** versus PN’s
**10.4 m/s²**, with peak command at the shared clamp (**245.2 m/s²**).
In one line: the policy over-drove lateral command through the full
budget and never closed inside 5 m, whereas PN intercepted cleanly ~8.6 s
earlier.

## 4. Justification for keeping RL

The defensible claim, backed only by the numbers in §1–§3, is narrower
than a portfolio headline of “learned guidance wins”:

> RL demonstrates **comparable** hit performance to hand-tuned classical
> laws on most Group A engagements **without** manual navigation-constant
> or geometry tuning, and shows a **measurable but narrow**
> closest-approach edge on the softest time-budget-constrained
> ConstantTurn (3 g: 832 m vs PN 975 m). It is **not** a replacement for
> PN: classical remains better on harder turns and uniquely succeeds on
> the resonant `weave_3g_055hz` case where this baseline misses.

That is why RL stays in the project: as a **fair, information-matched
comparison arm** and a demonstration that a learned policy can reach
near-classical competence on the frozen matrix — including one real
budget-constrained improvement — while remaining honest about where it
loses.

What this document does **not** claim: uniform superiority; Group B
hits; generalization of the 3 g edge to 5 g / 7 g; or that the weave
miss is an artifact.

## Appendix — full shadow comparison table

Copied from
[`outputs/shadow_comparison/shadow_comparison_report.md`](../outputs/shadow_comparison/shadow_comparison_report.md)
(hit / miss + miss distance).

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
