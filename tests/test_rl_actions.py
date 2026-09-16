"""lateral_basis's up x v_hat formula is discontinuous near vertical flight
(docs/rl-interface-6dof.md, "action-basis singularity"): a constant action
maps to a world command that whips 90-180 degrees between steps as the
velocity crosses the pole. lateral_basis_from_previous carries the frame
forward instead and should stay continuous through the same crossing.
"""

from __future__ import annotations

import numpy as np

from guidance_sim.rl.actions import lateral_basis, lateral_basis_from_previous


def _velocity_path_through_pole(n: int) -> list[np.ndarray]:
    """Speed-100 velocities whose direction sweeps from just below vertical,
    through vertical, to just above -- the exact crossing lateral_basis
    documents as singular."""

    pitch = np.linspace(np.deg2rad(89.0), np.deg2rad(91.0), n)
    return [100.0 * np.array([np.cos(p), 0.0, np.sin(p)]) for p in pitch]


def test_static_formula_flips_hard_across_the_pole():
    path = _velocity_path_through_pole(9)
    e1s = [lateral_basis(v)[0] for v in path]
    step_angles = [
        np.degrees(np.arccos(np.clip(np.dot(e1s[i], e1s[i + 1]), -1.0, 1.0)))
        for i in range(len(e1s) - 1)
    ]
    assert max(step_angles) > 90.0, step_angles


def test_carried_basis_stays_continuous_across_the_pole():
    path = _velocity_path_through_pole(9)
    previous_e1 = None
    e1s = []
    for v in path:
        e1, e2 = lateral_basis_from_previous(v, previous_e1)
        assert np.isclose(np.linalg.norm(e1), 1.0)
        assert np.isclose(np.linalg.norm(e2), 1.0)
        assert abs(np.dot(e1, v)) < 1e-9
        assert abs(np.dot(e2, v)) < 1e-9
        e1s.append(e1)
        previous_e1 = e1
    step_angles = [
        np.degrees(np.arccos(np.clip(np.dot(e1s[i], e1s[i + 1]), -1.0, 1.0)))
        for i in range(len(e1s) - 1)
    ]
    assert max(step_angles) < 5.0, step_angles


def test_carried_basis_falls_back_to_static_formula_with_no_previous_frame():
    velocity = np.array([200.0, -50.0, 30.0])
    e1, e2 = lateral_basis_from_previous(velocity, None)
    expected_e1, expected_e2 = lateral_basis(velocity)
    assert np.allclose(e1, expected_e1)
    assert np.allclose(e2, expected_e2)


def test_carried_basis_matches_static_formula_exactly_away_from_the_pole():
    """Ordinary (non-diving) flight must reproduce the pinned static formula
    bit-for-bit, even with an unrelated previous frame in hand -- other call
    sites and golden-rollout regression tests assume it."""
    velocity = np.array([300.0, 40.0, -20.0])
    unrelated_previous_e1 = np.array([0.0, 1.0, 0.0])
    e1, e2 = lateral_basis_from_previous(velocity, unrelated_previous_e1)
    expected_e1, expected_e2 = lateral_basis(velocity)
    assert np.array_equal(e1, expected_e1)
    assert np.array_equal(e2, expected_e2)


def test_carried_basis_falls_back_when_previous_frame_degenerates():
    velocity = np.array([0.0, 0.0, 100.0])
    previous_e1 = velocity / np.linalg.norm(velocity)  # parallel: projection is zero
    e1, e2 = lateral_basis_from_previous(velocity, previous_e1)
    expected_e1, expected_e2 = lateral_basis(velocity)
    assert np.allclose(e1, expected_e1)
    assert np.allclose(e2, expected_e2)
