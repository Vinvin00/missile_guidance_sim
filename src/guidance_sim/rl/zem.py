"""Zero-effort miss used as a potential for RL reward shaping.

Standard ZEM divides by closing velocity, which is undefined or negative
when the target recedes, and LOS rate blows up as range → 0.  This helper
never uses LOS rate.  It returns a finite predicted-miss distance:

* range at or inside the lethal radius → 0 (consistently zero at intercept);
* otherwise a single continuous horizon

      t_go = min(range / max(|Vc|, vc_min), t_go_max)

  so there is no closing/receding branch.

The potential is Φ = −ZEM / (ZEM + scale); callers zero Φ at every terminal.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

_RANGE_EPS = 1e-9


@dataclass(frozen=True)
class ZemSafeguards:
    vc_min_m_s: float = 1.0
    t_go_max_s: float = 25.0


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
    safeguards: ZemSafeguards | None = None,
) -> float:
    """Return a non-negative, capped prediction horizon.

    Continuous in ``closing_velocity``: the effective speed is
    ``max(|Vc|, vc_min)``, so the old jump from ``t_go_max`` (barely closing)
    to a separate receding horizon cannot occur.
    """

    cfg = safeguards or ZemSafeguards()
    if range_m <= _RANGE_EPS:
        return 0.0
    vc_eff = max(abs(float(closing_velocity)), float(cfg.vc_min_m_s))
    if vc_eff <= 0.0:
        return float(cfg.t_go_max_s)
    return min(float(range_m) / vc_eff, float(cfg.t_go_max_s))


def predicted_miss_m(
    relative_position_m: np.ndarray,
    relative_velocity_m_s: np.ndarray,
    intercept_radius_m: float,
    safeguards: ZemSafeguards | None = None,
) -> float:
    """Kinematic ZEM magnitude (no target-accel term) with continuous t_go."""

    cfg = safeguards or ZemSafeguards()
    relative_position_m = np.asarray(relative_position_m, dtype=float).reshape(3)
    relative_velocity_m_s = np.asarray(relative_velocity_m_s, dtype=float).reshape(3)
    range_m = float(np.linalg.norm(relative_position_m))
    if not np.isfinite(range_m):
        raise ValueError("relative position must be finite")
    if range_m <= float(intercept_radius_m):
        return 0.0
    closing = closing_velocity_m_s(relative_position_m, relative_velocity_m_s)
    t_go = time_to_go_s(range_m, closing, cfg)
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
