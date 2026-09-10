"""Zero-effort miss used as a potential for RL reward shaping.

Standard ZEM divides by closing velocity, which is undefined or negative
when the target recedes, and LOS rate blows up as range → 0.  This helper
never uses LOS rate.  It returns a finite predicted-miss distance:

* range at or inside the lethal radius → 0 (consistently zero at intercept);
* closing (Vc > vc_min) → t_go = min(range/Vc, t_go_max, time remaining);
* receding or nearly so → fixed-horizon prediction over
  min(t_horizon_receding, time remaining).

The potential is Φ = −ZEM; callers zero Φ at every terminal state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_RANGE_EPS = 1e-9


@dataclass(frozen=True)
class ZemSafeguards:
    vc_min_m_s: float = 1.0
    t_go_max_s: float = 25.0
    t_horizon_receding_s: float = 5.0


def closing_velocity_m_s(
    relative_position_m: np.ndarray,
    relative_velocity_m_s: np.ndarray,
) -> float:
    relative_position_m = np.asarray(relative_position_m, dtype=float).reshape(3)
    range_m = float(np.linalg.norm(relative_position_m))
    if range_m <= _RANGE_EPS:
        return 0.0
    relative_velocity_m_s = np.asarray(relative_velocity_m_s, dtype=float).reshape(3)
    return -float(np.dot(relative_position_m, relative_velocity_m_s) / range_m)


def time_to_go_s(
    range_m: float,
    closing_velocity: float,
    remaining_time_s: float = np.inf,
    safeguards: ZemSafeguards | None = None,
) -> float:
    """Return a non-negative, capped prediction horizon.

    ``remaining_time_s`` is accepted for call-site compatibility but does
    **not** cap closing ``t_go``.  Capping on the episode clock made Φ a
    function of ``max_time`` and inflated ZEM as timeout approached, so the
    terminal Φ=0 reset paid out range as a bonus.  Closing uses
    ``min(range/Vc, t_go_max)``; receding uses the fixed horizon.
    """

    cfg = safeguards or ZemSafeguards()
    del remaining_time_s
    if float(closing_velocity) > cfg.vc_min_m_s and range_m > _RANGE_EPS:
        t_go = float(range_m) / float(closing_velocity)
        return min(t_go, cfg.t_go_max_s)
    return cfg.t_horizon_receding_s


def predicted_miss_m(
    relative_position_m: np.ndarray,
    relative_velocity_m_s: np.ndarray,
    remaining_time_s: float,
    intercept_radius_m: float,
    safeguards: ZemSafeguards | None = None,
) -> float:
    """Kinematic ZEM magnitude (no target-accel term) with receding/near-zero guards."""

    cfg = safeguards or ZemSafeguards()
    relative_position_m = np.asarray(relative_position_m, dtype=float).reshape(3)
    relative_velocity_m_s = np.asarray(relative_velocity_m_s, dtype=float).reshape(3)
    range_m = float(np.linalg.norm(relative_position_m))
    if not np.isfinite(range_m):
        raise ValueError("relative position must be finite")
    if range_m <= float(intercept_radius_m):
        return 0.0
    closing = closing_velocity_m_s(relative_position_m, relative_velocity_m_s)
    t_go = time_to_go_s(range_m, closing, remaining_time_s, cfg)
    zem_vec = relative_position_m + relative_velocity_m_s * t_go
    zem = float(np.linalg.norm(zem_vec))
    if not np.isfinite(zem) or zem < 0.0:
        raise RuntimeError("ZEM safeguard failed to produce a finite non-negative miss")
    return zem


def potential_from_zem(
    zem_m: float,
    zem_scale_m: float,
    *,
    terminal: bool,
) -> float:
    """Φ(s) = −ZEM / (ZEM + scale) ∈ (−1, 0], identically 0 at every terminal.

    The bounded form is required so zeroing Φ at miss/timeout cannot pay out
    kilometres of residual ZEM as a bonus that beats a true intercept.
    """

    if terminal:
        return 0.0
    if not np.isfinite(zem_m) or zem_m < 0.0:
        raise ValueError("ZEM must be finite and non-negative")
    if not np.isfinite(zem_scale_m) or zem_scale_m <= 0.0:
        raise ValueError("zem_scale_m must be finite and positive")
    return -float(zem_m) / (float(zem_m) + float(zem_scale_m))
