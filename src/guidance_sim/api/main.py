"""FastAPI entry point for the trajectory visualization scaffold."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from guidance_sim.api.catalog import get_catalog
from guidance_sim.api.mock_stream import build_mock_trajectory
from guidance_sim.api.schemas import (
    CatalogResponse,
    StreamCompleted,
    StreamError,
    StreamStartRequest,
    StreamStarted,
)

app = FastAPI(
    title="Guidance Simulation Visualization API",
    version="0.1.0",
    description=(
        "Streams synthetic 3D trajectory previews. Checkpoint evaluation is "
        "intentionally deferred until its format is stable."
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
        "trajectory_source": "synthetic",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "trajectory_source": "synthetic"}


@app.get("/api/catalog", response_model=CatalogResponse)
def catalog() -> CatalogResponse:
    return get_catalog()


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
        trajectory = build_mock_trajectory(
            request.scenario_id,
            request.guidance_law,
            stream_id,
        )
        started = StreamStarted(
            stream_id=stream_id,
            scenario_id=request.scenario_id,
            guidance_law=request.guidance_law,
            frame_count=len(trajectory.frames),
            dt_s=trajectory.dt_s,
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
        )
        await websocket.send_json(completed.model_dump(mode="json"))
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        return
