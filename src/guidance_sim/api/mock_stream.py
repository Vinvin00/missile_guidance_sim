"""Deterministic synthetic trajectories for the visualization scaffold.

These paths exercise the streaming and playback contracts only.  They are
explicitly marked synthetic and do not evaluate any guidance implementation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from guidance_sim.api.catalog import get_catalog, resolve_live_parameters
from guidance_sim.api.schemas import (
    BodyState,
    GuidanceLawId,
    ScenarioId,
    TrajectoryFrame,
    Vector3,
)

_DT_S = 0.1
_INTERCEPTOR_SPEED_KEY = "interceptor.speed"
_TARGET_SPEED_KEY = "target.speed"


@dataclass(frozen=True)
class MockGeometry:
    target_heading_deg: float
    lateral_offset_m: float
    interceptor_altitude_offset_m: float
    target_climb_rate_m_s: float = 0.0
    weave_amplitude_m: float = 0.0
    weave_frequency_hz: float = 0.0


@dataclass(frozen=True)
class MockTrajectory:
    dt_s: float
    frames: list[TrajectoryFrame]
    closest_approach_m: float
    applied_parameters: dict[str, float]


_GEOMETRIES: dict[ScenarioId, MockGeometry] = {
    "crossing-intercept": MockGeometry(
        target_heading_deg=-82.0,
        lateral_offset_m=1_100.0,
        interceptor_altitude_offset_m=-180.0,
    ),
    "head-on-intercept": MockGeometry(
        target_heading_deg=180.0,
        lateral_offset_m=300.0,
        interceptor_altitude_offset_m=-80.0,
    ),
    "evasive-climb": MockGeometry(
        target_heading_deg=164.0,
        lateral_offset_m=900.0,
        interceptor_altitude_offset_m=-260.0,
        target_climb_rate_m_s=18.0,
        weave_amplitude_m=80.0,
        weave_frequency_hz=0.08,
    ),
}

_GUIDANCE_CURVE_M: dict[GuidanceLawId, tuple[float, float]] = {
    "pn": (420.0, 115.0),
    "apn": (260.0, 70.0),
    "ogl": (150.0, 40.0),
}

_GUIDANCE_RESIDUAL_M: dict[GuidanceLawId, float] = {
    "pn": 3.2,
    "apn": 2.1,
    "ogl": 1.4,
}


def _vector3(values: np.ndarray) -> Vector3:
    return Vector3(x=float(values[0]), y=float(values[1]), z=float(values[2]))


def _body_state(position: np.ndarray, velocity: np.ndarray) -> BodyState:
    return BodyState(
        position_m=_vector3(position),
        velocity_m_s=_vector3(velocity),
    )


def build_mock_trajectory(
    scenario_id: ScenarioId,
    guidance_law: GuidanceLawId,
    stream_id: str,
    parameter_overrides: dict[str, float] | None = None,
) -> MockTrajectory:
    """Build one repeatable z-up trajectory for the selected preview."""

    default_parameters = resolve_live_parameters({})
    applied_parameters = resolve_live_parameters(parameter_overrides or {})
    interceptor_speed_m_s = applied_parameters[_INTERCEPTOR_SPEED_KEY]
    target_speed_m_s = applied_parameters[_TARGET_SPEED_KEY]

    scenario = next(
        item for item in get_catalog().scenarios if item.id == scenario_id
    )
    geometry = _GEOMETRIES[scenario_id]
    reference_closing_scale = (
        default_parameters[_INTERCEPTOR_SPEED_KEY]
        + 0.35 * default_parameters[_TARGET_SPEED_KEY]
    )
    selected_closing_scale = interceptor_speed_m_s + 0.35 * target_speed_m_s
    duration_s = scenario.duration_s * np.clip(
        reference_closing_scale / selected_closing_scale,
        0.65,
        1.4,
    )
    frame_count = int(round(duration_s / _DT_S)) + 1
    times = np.linspace(0.0, duration_s, frame_count)
    u = times / duration_s

    horizontal_range = np.sqrt(
        scenario.initial_range_m**2 - geometry.lateral_offset_m**2
    )
    pursuer_start = np.array(
        [
            0.0,
            0.0,
            scenario.altitude_m + geometry.interceptor_altitude_offset_m,
        ]
    )
    target_start = np.array(
        [horizontal_range, geometry.lateral_offset_m, scenario.altitude_m]
    )

    heading_rad = np.deg2rad(geometry.target_heading_deg)
    target_velocity = np.array(
        [
            target_speed_m_s * np.cos(heading_rad),
            target_speed_m_s * np.sin(heading_rad),
            geometry.target_climb_rate_m_s,
        ]
    )
    target_positions = target_start + times[:, None] * target_velocity

    if geometry.weave_amplitude_m:
        phase = 2.0 * np.pi * geometry.weave_frequency_hz * times
        target_positions[:, 1] += geometry.weave_amplitude_m * np.sin(phase)
        target_positions[:, 2] += (
            0.45 * geometry.weave_amplitude_m * np.sin(phase + np.pi / 3.0)
            - 0.45 * geometry.weave_amplitude_m * np.sin(np.pi / 3.0)
        )

    curve_scale = default_parameters[_INTERCEPTOR_SPEED_KEY] / interceptor_speed_m_s
    lateral_curve_m, vertical_curve_m = (
        component * curve_scale
        for component in _GUIDANCE_CURVE_M[guidance_law]
    )
    lead_arc = np.sin(np.pi * u)
    lead_direction = np.column_stack(
        (
            np.zeros(frame_count),
            lateral_curve_m * lead_arc,
            vertical_curve_m * lead_arc,
        )
    )
    catch_fraction = u * u * (3.0 - 2.0 * u)
    pursuer_positions = (
        pursuer_start
        + catch_fraction[:, None] * (target_positions - pursuer_start)
        + lead_direction
    )

    residual = _GUIDANCE_RESIDUAL_M[guidance_law]
    pursuer_positions[:, 1] += residual * u**4

    pursuer_velocities = np.gradient(pursuer_positions, times, axis=0)
    target_velocities = np.gradient(target_positions, times, axis=0)
    ranges = np.linalg.norm(target_positions - pursuer_positions, axis=1)

    # Match the grounded catalog's initial-speed values exactly. Subsequent
    # samples are finite differences of the deliberately geometric preview.
    initial_los = target_start - pursuer_start
    pursuer_velocities[0] = (
        initial_los / np.linalg.norm(initial_los) * interceptor_speed_m_s
    )
    target_velocities[0] *= target_speed_m_s / np.linalg.norm(
        target_velocities[0]
    )

    frames = [
        TrajectoryFrame(
            stream_id=stream_id,
            sequence=index,
            time_s=float(time_s),
            pursuer=_body_state(pursuer_positions[index], pursuer_velocities[index]),
            target=_body_state(target_positions[index], target_velocities[index]),
            range_m=float(ranges[index]),
        )
        for index, time_s in enumerate(times)
    ]
    return MockTrajectory(
        dt_s=_DT_S,
        frames=frames,
        closest_approach_m=float(np.min(ranges)),
        applied_parameters=applied_parameters,
    )
