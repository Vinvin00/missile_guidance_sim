"""Serving-time inference wrapper for the frozen RL baseline policy.

This is the *serving* counterpart to the training-time PPO wrapper in
``guidance_sim.rl.training``. It intentionally does not import that module
(or anything else training-specific): it only loads a frozen checkpoint via
``sb3_contrib.RecurrentPPO.load`` and exposes a minimal ``predict`` surface,
so serving code never creates a dependency back onto training internals.

Scenario/physics stepping is reused as-is from ``guidance_sim.rl.environment``
and ``guidance_sim.rl.actions`` (frozen interfaces), and vehicle defaults from
``guidance_sim.physics.entities`` -- none of that is modified here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sb3_contrib import RecurrentPPO

from guidance_sim.rl.actions import ActionLayout

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASELINE_POINTER = REPO_ROOT / "outputs" / "CURRENT_RL_BASELINE.json"


@dataclass(frozen=True)
class FrozenPolicyBaseline:
    """Resolved pointer contents from ``CURRENT_RL_BASELINE.json``."""

    pointer_path: Path
    model_path: Path
    action_layout: ActionLayout
    use_target_turn_rate_obs: bool
    tracking_enabled: bool
    max_time_s: float
    observation_dim: int
    branch_name: str
    cumulative_timesteps: int


def load_baseline_pointer(
    pointer_path: Path | str = DEFAULT_BASELINE_POINTER,
) -> FrozenPolicyBaseline:
    """Resolve the current frozen baseline checkpoint from its JSON pointer."""

    pointer_path = Path(pointer_path)
    payload = json.loads(pointer_path.read_text(encoding="utf-8"))
    # model_path in the pointer is repo-root-relative (matches the convention
    # already used by scripts/capture_rl_rollout.py).
    repo_root = pointer_path.parent.parent
    model_path = (repo_root / str(payload["model_path"])).resolve()
    if not model_path.is_file():
        raise FileNotFoundError(f"checkpoint not found: {model_path}")
    return FrozenPolicyBaseline(
        pointer_path=pointer_path.resolve(),
        model_path=model_path,
        action_layout=str(payload.get("action_layout", "lateral2")),  # type: ignore[arg-type]
        use_target_turn_rate_obs=bool(payload["use_target_turn_rate_obs"]),
        # Absent on pre-tracking baseline pointers (frozen CP1-CP5 lineage);
        # default False preserves their 10/13-D contract unchanged.
        tracking_enabled=bool(payload.get("tracking_enabled", False)),
        # Absent on baseline pointers predating the evasive lineage; default
        # 25.0 matches PPOTrainingConfig's own default (the frozen lineage's
        # episode budget), so old pointers keep their existing behavior.
        max_time_s=float(payload.get("max_time_s", 25.0)),
        observation_dim=int(payload["observation_dim"]),
        branch_name=str(payload.get("branch_name", "")),
        cumulative_timesteps=int(payload.get("cumulative_timesteps", 0)),
    )


class FrozenPolicy:
    """Loads one frozen checkpoint once and serves deterministic predictions.

    Weights are loaded a single time; recurrent (LSTM) hidden state is passed
    in and out explicitly by the caller so one loaded policy can back many
    concurrent live-inference sessions without cross-talk.
    """

    def __init__(self, baseline: FrozenPolicyBaseline | None = None) -> None:
        self.baseline = baseline or load_baseline_pointer()
        self._model = RecurrentPPO.load(str(self.baseline.model_path), device="cpu")

    def predict(
        self,
        observation: np.ndarray,
        *,
        recurrent_state: Any,
        episode_start: np.ndarray,
        deterministic: bool = True,
    ) -> tuple[np.ndarray, Any]:
        """Return ``(action, next_recurrent_state)`` for one policy step."""

        action, next_state = self._model.predict(
            observation,
            state=recurrent_state,
            episode_start=episode_start,
            deterministic=deterministic,
        )
        return action, next_state


_shared_policy: FrozenPolicy | None = None


def get_shared_policy() -> FrozenPolicy:
    """Process-wide singleton so the checkpoint is loaded from disk once."""

    global _shared_policy
    if _shared_policy is None:
        _shared_policy = FrozenPolicy()
    return _shared_policy
