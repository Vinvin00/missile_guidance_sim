"""Step 2: validate_physics classification + tiny-grid sweep shape."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Import the script module by path (not an installed package).
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import validate_physics as vp  # noqa: E402


def test_classify_hit_threshold():
    assert vp.classify_hit(0.0, threshold_m=5.0) is True
    assert vp.classify_hit(3.0, threshold_m=5.0) is True  # Step 1 demo-scale miss
    assert vp.classify_hit(5.0, threshold_m=5.0) is True
    assert vp.classify_hit(5.01, threshold_m=5.0) is False
    assert vp.classify_hit(10.0, threshold_m=5.0) is False


def test_tiny_sweep_output_shape():
    offsets = np.array([0.0, 400.0, 1200.0])
    ranges = np.array([5000.0, 7000.0, 9000.0])
    result = vp.run_sweep(
        offsets,
        ranges,
        threshold_m=vp.HIT_THRESHOLD_M,
        dt=0.05,  # coarse for speed; shape/classification API only
        max_time=45.0,
    )
    assert result.lateral_offsets.shape == (3,)
    assert result.initial_ranges.shape == (3,)
    assert result.miss_distances.shape == (3, 3)
    assert result.hits.shape == (3, 3)
    assert result.hits.dtype == bool
    assert np.isfinite(result.miss_distances).all()
    # Hits must agree with threshold on miss distances.
    for j in range(3):
        for i in range(3):
            assert result.hits[j, i] == vp.classify_hit(
                result.miss_distances[j, i], result.threshold_m
            )


def test_demo_point_is_hit_at_sweep_dt():
    """Sanity: demo IC (7000 m, 400 m) remains a hit at sweep dt=0.02."""
    miss = vp.run_engagement(400.0, 7000.0, dt=vp.SWEEP_DT)
    assert vp.classify_hit(miss, vp.HIT_THRESHOLD_M), f"miss={miss:.2f} m"
