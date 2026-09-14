"""FastAPI entry point for the trajectory visualization scaffold."""

from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from guidance_sim.api import live_guidance
from guidance_sim.api.catalog import get_catalog
from guidance_sim.api.live_stream import build_live_trajectory, build_rl_trials
from guidance_sim.api.schemas import (
    CatalogResponse,
    GuidanceFrame,
    GuidanceSessionStartRequest,
    GuidanceStepRequest,
    StreamCompleted,
    StreamError,
    StreamStartRequest,
    StreamStarted,
    TrialsRequest,
)

app = FastAPI(
    title="Guidance Simulation Visualization API",
    version="0.1.0",
    description=(
        "Streams a freshly simulated engagement per request over the "
        "trajectory WebSocket schema: the selected scenario drives the "
        "target's maneuver, the selected guidance law drives the "
        "interceptor, live speed overrides reshape the initial conditions, "
        "and each run draws a new random seed."
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
        "trajectory_source": "live_simulation",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "trajectory_source": "live_simulation"}


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


REPO_ROOT = Path(__file__).resolve().parents[3]


def load_training_log(pointer_path: Path = REPO_ROOT / "outputs" / "CURRENT_RL_BASELINE.json") -> dict[str, object]:
    """Episode log + fixed-eval results of the lineage behind the frozen baseline."""

    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    run_dir = pointer_path.parent.parent / Path(pointer["progress_path"]).parent
    with (run_dir / "training_episodes.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    episodes = [
        {
            "episode": index,
            "checkpoint": int(row["checkpoint"]),
            "timesteps": int(row["total_timesteps"]),
            "reward": float(row["episode_reward"]),
            "success": row["outcome"] == "hit",
            "outcome": row["outcome"],
            "miss_m": float(row["min_range_m"]),
        }
        for index, row in enumerate(rows, start=1)
    ]
    checkpoints = []
    for eval_path in sorted(run_dir.glob("rl_checkpoint_*_eval.json")):
        summary = json.loads(eval_path.read_text(encoding="utf-8"))
        metadata = json.loads(
            eval_path.with_name(eval_path.name.replace("_eval", "")).read_text(encoding="utf-8")
        )
        checkpoints.append(
            {
                "checkpoint": int(metadata["checkpoint_index"]),
                "timesteps": int(metadata["cumulative_timesteps"]),
                "hits": int(summary["n_hits"]),
                "cases": int(summary["n_cases"]),
                "median_miss_m": float(summary["median_miss_distance_m"]),
                "mean_reward": float(summary["mean_episode_reward"]),
            }
        )
    return {
        "source": "training-run",
        "branch_name": pointer.get("branch_name", ""),
        "model_path": pointer["model_path"],
        "episodes": episodes,
        "checkpoints": checkpoints,
    }


@app.get("/api/training")
def training_log() -> dict[str, object]:
    return load_training_log()


@app.post("/api/trials")
def rl_trials(request: TrialsRequest) -> dict[str, object]:
    """Frozen-RL-policy Monte Carlo episodes around the current setup."""

    try:
        trials = build_rl_trials(
            request.scenario_id, request.parameter_overrides, request.count
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"schema_version": "1.0", "source": "rl-rollouts", "trials": trials}


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
            trajectory = build_live_trajectory(
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
