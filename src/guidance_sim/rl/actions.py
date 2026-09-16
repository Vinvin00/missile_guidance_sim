"""Velocity-normal action mapping used only by the RL environment wrapper.

``GuidanceLaw.compute_command`` remains a world-frame ``(3,)`` vector.
``PointMassEntity.step`` / ``clamp_lateral_command`` remain the authority
that projects any 3D command onto the plane perpendicular to velocity.
Restricting the policy to that plane is done here so the along-track
null space is removed structurally for training, without touching frozen
guidance or dynamics code.

``world3`` preserves the Phase-1/2 three-component world-frame action so
archived checkpoints can be replayed.  ``lateral2`` is the training layout:
the two action components are coefficients on an orthonormal basis of the
velocity-normal plane.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

ACTION_LAYOUT_LATERAL2 = "lateral2"
ACTION_LAYOUT_WORLD3 = "world3"
ActionLayout = Literal["lateral2", "world3"]

_SPEED_EPS = 1e-6
_BASIS_EPS = 1e-9
_UP = np.array([0.0, 0.0, 1.0])


def action_dimension(layout: ActionLayout) -> int:
    if layout == ACTION_LAYOUT_LATERAL2:
        return 2
    if layout == ACTION_LAYOUT_WORLD3:
        return 3
    raise ValueError(f"unsupported action layout: {layout}")


def lateral_basis(velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return two unit vectors spanning the plane perpendicular to ``velocity``.

    ``e1`` is the horizontal-ish turn direction (world-up × velocity).  ``e2``
    completes a right-handed triad with the velocity unit vector.  A still
    vehicle gets a fixed world ``y``/``z`` pair so the mapping stays defined.
    """

    velocity = np.asarray(velocity, dtype=float).reshape(3)
    speed = float(np.linalg.norm(velocity))
    if speed < _SPEED_EPS:
        return np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])

    v_hat = velocity / speed
    raw = np.cross(_UP, v_hat)
    norm = float(np.linalg.norm(raw))
    if norm < _BASIS_EPS:
        fallback = (
            np.array([1.0, 0.0, 0.0])
            if abs(v_hat[0]) < 0.9
            else np.array([0.0, 1.0, 0.0])
        )
        raw = np.cross(fallback, v_hat)
        norm = float(np.linalg.norm(raw))
    e1 = raw / norm
    e2 = np.cross(v_hat, e1)
    e2_norm = float(np.linalg.norm(e2))
    if e2_norm < _BASIS_EPS:
        return e1, np.zeros(3)
    return e1, e2 / e2_norm


def lateral_basis_from_previous(
    velocity: np.ndarray, previous_e1: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray]:
    """Continuous variant of ``lateral_basis`` for sequential control steps.

    ``lateral_basis`` recomputes ``e1`` from ``up x v_hat`` every call, which
    is discontinuous near the poles (``v_hat`` parallel to world-up): as the
    fallback branch flips, a constant action maps to a world command that
    whips 90-180 degrees between steps (see docs/rl-interface-6dof.md,
    "action-basis singularity"). This instead projects the previous step's
    ``e1`` onto the new velocity-normal plane and re-normalises, which keeps
    the frame continuous through the pole. Falls back to ``lateral_basis``
    when there is no previous frame (episode reset) or it has degenerated
    (previous ``e1`` now anti-/parallel to the new velocity).
    """

    velocity = np.asarray(velocity, dtype=float).reshape(3)
    speed = float(np.linalg.norm(velocity))
    if speed < _SPEED_EPS:
        return np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])
    v_hat = velocity / speed

    if previous_e1 is not None:
        projected = previous_e1 - np.dot(previous_e1, v_hat) * v_hat
        norm = float(np.linalg.norm(projected))
        if norm >= _BASIS_EPS:
            e1 = projected / norm
            e2 = np.cross(v_hat, e1)
            return e1, e2 / float(np.linalg.norm(e2))

    return lateral_basis(velocity)


def lateral_to_world(action_2d: np.ndarray, velocity: np.ndarray) -> np.ndarray:
    """Map a 2D lateral action onto the velocity-normal plane in world axes."""

    coefficients = np.asarray(action_2d, dtype=float).reshape(2)
    e1, e2 = lateral_basis(velocity)
    return coefficients[0] * e1 + coefficients[1] * e2


def world_to_lateral(world_3d: np.ndarray, velocity: np.ndarray) -> np.ndarray:
    """Project a world-frame command onto the 2D lateral basis."""

    world = np.asarray(world_3d, dtype=float).reshape(3)
    e1, e2 = lateral_basis(velocity)
    return np.array([float(np.dot(world, e1)), float(np.dot(world, e2))])
