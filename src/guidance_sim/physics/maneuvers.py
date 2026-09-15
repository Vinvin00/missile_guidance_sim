"""
Target maneuver profiles, generalized to 3D.

In 2D there's exactly one "perpendicular to velocity" direction, so a
maneuver could be a scalar. In 3D there's a whole plane of directions
perpendicular to velocity, so a maneuver needs to say *which* one --
these profiles do that by picking a reference axis (e.g. "up") and
turning/weaving in the plane that axis defines relative to the
vehicle's current velocity. Because of that, `lateral_accel` now
takes the current `State`, not just time.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

import numpy as np

from guidance_sim.physics.atmosphere import isa_density
from guidance_sim.physics.aerodynamics import dynamic_pressure
from guidance_sim.physics.dynamics import flight_path_angle
from guidance_sim.physics.entities import AttitudeAugmentedEntity, State

UP = np.array([0.0, 0.0, 1.0])


def _turn_direction(velocity: np.ndarray, reference_axis: np.ndarray) -> np.ndarray:
    """
    Unit vector perpendicular to velocity, in the plane defined by
    `reference_axis` and velocity -- e.g. reference_axis=UP gives a
    horizontal turn direction; reference_axis pointing sideways gives
    a vertical pull-up/push-over direction.
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-6:
        return np.zeros(3)
    v_hat = velocity / speed
    raw = np.cross(reference_axis, v_hat)
    norm = np.linalg.norm(raw)
    if norm < 1e-9:
        # velocity is parallel to reference_axis; pick an arbitrary
        # perpendicular direction so the maneuver is still defined
        fallback = np.array([1.0, 0.0, 0.0]) if abs(v_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        raw = np.cross(fallback, v_hat)
        norm = np.linalg.norm(raw)
    return raw / norm


def _vertical_direction(velocity: np.ndarray) -> np.ndarray:
    """
    Unit vector perpendicular to velocity, in the vertical plane containing
    velocity, pointing "up" (positive z component). This is the pull-up
    direction; negate it for a push-over/dive.
    """
    speed = np.linalg.norm(velocity)
    if speed < 1e-6:
        return np.zeros(3)
    v_hat = velocity / speed
    raw = UP - np.dot(UP, v_hat) * v_hat
    norm = np.linalg.norm(raw)
    if norm < 1e-9:
        # Velocity is vertical; every perpendicular direction is horizontal,
        # so there is no meaningful "up" -- pick a stable horizontal axis.
        fallback = np.array([1.0, 0.0, 0.0])
        raw = fallback - np.dot(fallback, v_hat) * v_hat
        norm = np.linalg.norm(raw)
        if norm < 1e-9:
            return np.zeros(3)
    return raw / norm


def _time_to_go(target_state: State, pursuer_state: State) -> Optional[float]:
    """Range / closing speed; None when receding or parallel (no finite t_go)."""
    relative_position = target_state.position - pursuer_state.position
    relative_velocity = target_state.velocity - pursuer_state.velocity
    range_m = float(np.linalg.norm(relative_position))
    closing_speed = -float(np.dot(relative_position, relative_velocity)) / max(range_m, 1e-9)
    return range_m / closing_speed if closing_speed > 1e-6 else None


class ManeuverProfile(ABC):
    """Base interface: given time t and current state, return a 3D lateral accel command (m/s^2, world frame)."""

    @abstractmethod
    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        raise NotImplementedError

    def update_engagement(
        self,
        t: float,
        target_state: State,
        pursuer_state: Optional[State],
    ) -> None:
        """Optional hook for maneuvers that trigger off engagement geometry.

        Called by the simulation before ``lateral_accel`` each step. A v1
        scripted target is allowed to use true pursuer geometry here: the
        target is not the entity whose observability is being degraded.
        Profiles that ignore engagement geometry need not override this.
        """


class NoManeuver(ManeuverProfile):
    """Non-maneuvering target: ballistic/straight, no commanded turn."""

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        return np.zeros(3)


class ConstantTurn(ManeuverProfile):
    """
    Holds a constant-magnitude lateral acceleration in the turn
    direction defined by `reference_axis` (default: a horizontal
    turn). Produces a roughly constant-radius turn once the entity's
    speed settles.
    """

    def __init__(self, accel: float, reference_axis: np.ndarray = UP):
        self.accel = accel
        self.reference_axis = np.asarray(reference_axis, dtype=float)

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        direction = _turn_direction(state.velocity, self.reference_axis)
        return self.accel * direction


class SinusoidalWeave(ManeuverProfile):
    """
    Oscillates lateral acceleration sinusoidally in the plane defined
    by `reference_axis` -- a classic "jinking" evasive profile,
    generalized to weave horizontally, vertically, or anywhere in
    between depending on the chosen axis.
    """

    def __init__(self, amplitude: float, frequency_hz: float, phase: float = 0.0,
                 reference_axis: np.ndarray = UP):
        self.amplitude = amplitude
        self.frequency_hz = frequency_hz
        self.phase = phase
        self.reference_axis = np.asarray(reference_axis, dtype=float)

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        direction = _turn_direction(state.velocity, self.reference_axis)
        magnitude = self.amplitude * np.sin(2 * np.pi * self.frequency_hz * t + self.phase)
        return magnitude * direction


def _axis_direction(axis: str, velocity: np.ndarray) -> np.ndarray:
    """Resolve a named maneuver axis into a unit direction perpendicular to velocity."""

    if axis == "horizontal":
        return _turn_direction(velocity, UP)
    if axis == "vertical":
        return _vertical_direction(velocity)
    if axis == "combined":
        combined = _turn_direction(velocity, UP) + _vertical_direction(velocity)
        norm = float(np.linalg.norm(combined))
        return combined / norm if norm > 1e-9 else np.zeros(3)
    raise ValueError(f"axis must be 'horizontal', 'vertical', or 'combined'; got {axis!r}")


class BreakTurn(ManeuverProfile):
    """
    Hard turn at/near the target's structural limit, timed against the
    missile's time-to-go.

    Unlike `SinusoidalWeave` (whose zero-mean acceleration integrates to a
    bounded oscillation about the unperturbed path), a break turn holds its
    sign, so heading change -- and therefore lateral displacement -- grows
    for as long as it is held. That is the mechanism that actually opens
    separation against a pursuer whose guidance assumes a roughly fixed
    engagement geometry.

    `bank_angle_deg` tilts the acceleration out of the horizontal plane:
    0 deg is a level break turn, +90 deg is a pure pull-up.

    Triggering prefers `trigger_time_to_go_s` (needs engagement geometry via
    `update_engagement`); without it, or before any geometry arrives, the
    maneuver falls back to the absolute `trigger_time_s`.
    """

    def __init__(
        self,
        turn_accel: float,
        trigger_time_to_go_s: Optional[float] = None,
        trigger_time_s: float = 0.0,
        bank_angle_deg: float = 0.0,
        turn_sign: float = 1.0,
    ):
        self.turn_accel = float(turn_accel)
        self.trigger_time_to_go_s = (
            None if trigger_time_to_go_s is None else float(trigger_time_to_go_s)
        )
        self.trigger_time_s = float(trigger_time_s)
        self.bank_angle_rad = float(np.deg2rad(bank_angle_deg))
        self.turn_sign = 1.0 if turn_sign >= 0.0 else -1.0
        self._time_to_go_s: Optional[float] = None
        self._triggered_at_s: Optional[float] = None

    def update_engagement(
        self,
        t: float,
        target_state: State,
        pursuer_state: Optional[State],
    ) -> None:
        if pursuer_state is None:
            self._time_to_go_s = None
            return
        self._time_to_go_s = _time_to_go(target_state, pursuer_state)

    def _is_active(self, t: float) -> bool:
        # Once a break is committed it is held for the rest of the run; a
        # break turn that stopped the instant t_go rose again would be a
        # re-triggering oscillation, not a maneuver.
        if self._triggered_at_s is not None:
            return True
        triggered = False
        if self.trigger_time_to_go_s is not None and self._time_to_go_s is not None:
            triggered = self._time_to_go_s <= self.trigger_time_to_go_s
        else:
            triggered = t >= self.trigger_time_s
        if triggered:
            self._triggered_at_s = t
        return triggered

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        if not self._is_active(t):
            return np.zeros(3)
        horizontal = _turn_direction(state.velocity, UP)
        vertical = _vertical_direction(state.velocity)
        direction = (
            np.cos(self.bank_angle_rad) * self.turn_sign * horizontal
            + np.sin(self.bank_angle_rad) * vertical
        )
        norm = float(np.linalg.norm(direction))
        if norm < 1e-9:
            return np.zeros(3)
        return self.turn_accel * direction / norm


class VerticalJink(ManeuverProfile):
    """
    Climb or dive: a step change in flight-path angle, ramped over a
    realistic transition time, held until `altitude_delta_m` is achieved.

    Displacement in the vertical axis is not mean-reverting the way a
    sinusoidal weave is, so this opens genuine separation and moves the
    intercept geometry out of the pursuer's current plane.
    """

    def __init__(
        self,
        pullup_accel: float,
        trigger_time_s: float = 0.0,
        ramp_time_s: float = 0.75,
        altitude_delta_m: Optional[float] = None,
        climb: bool = True,
    ):
        if ramp_time_s < 0.0:
            raise ValueError("ramp_time_s must be non-negative")
        if altitude_delta_m is not None and altitude_delta_m <= 0.0:
            raise ValueError("altitude_delta_m must be positive when set")
        self.pullup_accel = float(pullup_accel)
        self.trigger_time_s = float(trigger_time_s)
        self.ramp_time_s = float(ramp_time_s)
        self.altitude_delta_m = altitude_delta_m
        self.climb = bool(climb)
        self._start_altitude_m: Optional[float] = None
        self._complete = False

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        if t < self.trigger_time_s or self._complete:
            return np.zeros(3)
        if self._start_altitude_m is None:
            self._start_altitude_m = float(state.altitude())
        if self.altitude_delta_m is not None:
            achieved = abs(float(state.altitude()) - self._start_altitude_m)
            if achieved >= self.altitude_delta_m:
                self._complete = True
                return np.zeros(3)
        elapsed = t - self.trigger_time_s
        ramp = 1.0 if self.ramp_time_s <= 0.0 else min(1.0, elapsed / self.ramp_time_s)
        direction = _vertical_direction(state.velocity)
        sign = 1.0 if self.climb else -1.0
        return sign * ramp * self.pullup_accel * direction


class SquareWaveJink(ManeuverProfile):
    """
    Square-wave lateral acceleration with reversals every `period_s`,
    optionally non-periodic.

    Real jinking favors unpredictability over smoothness -- a fixed-frequency
    weave is partially anticipatable, which is exactly why the randomized
    variant matters. Note this is an *unpredictability* layer, not a
    displacement mechanism: like the sinusoidal weave, a zero-mean reversing
    acceleration produces bounded oscillation about the baseline path. Pair
    it with a break turn or vertical jink for genuine separation.

    The reversal schedule is drawn up front from `rng` rather than advanced
    per call, so `lateral_accel` stays a pure function of `t` and is safe to
    call repeatedly or out of order.
    """

    _SCHEDULE_HORIZON_S = 120.0

    def __init__(
        self,
        amplitude: float,
        period_s: float,
        axis: str = "horizontal",
        onset_delay_s: float = 0.0,
        randomize_period: bool = False,
        jitter_fraction: float = 0.4,
        rng: Optional[np.random.Generator] = None,
    ):
        if period_s <= 0.0:
            raise ValueError("period_s must be positive")
        if not (0.0 <= jitter_fraction < 1.0):
            raise ValueError("jitter_fraction must be in [0, 1)")
        _axis_direction(axis, np.array([1.0, 0.0, 0.0]))  # validate axis name
        self.amplitude = float(amplitude)
        self.period_s = float(period_s)
        self.axis = axis
        self.onset_delay_s = float(onset_delay_s)
        self.randomize_period = bool(randomize_period)
        self.jitter_fraction = float(jitter_fraction)
        self._reversal_times = self._build_schedule(rng)

    def _build_schedule(self, rng: Optional[np.random.Generator]) -> np.ndarray:
        if not self.randomize_period:
            return np.empty(0)
        generator = rng if rng is not None else np.random.default_rng()
        times: list[float] = []
        elapsed = 0.0
        while elapsed < self._SCHEDULE_HORIZON_S:
            low = self.period_s * (1.0 - self.jitter_fraction)
            high = self.period_s * (1.0 + self.jitter_fraction)
            elapsed += float(generator.uniform(low, high))
            times.append(elapsed)
        return np.asarray(times, dtype=float)

    def _sign(self, elapsed: float) -> float:
        if not self.randomize_period:
            half_periods = int(np.floor(elapsed / (self.period_s / 2.0)))
            return 1.0 if half_periods % 2 == 0 else -1.0
        reversals = int(np.searchsorted(self._reversal_times, elapsed, side="right"))
        return 1.0 if reversals % 2 == 0 else -1.0

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        elapsed = t - self.onset_delay_s
        if elapsed < 0.0:
            return np.zeros(3)
        direction = _axis_direction(self.axis, state.velocity)
        return self._sign(elapsed) * self.amplitude * direction


class SplitS(ManeuverProfile):
    """
    Half-roll followed by a pull-through dive: rapid heading reversal plus
    altitude loss.

    Point-mass caveat: the target entity carries no attitude or angle-of-attack
    state, so the roll itself cannot be modelled directly. It is approximated
    as the lift vector rotating from horizontal to vertical-down over
    `roll_time_s`, after which the dive is held at `dive_accel` until
    `altitude_loss_m` is given up. Needs enough starting altitude that the
    dive does not fly into the ground mid-maneuver.
    """

    def __init__(
        self,
        dive_accel: float,
        roll_time_s: float = 1.0,
        altitude_loss_m: float = 1_500.0,
        trigger_time_s: float = 0.0,
        roll_sign: float = 1.0,
    ):
        if roll_time_s < 0.0:
            raise ValueError("roll_time_s must be non-negative")
        if altitude_loss_m <= 0.0:
            raise ValueError("altitude_loss_m must be positive")
        self.dive_accel = float(dive_accel)
        self.roll_time_s = float(roll_time_s)
        self.altitude_loss_m = float(altitude_loss_m)
        self.trigger_time_s = float(trigger_time_s)
        self.roll_sign = 1.0 if roll_sign >= 0.0 else -1.0
        self._start_altitude_m: Optional[float] = None
        self._complete = False

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        if t < self.trigger_time_s or self._complete:
            return np.zeros(3)
        if self._start_altitude_m is None:
            self._start_altitude_m = float(state.altitude())
        lost = self._start_altitude_m - float(state.altitude())
        if lost >= self.altitude_loss_m:
            self._complete = True
            return np.zeros(3)

        elapsed = t - self.trigger_time_s
        horizontal = _turn_direction(state.velocity, UP)
        down = -_vertical_direction(state.velocity)
        if self.roll_time_s > 0.0 and elapsed < self.roll_time_s:
            # Lift vector rotating from level toward inverted/pull-through.
            fraction = elapsed / self.roll_time_s
            angle = 0.5 * np.pi * fraction
            direction = np.cos(angle) * self.roll_sign * horizontal + np.sin(angle) * down
        else:
            direction = down
        norm = float(np.linalg.norm(direction))
        if norm < 1e-9:
            return np.zeros(3)
        return self.dive_accel * direction / norm


class ManeuverSequence(ManeuverProfile):
    """
    Composes several profiles into one scripted sequence -- e.g. break turn at
    t=trigger, then vertical jink at t=trigger+delta.

    Segments are time-windowed and summed while active (the entity clamps the
    total to what the airframe can achieve anyway), so overlapping segments
    blend rather than one silently winning.
    """

    def __init__(
        self,
        segments: Sequence[tuple[float, Optional[float], ManeuverProfile]],
    ):
        if not segments:
            raise ValueError("ManeuverSequence requires at least one segment")
        for start_s, end_s, profile in segments:
            if not isinstance(profile, ManeuverProfile):
                raise TypeError("each segment must carry a ManeuverProfile")
            if end_s is not None and end_s <= start_s:
                raise ValueError("segment end_s must be greater than start_s")
        self.segments = list(segments)

    def update_engagement(
        self,
        t: float,
        target_state: State,
        pursuer_state: Optional[State],
    ) -> None:
        for _start_s, _end_s, profile in self.segments:
            profile.update_engagement(t, target_state, pursuer_state)

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        total = np.zeros(3)
        for start_s, end_s, profile in self.segments:
            if t < start_s:
                continue
            if end_s is not None and t >= end_s:
                continue
            # Segment-local time, so a profile's own trigger/ramp offsets are
            # relative to when its segment opens, not to episode start.
            total = total + profile.lateral_accel(t - start_s, state)
        return total


class CobraManeuver(ManeuverProfile):
    """
    Post-stall "Cobra" evasion for an `AttitudeAugmentedEntity` target.

    The profile only commands what a pilot/autopilot commands -- throttle,
    pitch rate, bank rate. It never touches position or velocity: the
    deceleration, near-zero-airspeed hang, and fall come out of the force
    balance in `attitude_net_acceleration` (thrust along the body, aero
    collapsing with q, gravity unchanged).

    Phases: armed -> throttle_cut -> pitch_up -> hang -> spiral -> recovered.
    `hang` is telemetry only (airspeed < `hang_speed_m_s`) and may be skipped
    if the vehicle starts falling before bleeding that far. `recovered` hands
    the entity back to plain point-mass flight.

    Trigger mirrors `BreakTurn`: `trigger_time_to_go_s` against engagement
    geometry, else absolute `trigger_time_s`. `lateral_accel` always returns
    zeros; the commands are written onto `entity` (the engine then calls its
    polymorphic `step`).
    """

    PHASES = ("armed", "throttle_cut", "pitch_up", "hang", "spiral", "recovered")
    _GAIN = 10.0  # 1/s, proportional attitude-hold gain (saturates at max rate)

    def __init__(
        self,
        entity: AttitudeAugmentedEntity,
        trigger_time_to_go_s: Optional[float] = None,
        trigger_time_s: float = 0.0,
        pitch_target_deg: float = 88.0,
        idle_throttle: float = 0.02,
        hang_speed_m_s: float = 40.0,
        spiral_bank_deg: float = 60.0,
        spiral_alpha_deg: float = 10.0,
        spiral_throttle: float = 0.5,
        recovery_q_pa: float = 3_000.0,
        recovery_altitude_loss_m: float = 100.0,
    ):
        if not isinstance(entity, AttitudeAugmentedEntity):
            raise TypeError("CobraManeuver needs an AttitudeAugmentedEntity")
        self.entity = entity
        self.trigger_time_to_go_s = trigger_time_to_go_s
        self.trigger_time_s = float(trigger_time_s)
        self.pitch_target = float(np.deg2rad(pitch_target_deg))
        self.idle_throttle = float(idle_throttle)
        self.hang_speed_m_s = float(hang_speed_m_s)
        self.spiral_bank = float(np.deg2rad(spiral_bank_deg))
        self.spiral_alpha = float(np.deg2rad(spiral_alpha_deg))
        self.spiral_throttle = float(spiral_throttle)
        self.recovery_q_pa = float(recovery_q_pa)
        self.recovery_altitude_loss_m = float(recovery_altitude_loss_m)
        self.phase = "armed"
        self.phase_history: list[tuple[float, str]] = [(0.0, "armed")]
        self._time_to_go_s: Optional[float] = None
        self._spiral_start_altitude_m = 0.0

    def update_engagement(self, t: float, target_state: State, pursuer_state: Optional[State]) -> None:
        self._time_to_go_s = None if pursuer_state is None else _time_to_go(target_state, pursuer_state)

    def _enter(self, t: float, phase: str) -> None:
        self.phase = phase
        self.phase_history.append((t, phase))

    def lateral_accel(self, t: float, state: State) -> np.ndarray:
        e = self.entity
        if self.phase == "armed":
            if self.trigger_time_to_go_s is not None and self._time_to_go_s is not None:
                triggered = self._time_to_go_s <= self.trigger_time_to_go_s
            else:
                triggered = t >= self.trigger_time_s
            if triggered:
                e.sync_attitude_to_velocity()
                e.attitude_active = True
                e.throttle = self.idle_throttle
                e.theta_dot = e.phi_dot = 0.0
                self._enter(t, "throttle_cut")
            return np.zeros(3)

        if self.phase == "throttle_cut":  # one control tick at idle, then pull
            self._enter(t, "pitch_up")

        if self.phase in ("pitch_up", "hang"):
            e.theta_dot = self._GAIN * (self.pitch_target - e.theta)
            if self.phase == "pitch_up" and state.speed() < self.hang_speed_m_s:
                self._enter(t, "hang")
            pitch_done = e.theta >= self.pitch_target - np.deg2rad(2.0)
            if pitch_done and state.velocity[2] < 0.0:
                self._spiral_start_altitude_m = state.altitude()
                self._enter(t, "spiral")

        if self.phase == "spiral":
            e.throttle = self.spiral_throttle
            e.phi_dot = self._GAIN * (self.spiral_bank - e.phi)
            # Nose follows velocity with a small alpha, so the banked lift
            # (not a scripted path) winds the descent into a spiral.
            gamma = flight_path_angle(state.velocity, e.psi)
            e.theta_dot = self._GAIN * (gamma + self.spiral_alpha - e.theta)
            q = dynamic_pressure(isa_density(state.altitude()), state.speed())
            lost = self._spiral_start_altitude_m - state.altitude()
            if q >= self.recovery_q_pa and lost >= self.recovery_altitude_loss_m:
                e.attitude_active = False
                e.throttle = e.theta_dot = e.phi_dot = 0.0
                self._enter(t, "recovered")

        return np.zeros(3)
