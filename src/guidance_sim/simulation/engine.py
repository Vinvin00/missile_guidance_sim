"""
Simulation engine: drives a pursuer (guided by a GuidanceLaw) against
a target (following a ManeuverProfile) forward in time under real
3D dynamics (gravity + drag + clamped maneuver command) until either
intercept (miss distance below threshold) or a timeout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.physics.entities import PointMassEntity
from guidance_sim.physics.integrator import IntegratorType
from guidance_sim.physics.maneuvers import ManeuverProfile


@dataclass
class SimulationResult:
    hit: bool
    miss_distance: float
    time_to_intercept: Optional[float]  # None if no intercept occurred
    final_time: float
    pursuer_trajectory: np.ndarray  # shape (T, 3)
    target_trajectory: np.ndarray  # shape (T, 3)
    times: np.ndarray  # shape (T,)
    pursuer_accel_cmd: np.ndarray  # shape (T, 3); raw guidance at sample
    pursuer_accel_achieved: np.ndarray  # shape (T, 3); clamped lateral applied


@dataclass
class SimulationConfig:
    dt: float = 0.01  # s
    max_time: float = 60.0  # s
    intercept_radius: float = 5.0  # m; range below this counts as a hit
    integrator: IntegratorType = IntegratorType.RK4
    # First-order autopilot lag time constant [s]. 0.2 s is a typical
    # short-range interceptor airframe/autopilot response (Nesline &
    # Zarchan); 0.0 disables the lag exactly (legacy / ideal tests).
    autopilot_tau: float = 0.2


class Simulation:
    def __init__(
        self,
        pursuer: PointMassEntity,
        target: PointMassEntity,
        guidance_law: GuidanceLaw,
        target_maneuver: ManeuverProfile,
        config: Optional[SimulationConfig] = None,
    ):
        self.pursuer = pursuer
        self.target = target
        self.guidance_law = guidance_law
        self.target_maneuver = target_maneuver
        self.config = config if config is not None else SimulationConfig()

    def _range(self) -> float:
        return float(np.linalg.norm(self.target.state.position - self.pursuer.state.position))

    def run(self) -> SimulationResult:
        cfg = self.config
        t = 0.0
        times: List[float] = []
        pursuer_positions: List[np.ndarray] = []
        target_positions: List[np.ndarray] = []
        accel_cmds: List[np.ndarray] = []
        accel_achieved: List[np.ndarray] = []

        min_range = self._range()
        hit = False
        time_to_intercept: Optional[float] = None

        while t <= cfg.max_time:
            times.append(t)
            pursuer_positions.append(self.pursuer.state.position.copy())
            target_positions.append(self.target.state.position.copy())

            current_range = self._range()
            min_range = min(min_range, current_range)

            if current_range <= cfg.intercept_radius:
                hit = True
                time_to_intercept = t
                # Terminal sample: no command issued after intercept.
                accel_cmds.append(np.zeros(3))
                accel_achieved.append(np.zeros(3))
                break

            target_accel_cmd = self.target_maneuver.lateral_accel(t, self.target.state)
            self.target.step(
                cfg.dt,
                target_accel_cmd,
                integrator=cfg.integrator,
                autopilot_tau=cfg.autopilot_tau,
            )

            pursuer_accel_cmd = self.guidance_law.compute_command(
                self.pursuer.state, self.target.state, cfg.dt
            )
            self.pursuer.step(
                cfg.dt,
                pursuer_accel_cmd,
                integrator=cfg.integrator,
                autopilot_tau=cfg.autopilot_tau,
            )

            accel_cmds.append(np.asarray(pursuer_accel_cmd, dtype=float).reshape(3).copy())
            accel_achieved.append(self.pursuer.last_achieved_lateral_accel.copy())

            t += cfg.dt

        return SimulationResult(
            hit=hit,
            miss_distance=min_range,
            time_to_intercept=time_to_intercept,
            final_time=t,
            pursuer_trajectory=np.array(pursuer_positions),
            target_trajectory=np.array(target_positions),
            times=np.array(times),
            pursuer_accel_cmd=np.array(accel_cmds),
            pursuer_accel_achieved=np.array(accel_achieved),
        )
