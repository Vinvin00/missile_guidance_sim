"""FastAPI entry point for the trajectory visualization scaffold."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from guidance_sim.api import live_guidance
from guidance_sim.api.catalog import get_catalog
from guidance_sim.api.rollout_stream import build_rollout_trajectory
from guidance_sim.api.schemas import (
    CatalogResponse,
    GuidanceFrame,
    GuidanceSessionStartRequest,
    GuidanceStepRequest,
    StreamCompleted,
    StreamError,
    StreamStartRequest,
    StreamStarted,
)

app = FastAPI(
    title="Guidance Simulation Visualization API",
    version="0.1.0",
    description=(
        "Streams captured RL baseline evaluation rollouts over the frozen "
        "trajectory WebSocket schema. Offline capture only — no live "
        "checkpoint evaluation in the request path."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": "guidance-sim-visualization",
        "docs": "/docs",
        "trajectory_source": "rl_rollout",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "trajectory_source": "rl_rollout"}


@app.get("/api/catalog", response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return get_catalog()


@app.post("/api/guidance/session", response_model=GuidanceFrame)
def start_guidance_session(request: GuidanceSessionStartRequest) -> dict[str, object]:
    """Start a live RL-policy-in-the-loop session and return its initial frame.

    Additive to the existing captured-rollout ``/ws/trajectory`` stream: this
    runs the frozen checkpoint live, one step at a time, instead of replaying
    a pre-captured episode.
    """

    try:
        return live_guidance.start_session(
            case_name=request.case_name,
            pursuer_position_m=(
                tuple(
                    getattr(request.pursuer.position_m, axis) for axis in "xyz"
                )
                if request.pursuer is not None
                else None
            ),
            pursuer_velocity_m_s=(
                tuple(
                    getattr(request.pursuer.velocity_m_s, axis) for axis in "xyz"
                )
                if request.pursuer is not None
                else None
            ),
            target_position_m=(
                tuple(getattr(request.target.position_m, axis) for axis in "xyz")
                if request.target is not None
                else None
            ),
            target_velocity_m_s=(
                tuple(getattr(request.target.velocity_m_s, axis) for axis in "xyz")
                if request.target is not None
                else None
            ),
            maneuver_kind=request.target_maneuver.kind,
            maneuver_accel_g=request.target_maneuver.accel_g,
            maneuver_frequency_hz=request.target_maneuver.frequency_hz,
            maneuver_phase_rad=request.target_maneuver.phase_rad,
            seed=request.seed,
        )
    except live_guidance.LiveGuidanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/guidance/step", response_model=GuidanceFrame)
def step_guidance_session(request: GuidanceStepRequest) -> dict[str, object]:
    """Advance one live session by one policy step and one physics step."""

    try:
        return live_guidance.step_session(request.session_id)
    except live_guidance.SessionNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail=f"unknown or expired session: {exc}"
        ) from exc
    except live_guidance.LiveGuidanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.websocket("/ws/trajectory")
async def trajectory_stream(websocket: WebSocket) -> None:
    """Receive one ``stream.start`` request and emit ordered trajectory frames."""

    await websocket.accept()
    try:
        raw_request = await websocket.receive_text()
        try:
            request = StreamStartRequest.model_validate_json(raw_request)
        except ValidationError as exc:
            error = StreamError(
                code="invalid_request",
                detail=exc.errors(include_url=False)[0]["msg"],
            )
            await websocket.send_json(error.model_dump(mode="json"))
            await websocket.close(code=1008)
            return

        stream_id = str(uuid4())
        try:
            trajectory = build_rollout_trajectory(
                request.scenario_id,
                request.guidance_law,
                stream_id,
                request.parameter_overrides,
            )
        except ValueError as exc:
            error = StreamError(
                code="invalid_parameter_override",
                detail=str(exc),
            )
            await websocket.send_json(error.model_dump(mode="json"))
            await websocket.close(code=1008)
            return
        except FileNotFoundError as exc:
            error = StreamError(
                code="rollout_unavailable",
                detail=str(exc),
            )
            await websocket.send_json(error.model_dump(mode="json"))
            await websocket.close(code=1011)
            return
        started = StreamStarted(
            stream_id=stream_id,
            scenario_id=request.scenario_id,
            guidance_law=request.guidance_law,
            frame_count=len(trajectory.frames),
            dt_s=trajectory.dt_s,
            data_source="rollout",
            applied_parameters=trajectory.applied_parameters,
        )
        await websocket.send_json(started.model_dump(mode="json"))

        interval_s = request.frame_interval_ms / 1000.0
        for frame in trajectory.frames:
            await websocket.send_json(frame.model_dump(mode="json"))
            await asyncio.sleep(interval_s if interval_s else 0)

        completed = StreamCompleted(
            stream_id=stream_id,
            outcome=(
                "intercept" if trajectory.closest_approach_m <= 5.0 else "miss"
            ),
            closest_approach_m=trajectory.closest_approach_m,
            frame_count=len(trajectory.frames),
            data_source="rollout",
        )
        await websocket.send_json(completed.model_dump(mode="json"))
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
