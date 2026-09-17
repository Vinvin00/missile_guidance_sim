"""Zero-effort-miss safeguards: receding target, near-zero range, Vc continuity."""

from __future__ import annotations

import numpy as np
import pytest

from guidance_sim.rl.reward import RewardConfig
from guidance_sim.rl.zem import (
    ZemSafeguards,
    potential_from_zem,
    predicted_miss_m,
    time_to_go_s,
)


def test_receding_target_uses_speed_based_horizon_and_stays_finite():
    relative_position = np.array([1_000.0, 0.0, 0.0])
    relative_velocity = np.array([100.0, 0.0, 0.0])  # receding, Vc = -100 m/s
    safeguards = ZemSafeguards(vc_min_m_s=1.0, t_go_max_s=25.0)
    zem = predicted_miss_m(
        relative_position,
        relative_velocity,
        intercept_radius_m=5.0,
        safeguards=safeguards,
    )
    # Unified horizon: t_go = min(range / max(|Vc|, vc_min), t_go_max) = 10 s.
    expected_t_go = 1_000.0 / 100.0
    expected = float(np.linalg.norm(relative_position + relative_velocity * expected_t_go))
    assert zem == pytest.approx(expected)
    assert zem == pytest.approx(2_000.0)
    assert np.isfinite(zem)
    assert zem > 0.0
    t_go = time_to_go_s(1_000.0, closing_velocity=-100.0)
    assert t_go == pytest.approx(expected_t_go)


def test_near_zero_range_returns_zero_and_does_not_blow_up():
    relative_position = np.array([1.0, 0.0, 0.0])
    relative_velocity = np.array([-400.0, 50.0, -20.0])
    zem = predicted_miss_m(
        relative_position,
        relative_velocity,
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
        intercept_radius_m=5.0,
    )
    expected = float(np.linalg.norm(relative_position + relative_velocity * t_go))
    assert zem == pytest.approx(expected)
    assert zem == pytest.approx(80.0, abs=1.0)


def test_phi_is_continuous_across_closing_receding_vc_boundary():
    """Sweep Vc through vc_min at several ranges; Phi must not jump."""

    cfg = RewardConfig()
    safeguards = cfg.zem_safeguards()
    zem_scale = cfg.zem_scale_m
    shaping_weight = cfg.shaping_weight
    vc_min = safeguards.vc_min_m_s
    # Dense sweep including points arbitrarily close to ±vc_min and 0.
    vc_values = np.concatenate(
        (
            np.linspace(-5.0, 5.0, 401),
            np.array(
                [
                    vc_min - 1e-9,
                    vc_min,
                    vc_min + 1e-9,
                    -vc_min - 1e-9,
                    -vc_min,
                    -vc_min + 1e-9,
                    0.0,
                ]
            ),
        )
    )
    vc_values = np.unique(np.sort(vc_values))
    ranges_m = (500.0, 1_000.0, 3_000.0, 7_000.0)
    max_dphi = 0.0
    max_d_shaping = 0.0
    for range_m in ranges_m:
        phis = []
        for vc in vc_values:
            relative_position = np.array([range_m, 0.0, 0.0])
            relative_velocity = np.array([-float(vc), 0.0, 0.0])
            zem = predicted_miss_m(
                relative_position,
                relative_velocity,
                intercept_radius_m=5.0,
                safeguards=safeguards,
            )
            phis.append(potential_from_zem(zem, zem_scale, terminal=False))
        phis = np.asarray(phis, dtype=float)
        assert np.all(np.isfinite(phis))
        dphi = np.max(np.abs(np.diff(phis)))
        max_dphi = max(max_dphi, float(dphi))
        max_d_shaping = max(max_d_shaping, float(shaping_weight * dphi))
        # Adjacent sample spacing is ≤ 0.025 m/s over the linspace; a
        # discontinuous branch would produce |dPhi| ~ 1e-2 at R=500.
        assert dphi < 5e-3, (
            f"Phi jumped by {dphi} across Vc samples at range={range_m}"
        )
    # Global bound: per-step shaping from a Vc-boundary flip must stay tiny.
    assert max_d_shaping < 0.25, (
        f"worst adjacent shaping jump {max_d_shaping} exceeds continuity budget"
    )
    assert max_dphi < 5e-3
