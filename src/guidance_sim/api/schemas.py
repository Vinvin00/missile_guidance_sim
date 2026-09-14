"""Pydantic contracts for the visualization API and WebSocket stream."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScenarioId = Literal[
    "crossing-intercept",
    "head-on-intercept",
    "evasive-climb",
    "g-limited-turn",
]
GuidanceLawId = Literal["pn", "apn", "ogl", "rl"]
DataSource = Literal["synthetic", "rollout"]


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
    live_control: bool = False
    control_step: float | None = None


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
    # Live-control values the viewer applies when this scenario is picked.
    parameter_defaults: dict[str, float] = Field(default_factory=dict)
    # Interceptor structural g-limit override; None = vehicle profile default.
    pursuer_g_limit: float | None = None


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
    # Initial geometry / target behaviour controls, keyed ``engagement.<name>``.
    engagement_parameters: dict[str, ParameterValue] = Field(default_factory=dict)


class StreamStartRequest(StrictModel):
    type: Literal["stream.start"] = "stream.start"
    scenario_id: ScenarioId
    guidance_law: GuidanceLawId
    frame_interval_ms: int = Field(default=8, ge=0, le=250)
    parameter_overrides: dict[str, float] = Field(default_factory=dict)


class TrialsRequest(StrictModel):
    scenario_id: ScenarioId
    count: int = Field(default=30, ge=1, le=50)
    parameter_overrides: dict[str, float] = Field(default_factory=dict)


class StreamStarted(StrictModel):
    type: Literal["stream.started"] = "stream.started"
    protocol_version: Literal["1.0"] = "1.0"
    stream_id: str
    scenario_id: ScenarioId
    guidance_law: GuidanceLawId
    frame_count: int
    dt_s: float
    data_source: DataSource = "synthetic"
    applied_parameters: dict[str, float]


class TrajectoryFrame(StrictModel):
    type: Literal["trajectory.frame"] = "trajectory.frame"
    stream_id: str
    sequence: int
    time_s: float
    pursuer: BodyState
    target: BodyState
    range_m: float
    # Lateral accel in world frame (m/s^2). Mock stream populates these so the
    # RL-relevant commanded/achieved pair is in the contract before checkpoint
    # eval wiring; real adapter should match SimulationResult field semantics.
    pursuer_accel_cmd_m_s2: Vector3
    pursuer_accel_achieved_m_s2: Vector3


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


GuidanceManeuverKind = Literal["none", "constant_turn", "weave"]
GuidanceOutcome = Literal["ongoing", "hit", "miss", "timeout"]


class GuidanceManeuverSpec(StrictModel):
    """Target maneuver for a custom (non-``case_name``) live session."""

    kind: GuidanceManeuverKind = "none"
    accel_g: float = 0.0
    frequency_hz: float = 0.0
    phase_rad: float = 0.0


class GuidanceSessionStartRequest(StrictModel):
    """Start a live-inference session.

    Either ``case_name`` (one of the frozen fixed evaluation cases) or a full
    explicit ``pursuer``/``target`` initial state must be given, not both.
    """

    case_name: str | None = None
    pursuer: BodyState | None = None
    target: BodyState | None = None
    target_maneuver: GuidanceManeuverSpec = Field(default_factory=GuidanceManeuverSpec)
    seed: int = 91_000


class GuidanceStepRequest(StrictModel):
    session_id: str


class GuidanceFrame(StrictModel):
    """One live step of policy-in-the-loop inference.

    Field names mirror ``TrajectoryFrame`` deliberately -- this is the same
    physical content, computed live via the frozen RL policy and the
    existing ``InterceptionEnv`` stepping code instead of replayed from a
    captured rollout file.
    """

    session_id: str
    sequence: int
    time_s: float
    pursuer: BodyState
    target: BodyState
    range_m: float
    pursuer_accel_cmd_m_s2: Vector3
    pursuer_accel_achieved_m_s2: Vector3
    terminated: bool
    outcome: GuidanceOutcome
    hit: bool
