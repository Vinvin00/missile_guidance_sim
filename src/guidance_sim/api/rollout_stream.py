"""Load captured RL evaluation rollouts for the visualization WebSocket.

Replaces the synthetic mock generator as the ``/ws/trajectory`` data source.
Rollout JSON is produced offline by ``scripts/capture_rl_rollout.py`` against
the frozen CURRENT_RL_BASELINE checkpoint; this module only reads and maps
frames into the existing TrajectoryFrame schema.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from guidance_sim.api.catalog import resolve_live_parameters
from guidance_sim.api.schemas import (
    BodyState,
    GuidanceLawId,
    ScenarioId,
    TrajectoryFrame,
    Vector3,
)

_ROLLOUT_DIR = Path(__file__).resolve().parents[3] / "outputs" / "rl_rollouts"

# Catalog scenario id → captured Group A hit rollout.
# ConstantTurn has no confirmed baseline hit; reuse NoManeuver demo.
_SCENARIO_ROLLOUT: dict[ScenarioId, str] = {
    "crossing-intercept": "no_maneuver_demo",
    "head-on-intercept": "no_maneuver_demo",
    "evasive-climb": "weave_5g_070hz",
    "g-limited-turn": "no_maneuver_demo",
}


@dataclass(frozen=True)
class RolloutTrajectory:
    dt_s: float
    frames: list[TrajectoryFrame]
    closest_approach_m: float
    applied_parameters: dict[str, float]
    case_name: str
    outcome: str


def _vector3(payload: dict[str, float]) -> Vector3:
    return Vector3(x=float(payload["x"]), y=float(payload["y"]), z=float(payload["z"]))


def _body_state(payload: dict[str, dict[str, float]]) -> BodyState:
    return BodyState(
        position_m=_vector3(payload["position_m"]),
        velocity_m_s=_vector3(payload["velocity_m_s"]),
    )


@lru_cache(maxsize=8)
def _load_rollout_payload(case_name: str) -> dict:
    path = _ROLLOUT_DIR / f"{case_name}.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"missing RL rollout artifact: {path}. "
            "Run scripts/capture_rl_rollout.py --case "
            f"{case_name} from the training worktree."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def build_rollout_trajectory(
    scenario_id: ScenarioId,
    guidance_law: GuidanceLawId,
    stream_id: str,
    parameter_overrides: dict[str, float] | None = None,
) -> RolloutTrajectory:
    """Map a catalog selection onto a captured RL evaluation episode.

    ``guidance_law`` is accepted for protocol compatibility but ignored: the
    frames come from the RL baseline policy, not classical PN/APN/OGL.
    Live speed overrides are validated and echoed in ``applied_parameters``
    but do not reshape the frozen rollout.
    """

    del guidance_law  # Protocol field only; rollout is RL-policy truth.
    applied_parameters = resolve_live_parameters(parameter_overrides or {})
    case_name = _SCENARIO_ROLLOUT[scenario_id]
    payload = _load_rollout_payload(case_name)

    frames = [
        TrajectoryFrame(
            stream_id=stream_id,
            sequence=index,
            time_s=float(raw["time_s"]),
            pursuer=_body_state(raw["pursuer"]),
            target=_body_state(raw["target"]),
            range_m=float(raw["range_m"]),
            pursuer_accel_cmd_m_s2=_vector3(raw["pursuer_accel_cmd_m_s2"]),
            pursuer_accel_achieved_m_s2=_vector3(
                raw["pursuer_accel_achieved_m_s2"]
            ),
        )
        for index, raw in enumerate(payload["frames"])
    ]
    return RolloutTrajectory(
        dt_s=float(payload["dt_s"]),
        frames=frames,
        closest_approach_m=float(payload["closest_approach_m"]),
        applied_parameters=applied_parameters,
        case_name=str(payload["case_name"]),
        outcome=str(payload["outcome"]),
    )
