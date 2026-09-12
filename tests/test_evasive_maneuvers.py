"""CP0 validation for the evasive maneuver library.

The redesign spec's section 1.1 claims, analytically, that the existing
`SinusoidalWeave` only perturbs the target's path (zero-mean acceleration
integrates to a bounded oscillation about the unperturbed line) while a
break turn / vertical jink / Split-S opens separation that keeps growing.
CP0 is exactly where that analytical claim gets checked against actual
integrated trajectories before any training budget is spent on it.
"""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.physics.atmosphere import G0
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import (
    BreakTurn,
    ConstantTurn,
    ManeuverProfile,
    ManeuverSequence,
    NoManeuver,
    SinusoidalWeave,
    SplitS,
    SquareWaveJink,
    VerticalJink,
)

_DT = 0.02
_WINDOW_S = 20.0


def _target_vehicle() -> VehicleParams:
    return VehicleParams(
        mass=9_100.0,
        reference_area=45.0,
        drag_coefficient=0.035,
        max_normal_force_coefficient=1.1,
        max_load_factor=9.0,
    )


def _fly(
    maneuver: ManeuverProfile,
    *,
    duration_s: float = _WINDOW_S,
    altitude_m: float = 3_300.0,
    speed_m_s: float = 240.0,
    pursuer_state: State | None = None,
) -> np.ndarray:
    """Integrate a lone target under one maneuver; return its position history."""

    target = PointMassEntity(
        name="target",
        state=State(position=[0.0, 0.0, altitude_m], velocity=[-speed_m_s, 0.0, 0.0]),
        vehicle=_target_vehicle(),
    )
    positions = [target.state.position.copy()]
    steps = int(round(duration_s / _DT))
    for index in range(steps):
        t = index * _DT
        maneuver.update_engagement(t, target.state, pursuer_state)
        command = maneuver.lateral_accel(t, target.state)
        target.step(_DT, command, autopilot_tau=0.0)
        positions.append(target.state.position.copy())
    return np.asarray(positions)


def _max_separation_from_baseline(maneuver: ManeuverProfile, **kwargs) -> float:
    """Largest distance between this maneuver's path and the straight-line path."""

    baseline = _fly(NoManeuver(), **kwargs)
    maneuvered = _fly(maneuver, **kwargs)
    return float(np.max(np.linalg.norm(maneuvered - baseline, axis=1)))


# --- Section 1.1: which maneuvers actually displace -------------------------


def test_sinusoidal_weave_is_bounded_only_when_it_starts_at_a_peak():
    """CP0 correction to spec 1.1, which called the weave bounded unconditionally.

    Integrating a(t) = A*sin(wt) once gives v(t) = (A/w)(1 - cos(wt)): a
    velocity with a *nonzero mean* A/w. So a weave starting at zero
    acceleration (phase 0) drifts cross-track at roughly A/w forever -- it is
    not mean-reverting. Only a weave starting at a peak (phase pi/2) yields
    the zero-mean velocity, and therefore the bounded corridor, that the
    spec assumed for every phase.
    """

    drifting_m = _max_separation_from_baseline(
        SinusoidalWeave(amplitude=5.0 * G0, frequency_hz=0.7, phase=0.0)
    )
    bounded_m = _max_separation_from_baseline(
        SinusoidalWeave(amplitude=5.0 * G0, frequency_hz=0.7, phase=np.pi / 2.0)
    )

    assert bounded_m < 50.0
    # Drift is real but an order of magnitude below a break turn's separation.
    assert 100.0 < drifting_m < 400.0
    assert drifting_m > 5.0 * bounded_m


def test_weave_drift_scales_with_amplitude_over_frequency():
    """Confirms the drift mechanism is the A/w velocity offset, not noise."""

    slow = _max_separation_from_baseline(
        SinusoidalWeave(amplitude=5.0 * G0, frequency_hz=0.55, phase=0.0)
    )
    fast = _max_separation_from_baseline(
        SinusoidalWeave(amplitude=5.0 * G0, frequency_hz=0.9, phase=0.0)
    )

    # Halving the period roughly halves the drift: separation ~ A/w.
    assert slow > fast
    assert 1.3 < slow / fast < 2.2


def test_square_wave_jink_is_also_bounded():
    """Randomized jink buys unpredictability, not displacement (spec 1.2 item 3)."""

    separation_m = _max_separation_from_baseline(
        SquareWaveJink(
            amplitude=5.0 * G0,
            period_s=1.5,
            randomize_period=True,
            rng=np.random.default_rng(7),
        )
    )
    assert separation_m < 600.0


@pytest.mark.parametrize(
    "maneuver_factory",
    [
        pytest.param(lambda: BreakTurn(turn_accel=7.0 * G0), id="break_turn"),
        pytest.param(
            lambda: VerticalJink(pullup_accel=5.0 * G0, altitude_delta_m=2_000.0),
            id="vertical_jink",
        ),
        pytest.param(
            lambda: SplitS(dive_accel=7.0 * G0, altitude_loss_m=2_000.0),
            id="split_s",
        ),
    ],
)
def test_displacing_maneuvers_open_real_separation(maneuver_factory):
    """Break turn / vertical jink / Split-S must diverge, not oscillate."""

    separation_m = _max_separation_from_baseline(maneuver_factory())
    assert separation_m > 1_000.0


def test_break_turn_separation_keeps_growing():
    """A held break turn's displacement grows with time rather than saturating."""

    baseline = _fly(NoManeuver())
    turned = _fly(BreakTurn(turn_accel=7.0 * G0))
    separation = np.linalg.norm(turned - baseline, axis=1)
    quarter = len(separation) // 4
    # Strictly increasing across quarters: no bounded-corridor saturation.
    assert separation[quarter] < separation[2 * quarter] < separation[-1]


def test_weave_corridor_is_orders_of_magnitude_below_a_break_turn():
    """The comparison that actually justifies demoting the weave (spec 1.2).

    Note CP0 found the weave is not strictly mean-reverting even at phase
    pi/2: because the command direction rotates with velocity, the system is
    coupled rather than a clean double integral of a sinusoid, so a slow
    residual drift remains. The decision-relevant fact survives that
    correction intact -- the corridor is still ~2 orders of magnitude
    narrower than the separation a held break turn opens.
    """

    weave_m = _max_separation_from_baseline(
        SinusoidalWeave(amplitude=5.0 * G0, frequency_hz=0.7, phase=np.pi / 2.0)
    )
    break_turn_m = _max_separation_from_baseline(BreakTurn(turn_accel=5.0 * G0))

    assert weave_m < 50.0
    assert break_turn_m > 50.0 * weave_m


def test_break_turn_separation_grows_faster_than_linearly():
    """Sustained heading change compounds; a bounded perturbation does not."""

    baseline = _fly(NoManeuver())
    turned = _fly(BreakTurn(turn_accel=5.0 * G0))
    separation = np.linalg.norm(turned - baseline, axis=1)
    half = len(separation) // 2

    # Second half adds strictly more separation than the first half did.
    assert (separation[-1] - separation[half]) > separation[half]


# --- Triggering and composition --------------------------------------------


def test_break_turn_holds_fire_until_its_absolute_trigger():
    maneuver = BreakTurn(turn_accel=7.0 * G0, trigger_time_s=5.0)
    state = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])

    assert np.allclose(maneuver.lateral_accel(4.9, state), np.zeros(3))
    assert np.linalg.norm(maneuver.lateral_accel(5.1, state)) > 0.0


def test_break_turn_triggers_on_time_to_go_when_geometry_is_available():
    maneuver = BreakTurn(turn_accel=7.0 * G0, trigger_time_to_go_s=4.0)
    target = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])

    # 6000 m out, closing at 940 m/s -> t_go ~6.4 s: too early to break.
    far = State(position=[-6_000.0, 0.0, 3_300.0], velocity=[700.0, 0.0, 0.0])
    maneuver.update_engagement(0.0, target, far)
    assert np.allclose(maneuver.lateral_accel(0.0, target), np.zeros(3))

    # 2000 m out at the same closure -> t_go ~2.1 s: inside the trigger.
    near = State(position=[-2_000.0, 0.0, 3_300.0], velocity=[700.0, 0.0, 0.0])
    maneuver.update_engagement(1.0, target, near)
    assert np.linalg.norm(maneuver.lateral_accel(1.0, target)) > 0.0


def test_break_turn_stays_committed_once_triggered():
    """A break that un-triggered as t_go rose would oscillate, not maneuver."""

    maneuver = BreakTurn(turn_accel=7.0 * G0, trigger_time_to_go_s=4.0)
    target = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])
    near = State(position=[-2_000.0, 0.0, 3_300.0], velocity=[700.0, 0.0, 0.0])
    maneuver.update_engagement(0.0, target, near)
    assert np.linalg.norm(maneuver.lateral_accel(0.0, target)) > 0.0

    receding = State(position=[-2_000.0, 0.0, 3_300.0], velocity=[-900.0, 0.0, 0.0])
    maneuver.update_engagement(1.0, target, receding)
    assert np.linalg.norm(maneuver.lateral_accel(1.0, target)) > 0.0


def test_vertical_jink_stops_after_its_altitude_delta():
    maneuver = VerticalJink(
        pullup_accel=5.0 * G0, ramp_time_s=0.0, altitude_delta_m=500.0
    )
    positions = _fly(maneuver, duration_s=40.0)
    climb_m = positions[:, 2] - positions[0, 2]

    assert np.max(climb_m) >= 500.0
    # Command must cut out once the delta is achieved.
    high_state = State(position=[0.0, 0.0, 4_000.0], velocity=[-240.0, 0.0, 0.0])
    assert np.allclose(maneuver.lateral_accel(41.0, high_state), np.zeros(3))


def test_split_s_loses_altitude():
    positions = _fly(
        SplitS(dive_accel=7.0 * G0, altitude_loss_m=1_500.0),
        altitude_m=6_000.0,
        duration_s=25.0,
    )
    altitude_lost_m = positions[0, 2] - np.min(positions[:, 2])

    assert altitude_lost_m >= 1_500.0


def test_randomized_jink_schedule_depends_on_seed():
    state = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])

    def signs(seed: int) -> list[float]:
        maneuver = SquareWaveJink(
            amplitude=5.0 * G0,
            period_s=1.0,
            randomize_period=True,
            rng=np.random.default_rng(seed),
        )
        return [
            float(np.sign(maneuver.lateral_accel(t, state)[1]))
            for t in np.arange(0.0, 20.0, 0.25)
        ]

    assert signs(1) != signs(2)
    assert signs(1) == signs(1)


def test_jink_lateral_accel_is_a_pure_function_of_time():
    """Repeated / out-of-order calls must not advance a hidden schedule."""

    maneuver = SquareWaveJink(
        amplitude=5.0 * G0,
        period_s=1.0,
        randomize_period=True,
        rng=np.random.default_rng(3),
    )
    state = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])

    first = maneuver.lateral_accel(4.0, state).copy()
    maneuver.lateral_accel(9.0, state)
    maneuver.lateral_accel(1.0, state)
    assert np.allclose(maneuver.lateral_accel(4.0, state), first)


def test_maneuver_sequence_runs_segments_in_their_windows():
    sequence = ManeuverSequence(
        [
            (0.0, 5.0, ConstantTurn(accel=5.0 * G0)),
            (5.0, None, VerticalJink(pullup_accel=5.0 * G0, ramp_time_s=0.0)),
        ]
    )
    state = State(position=[0.0, 0.0, 3_300.0], velocity=[-240.0, 0.0, 0.0])

    early = sequence.lateral_accel(1.0, state)
    late = sequence.lateral_accel(6.0, state)

    # First segment is a level turn (no vertical component); second is a pure
    # pull-up (no horizontal component).
    assert abs(early[2]) < 1e-6
    assert np.linalg.norm(early[:2]) > 0.0
    assert late[2] > 0.0


def test_maneuver_sequence_composition_displaces_more_than_either_alone():
    turn_only = _max_separation_from_baseline(BreakTurn(turn_accel=5.0 * G0))
    sequence = ManeuverSequence(
        [
            (0.0, None, BreakTurn(turn_accel=5.0 * G0)),
            (4.0, None, VerticalJink(pullup_accel=4.0 * G0, ramp_time_s=0.5)),
        ]
    )
    combined = _max_separation_from_baseline(sequence)

    assert combined > turn_only
