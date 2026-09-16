"""Potential-based intercept reward plus a frozen Phase-1 diagnostic replica.

New reward (undiscounted episode sum, γ_shape = 1 by default):

* dense: ``shaping_weight * (γ Φ(s') − Φ(s))`` with
  ``Φ = −ZEM / (ZEM + zem_scale) ∈ (−1, 0]``, and ``Φ = 0`` at hit, miss,
  timeout, and ground impact;
* terminal: ``+intercept_bonus`` on hit; otherwise
  ``−miss_penalty * tanh(closest_approach / miss_tanh_scale)`` using the
  episode-minimum range, never the final range;
* effort: ``−effort_weight * dt * (||a_achieved|| / a_structural)²`` on the
  post-clamp lateral acceleration;
* precision (terminal, any outcome): ``+precision_weight * exp(−cpa /
  precision_scale)`` on the true sub-step closest approach. Off by default.
  The hit bonus is binary at ``intercept_radius`` and the tanh miss penalty is
  flat below ~50 m, so without this nothing separates a 1 m hit from a 9 m
  near-miss -- which is where every evasive-lineage loss actually sits.

The Phase-1 range-telescope / commanded-effort / ±100 terminal reward is
computed in parallel as ``legacy_*`` so checkpoint 1–4 trends remain
comparable.  It is never added into the env return.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from guidance_sim.rl.zem import ZemSafeguards, potential_from_zem, predicted_miss_m


@dataclass(frozen=True)
class RewardConfig:
    """Scales for the ZEM-potential reward and the frozen Phase-1 diagnostic."""

    progress_scale_m: float = 100.0
    legacy_effort_weight: float = 1.0
    intercept_bonus: float = 100.0
    miss_penalty: float = 100.0
    timeout_penalty: float = 100.0
    shaping_gamma: float = 1.0
    zem_scale_m: float = 500.0
    miss_tanh_scale_m: float = 1_000.0
    effort_weight: float = 5.0
    # Penalises the step-to-step *change* in commanded (pre-lag) lateral
    # accel, not just its achieved (post-lag) magnitude. achieved_lateral_m_s2
    # is low-pass filtered by the autopilot's actuator lag, so a policy that
    # bang-bang jitters the command sees a small achieved-effort penalty even
    # though every jitter cycle costs real induced drag on the rigid-body
    # airframe (docs/rl-interface-6dof.md, "effort profile"). 0 keeps every
    # existing lineage's reward bit-identical.
    effort_rate_weight: float = 0.0
    shaping_weight: float = 50.0
    terminal_weight: float = 1.0
    vc_min_m_s: float = 1.0
    t_go_max_s: float = 25.0
    precision_weight: float = 0.0
    precision_scale_m: float = 5.0
    # Unused by continuous t_go; retained so older config dumps remain valid.
    t_horizon_receding_s: float = 5.0

    def __post_init__(self) -> None:
        positive = (
            self.progress_scale_m,
            self.legacy_effort_weight,
            self.intercept_bonus,
            self.miss_penalty,
            self.timeout_penalty,
            self.zem_scale_m,
            self.miss_tanh_scale_m,
            self.precision_scale_m,
        )
        if not all(np.isfinite(value) and value > 0.0 for value in positive):
            raise ValueError("reward scales must be finite and positive")
        non_negative = (
            self.effort_weight,
            self.effort_rate_weight,
            self.shaping_weight,
            self.terminal_weight,
            self.vc_min_m_s,
            self.t_go_max_s,
            self.t_horizon_receding_s,
            self.precision_weight,
        )
        if not all(np.isfinite(value) and value >= 0.0 for value in non_negative):
            raise ValueError("reward weights and ZEM caps must be finite and non-negative")
        if not np.isfinite(self.shaping_gamma) or not 0.0 < self.shaping_gamma <= 1.0:
            raise ValueError("shaping_gamma must be in (0, 1]")

    def zem_safeguards(self) -> ZemSafeguards:
        return ZemSafeguards(
            vc_min_m_s=self.vc_min_m_s,
            t_go_max_s=self.t_go_max_s,
            t_horizon_receding_s=self.t_horizon_receding_s,
        )


@dataclass(frozen=True)
class RewardBreakdown:
    total: float
    shaping: float
    effort: float
    terminal: float
    legacy_progress: float
    legacy_effort: float
    legacy_terminal: float
    legacy_total: float
    zem_m: float
    potential: float

    def env_terms(self) -> dict[str, float]:
        """Keys consumed by training eval: ``progress`` is the dense shaping term."""

        return {
            "progress": self.shaping,
            "shaping": self.shaping,
            "effort": self.effort,
            "terminal": self.terminal,
            "legacy_progress": self.legacy_progress,
            "legacy_effort": self.legacy_effort,
            "legacy_terminal": self.legacy_terminal,
            "legacy_total": self.legacy_total,
            "zem_m": self.zem_m,
            "potential": self.potential,
        }


def predicted_miss_from_states(
    pursuer_position: np.ndarray,
    pursuer_velocity: np.ndarray,
    target_position: np.ndarray,
    target_velocity: np.ndarray,
    remaining_time_s: float,
    intercept_radius_m: float,
    config: RewardConfig,
) -> float:
    relative_position = np.asarray(target_position, dtype=float) - np.asarray(
        pursuer_position, dtype=float
    )
    relative_velocity = np.asarray(target_velocity, dtype=float) - np.asarray(
        pursuer_velocity, dtype=float
    )
    return predicted_miss_m(
        relative_position,
        relative_velocity,
        remaining_time_s,
        intercept_radius_m,
        config.zem_safeguards(),
    )


def compute_reward(
    *,
    previous_potential: float,
    zem_m: float,
    previous_range_m: float,
    current_range_m: float,
    min_range_m: float,
    achieved_lateral_m_s2: np.ndarray,
    legacy_commanded_m_s2: np.ndarray,
    action_limit_m_s2: float,
    dt: float,
    outcome: str,
    config: RewardConfig,
    closest_approach_m: float | None = None,
    previous_commanded_m_s2: np.ndarray | None = None,
) -> RewardBreakdown:
    """Evaluate new and legacy reward terms for a single transition."""

    terminal_state = outcome != "ongoing"
    phi_next = potential_from_zem(
        zem_m, config.zem_scale_m, terminal=terminal_state
    )
    shaping = config.shaping_weight * (
        config.shaping_gamma * phi_next - previous_potential
    )
    achieved_norm = float(np.linalg.norm(np.asarray(achieved_lateral_m_s2, dtype=float)))
    effort = (
        -config.effort_weight
        * dt
        * (achieved_norm / action_limit_m_s2) ** 2
    )
    if config.effort_rate_weight > 0.0 and previous_commanded_m_s2 is not None:
        commanded_step = np.asarray(legacy_commanded_m_s2, dtype=float) - np.asarray(
            previous_commanded_m_s2, dtype=float
        )
        effort += (
            -config.effort_rate_weight
            * dt
            * (float(np.linalg.norm(commanded_step)) / action_limit_m_s2) ** 2
        )
    terminal = _new_terminal(outcome, min_range_m, config)
    if terminal_state and config.precision_weight > 0.0:
        cpa = min_range_m if closest_approach_m is None else closest_approach_m
        terminal += config.precision_weight * float(
            np.exp(-float(cpa) / config.precision_scale_m)
        )

    legacy_progress = (previous_range_m - current_range_m) / config.progress_scale_m
    legacy_command_norm = float(
        np.linalg.norm(np.asarray(legacy_commanded_m_s2, dtype=float))
    )
    legacy_effort = (
        -config.legacy_effort_weight
        * dt
        * (legacy_command_norm / action_limit_m_s2) ** 2
    )
    legacy_terminal = _legacy_terminal(outcome, config)
    legacy_total = legacy_progress + legacy_effort + legacy_terminal
    total = shaping + effort + terminal
    return RewardBreakdown(
        total=float(total),
        shaping=float(shaping),
        effort=float(effort),
        terminal=float(terminal),
        legacy_progress=float(legacy_progress),
        legacy_effort=float(legacy_effort),
        legacy_terminal=float(legacy_terminal),
        legacy_total=float(legacy_total),
        zem_m=float(zem_m),
        potential=float(phi_next),
    )


def _new_terminal(outcome: str, min_range_m: float, config: RewardConfig) -> float:
    if outcome == "hit":
        return config.terminal_weight * config.intercept_bonus
    if outcome in ("miss", "timeout"):
        graded = config.miss_penalty * np.tanh(
            float(min_range_m) / config.miss_tanh_scale_m
        )
        return -config.terminal_weight * float(graded)
    return 0.0


def _legacy_terminal(outcome: str, config: RewardConfig) -> float:
    if outcome == "hit":
        return config.intercept_bonus
    if outcome == "miss":
        return -config.miss_penalty
    if outcome == "timeout":
        return -config.timeout_penalty
    return 0.0
