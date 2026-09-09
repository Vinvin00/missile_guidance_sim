"""Pydantic contracts for the visualization API and WebSocket stream."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScenarioId = Literal[
    "crossing-intercept",
    "head-on-intercept",
    "evasive-climb",
]
GuidanceLawId = Literal["pn", "apn", "ogl"]
DataSource = Literal["synthetic"]


class StrictModel(BaseModel):
    """Reject misspelled fields at the API boundary."""

    model_config = ConfigDict(extra="forbid")


class Vector3(StrictModel):
    x: float
    y: float
    z: float


class BodyState(StrictModel):
    position_m: Vector3
    velocity_m_s: Vector3


class ParameterValue(StrictModel):
    value: float
    unit: str
    reference_min: float
    reference_max: float
    basis: Literal["direct", "synthesized", "illustrative"]
    source_ids: list[str]


class VehicleProfile(StrictModel):
    name: str
    role: Literal["interceptor", "target"]
    parameters: dict[str, ParameterValue]


class ScenarioOption(StrictModel):
    id: ScenarioId
    label: str
    description: str
    initial_range_m: float
    altitude_m: float
    duration_s: float


class GuidanceOption(StrictModel):
    id: GuidanceLawId
    label: str
    description: str


class CatalogResponse(StrictModel):
    protocol_version: Literal["1.0"] = "1.0"
    data_source: DataSource = "synthetic"
    scenarios: list[ScenarioOption]
    guidance_laws: list[GuidanceOption]
    vehicle_profiles: list[VehicleProfile]


class StreamStartRequest(StrictModel):
    type: Literal["stream.start"] = "stream.start"
    scenario_id: ScenarioId
    guidance_law: GuidanceLawId
    frame_interval_ms: int = Field(default=8, ge=0, le=250)


class StreamStarted(StrictModel):
    type: Literal["stream.started"] = "stream.started"
    protocol_version: Literal["1.0"] = "1.0"
    stream_id: str
    scenario_id: ScenarioId
    guidance_law: GuidanceLawId
    frame_count: int
    dt_s: float
    data_source: DataSource = "synthetic"


class TrajectoryFrame(StrictModel):
    type: Literal["trajectory.frame"] = "trajectory.frame"
    stream_id: str
    sequence: int
    time_s: float
    pursuer: BodyState
    target: BodyState
    range_m: float


class StreamCompleted(StrictModel):
    type: Literal["stream.completed"] = "stream.completed"
    stream_id: str
    outcome: Literal["intercept", "miss"]
    closest_approach_m: float
    frame_count: int
    data_source: DataSource = "synthetic"


class StreamError(StrictModel):
    type: Literal["stream.error"] = "stream.error"
    code: str
    detail: str
