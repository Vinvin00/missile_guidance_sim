"""Training distribution and held-out eval set for the evasive-target redesign.

Two distinct things live here, deliberately drawn from disjoint seed streams:

* ``evasive_maneuver_factory`` -- the training distribution over the v1
  maneuver set (break turn, vertical jink, randomized jink, and the retained
  bounded weave). Split-S is excluded at CP1 to isolate its altitude-budget
  risk; it is introduced at CP5.
* ``build_held_out_cases`` -- a seeded generalization set sampled from the
  same ranges but from a separate seed base, so passing it is evidence of
  generalization rather than a resample of training conditions.

Sampling ranges are stated as constants rather than inlined so a reviewer can
see the whole distribution in one place.
"""

from __future__ import annotations

from typing import Callable

import numpy as np

from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import State
from guidance_sim.physics.maneuvers import (
    BreakTurn,
    ManeuverProfile,
    SinusoidalWeave,
    SplitS,
    SquareWaveJink,
    VerticalJink,
)

# Target airframe limit is 9 g; break turns sit at the top of the envelope.
BREAK_TURN_G_RANGE = (5.0, 9.0)
BREAK_TURN_TRIGGER_TGO_RANGE_S = (3.0, 10.0)
BREAK_TURN_BANK_RANGE_DEG = (0.0, 45.0)

VERTICAL_JINK_G_RANGE = (3.0, 7.0)
VERTICAL_JINK_TRIGGER_RANGE_S = (2.0, 12.0)
VERTICAL_JINK_ALTITUDE_DELTA_RANGE_M = (500.0, 2_000.0)

JINK_G_RANGE = (3.0, 7.0)
JINK_PERIOD_RANGE_S = (0.8, 2.5)
JINK_ONSET_RANGE_S = (0.0, 6.0)

# Retained bounded perturbation: kept so "does the policy still overreact to a
# small bounded disturbance" stays directly checkable under the new baseline.
WEAVE_G_RANGE = (3.0, 7.0)
WEAVE_FREQUENCY_RANGE_HZ = (0.5, 1.0)

SPLIT_S_G_RANGE = (5.0, 9.0)
SPLIT_S_ALTITUDE_LOSS_RANGE_M = (1_000.0, 2_500.0)
SPLIT_S_TRIGGER_RANGE_S = (2.0, 10.0)
SPLIT_S_MIN_START_ALTITUDE_M = 5_000.0

CP1_MANEUVER_KINDS: tuple[str, ...] = (
    "break_turn",
    "vertical_jink",
    "random_jink",
    "bounded_weave",
)
ALL_MANEUVER_KINDS: tuple[str, ...] = CP1_MANEUVER_KINDS + ("split_s",)

# Disjoint from the training seed (20_260_909 + 10_000*cp) and from the frozen
# fixed-eval seed base (91_000).
HELD_OUT_SEED_BASE = 770_000


def _uniform(rng: np.random.Generator, bounds: tuple[float, float]) -> float:
    return float(rng.uniform(bounds[0], bounds[1]))


def _sign(rng: np.random.Generator) -> float:
    return -1.0 if float(rng.random()) < 0.5 else 1.0


def sample_maneuver(rng: np.random.Generator, kind: str) -> ManeuverProfile:
    """Draw one maneuver of the requested kind from its documented range."""

    if kind == "break_turn":
        return BreakTurn(
            turn_accel=_uniform(rng, BREAK_TURN_G_RANGE) * G0,
            trigger_time_to_go_s=_uniform(rng, BREAK_TURN_TRIGGER_TGO_RANGE_S),
            bank_angle_deg=_uniform(rng, BREAK_TURN_BANK_RANGE_DEG),
            turn_sign=_sign(rng),
        )
    if kind == "vertical_jink":
        return VerticalJink(
            pullup_accel=_uniform(rng, VERTICAL_JINK_G_RANGE) * G0,
            trigger_time_s=_uniform(rng, VERTICAL_JINK_TRIGGER_RANGE_S),
            altitude_delta_m=_uniform(rng, VERTICAL_JINK_ALTITUDE_DELTA_RANGE_M),
            climb=bool(rng.random() < 0.5),
        )
    if kind == "random_jink":
        axis = str(rng.choice(np.asarray(["horizontal", "vertical", "combined"])))
        return SquareWaveJink(
            amplitude=_uniform(rng, JINK_G_RANGE) * G0,
            period_s=_uniform(rng, JINK_PERIOD_RANGE_S),
            axis=axis,
            onset_delay_s=_uniform(rng, JINK_ONSET_RANGE_S),
            randomize_period=True,
            rng=rng,
        )
    if kind == "bounded_weave":
        return SinusoidalWeave(
            amplitude=_uniform(rng, WEAVE_G_RANGE) * G0,
            frequency_hz=_uniform(rng, WEAVE_FREQUENCY_RANGE_HZ),
            phase=float(rng.uniform(0.0, 2.0 * np.pi)),
        )
    if kind == "split_s":
        return SplitS(
            dive_accel=_uniform(rng, SPLIT_S_G_RANGE) * G0,
            altitude_loss_m=_uniform(rng, SPLIT_S_ALTITUDE_LOSS_RANGE_M),
            trigger_time_s=_uniform(rng, SPLIT_S_TRIGGER_RANGE_S),
            roll_sign=_sign(rng),
        )
    raise ValueError(f"unknown maneuver kind: {kind!r}")


def make_maneuver_factory(
    kinds: tuple[str, ...] = CP1_MANEUVER_KINDS,
) -> Callable[[np.random.Generator], ManeuverProfile]:
    """Uniform mixture over the given maneuver kinds."""

    def factory(rng: np.random.Generator) -> ManeuverProfile:
        kind = str(rng.choice(np.asarray(kinds)))
        return sample_maneuver(rng, kind)

    return factory


evasive_maneuver_factory = make_maneuver_factory()


def evasive_initial_conditions(
    rng: np.random.Generator,
) -> tuple[State, State]:
    """Engagement geometry with enough altitude for vertical maneuvering.

    Same family as ``training_initial_conditions`` but with the target started
    higher: a vertical jink or Split-S needs room to dive without the episode
    ending on a ground impact that says nothing about guidance quality.
    """

    target_range_m = float(rng.uniform(6_000.0, 8_000.0))
    lateral_offset_m = float(rng.uniform(-800.0, 800.0))
    target_altitude_m = float(rng.uniform(5_200.0, 6_500.0))
    target_speed_m_s = float(rng.uniform(180.0, 260.0))
    heading_error_rad = float(np.deg2rad(rng.uniform(-2.0, 2.0)))
    pursuer_speed_m_s = 350.0
    pursuer_altitude_m = target_altitude_m - float(rng.uniform(200.0, 600.0))
    return (
        State(
            position=[0.0, 0.0, pursuer_altitude_m],
            velocity=[
                pursuer_speed_m_s * np.cos(heading_error_rad),
                pursuer_speed_m_s * np.sin(heading_error_rad),
                0.0,
            ],
        ),
        State(
            position=[target_range_m, lateral_offset_m, target_altitude_m],
            velocity=[-target_speed_m_s, 0.0, 0.0],
        ),
    )


def _frozen_builders(seed: int, kind: str):
    """Deterministic (IC, maneuver) builders for one held-out case.

    Each case owns its own generator seeded from the held-out base, so a case
    replays identically regardless of evaluation order or of the env seed the
    caller passes.
    """

    def initial_conditions(_rng: np.random.Generator) -> tuple[State, State]:
        return evasive_initial_conditions(np.random.default_rng(seed))

    def maneuver(_rng: np.random.Generator) -> ManeuverProfile:
        # Offset keeps the maneuver draw independent of the geometry draw.
        return sample_maneuver(np.random.default_rng(seed + 1), kind)

    return initial_conditions, maneuver


def build_held_out_cases(
    n_cases: int = 50,
    *,
    kinds: tuple[str, ...] = CP1_MANEUVER_KINDS,
    seed_base: int = HELD_OUT_SEED_BASE,
):
    """Seeded generalization set, balanced across maneuver kinds.

    Returns ``EvaluationCase`` objects carrying explicit builders, so they run
    through the existing ``evaluate_policy`` loop unchanged.
    """

    from guidance_sim.rl.training import EvaluationCase

    cases = []
    for index in range(n_cases):
        kind = kinds[index % len(kinds)]
        seed = seed_base + 100 * index
        initial_conditions, maneuver = _frozen_builders(seed, kind)
        pursuer_state, target_state = initial_conditions(np.random.default_rng(seed))
        cases.append(
            EvaluationCase(
                name=f"heldout_{index:02d}_{kind}",
                target_position_m=tuple(float(v) for v in target_state.position),
                target_velocity_m_s=tuple(float(v) for v in target_state.velocity),
                maneuver=kind,
                maneuver_builder=maneuver,
                initial_condition_builder=initial_conditions,
            )
        )
    return tuple(cases)
