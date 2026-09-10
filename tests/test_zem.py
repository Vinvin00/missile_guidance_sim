"""Zero-effort-miss safeguards: receding target and near-zero range."""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.rl.zem import (
    ZemSafeguards,
    potential_from_zem,
    predicted_miss_m,
    time_to_go_s,
)


def test_receding_target_uses_fixed_horizon_and_stays_finite():
    relative_position = np.array([1_000.0, 0.0, 0.0])
    relative_velocity = np.array([100.0, 0.0, 0.0])  # receding, Vc = -100 m/s
    safeguards = ZemSafeguards(t_horizon_receding_s=5.0, t_go_max_s=25.0)
    zem = predicted_miss_m(
        relative_position,
        relative_velocity,
        remaining_time_s=20.0,
        intercept_radius_m=5.0,
        safeguards=safeguards,
    )
    expected = float(np.linalg.norm(relative_position + relative_velocity * 5.0))
    assert zem == pytest.approx(expected)
    assert zem == pytest.approx(1_500.0)
    assert np.isfinite(zem)
    assert zem > 0.0
    t_go = time_to_go_s(1_000.0, closing_velocity=-100.0, remaining_time_s=20.0)
    assert t_go == pytest.approx(5.0)


def test_near_zero_range_returns_zero_and_does_not_blow_up():
    relative_position = np.array([1.0, 0.0, 0.0])
    relative_velocity = np.array([-400.0, 50.0, -20.0])
    zem = predicted_miss_m(
        relative_position,
        relative_velocity,
        remaining_time_s=25.0,
        intercept_radius_m=5.0,
    )
    assert zem == 0.0
    assert potential_from_zem(zem, zem_scale_m=10.0, terminal=False) == 0.0
    assert potential_from_zem(1_000.0, zem_scale_m=10.0, terminal=True) == 0.0
    assert -1.0 < potential_from_zem(1.0e9, zem_scale_m=500.0, terminal=False) <= 0.0


def test_closing_predicted_miss_is_the_kinematic_miss():
    relative_position = np.array([1_000.0, 80.0, 0.0])
    relative_velocity = np.array([-100.0, 0.0, 0.0])
    range_m = float(np.linalg.norm(relative_position))
    closing = -float(np.dot(relative_position, relative_velocity) / range_m)
    t_go = range_m / closing
    zem = predicted_miss_m(
        relative_position,
        relative_velocity,
        remaining_time_s=25.0,
        intercept_radius_m=5.0,
    )
    expected = float(np.linalg.norm(relative_position + relative_velocity * t_go))
    assert zem == pytest.approx(expected)
    assert zem == pytest.approx(80.0, abs=1.0)
