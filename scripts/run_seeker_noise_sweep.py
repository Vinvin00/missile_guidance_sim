#!/usr/bin/env python3
"""
Sweep seeker noise scale and record miss distance (Priority 1 artifact).

Writes:
  outputs/seeker_noise_sweep.csv
  outputs/seeker_noise_sweep.png

Usage (from missile_guidance_sim/):
  .venv/bin/python scripts/run_seeker_noise_sweep.py
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

# Headless-safe plotting (CI / sandboxes without a display).
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np

from guidance_sim.estimation.alpha_beta import AlphaBetaFilter
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.sensors.measurement import SeekerNoiseConfig, Sensor, SensorConfig
from guidance_sim.simulation.engine import Simulation, SimulationConfig

PURSUER_VEHICLE = VehicleParams(
    mass=50.0,
    reference_area=0.05,
    drag_coefficient=0.3,
    max_normal_force_coefficient=15.0,
    max_load_factor=25.0,
)
TARGET_VEHICLE = VehicleParams(
    mass=40.0,
    reference_area=0.06,
    drag_coefficient=0.35,
    max_normal_force_coefficient=10.0,
    max_load_factor=9.0,
)


def run_one(noise_scale: float, seed: int) -> float:
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(
            position=np.array([0.0, 0.0, 3000.0]),
            velocity=np.array([350.0, 0.0, 0.0]),
        ),
        vehicle=PURSUER_VEHICLE,
    )
    target = PointMassEntity(
        name="target",
        state=State(
            position=np.array([5500.0, 1500.0, 3200.0]),
            velocity=np.array([-180.0, 40.0, 0.0]),
        ),
        vehicle=TARGET_VEHICLE,
    )
    sensor = Sensor(
        SensorConfig(
            noise=SeekerNoiseConfig().scaled(noise_scale),
            update_rate_hz=100.0,
        )
    )
    estimator = AlphaBetaFilter(alpha=0.75, initial_target=target.state.copy())
    sim = Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=ProportionalNavigation(navigation_constant=3.0),
        target_maneuver=NoManeuver(),
        config=SimulationConfig(
            dt=0.01, max_time=45.0, intercept_radius=5.0, autopilot_tau=0.2
        ),
        sensor=sensor,
        estimator=estimator,
        rng=np.random.default_rng(seed),
    )
    return float(sim.run().miss_distance)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scales",
        type=float,
        nargs="+",
        default=[0.0, 2.0, 5.0, 12.0],
        help="Multipliers applied to default SeekerNoiseConfig std-devs",
    )
    parser.add_argument("--trials", type=int, default=7, help="Seeds per scale")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for CSV and PNG",
    )
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[tuple[float, int, float]] = []
    medians: list[float] = []
    for scale in args.scales:
        misses = [run_one(scale, seed=20_000 + i) for i in range(args.trials)]
        med = float(np.median(misses))
        medians.append(med)
        print(f"scale={scale:g}: median={med:.3f} m  mean={np.mean(misses):.3f} m")
        for i, m in enumerate(misses):
            rows.append((scale, i, m))

    csv_path = args.out_dir / "seeker_noise_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["noise_scale", "seed_index", "miss_distance_m"])
        writer.writerows(rows)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(args.scales, medians, "o-", color="C0", label="median miss")
    # Per-trial scatter for dispersion feel
    for scale, _idx, miss in rows:
        ax.scatter(scale, miss, color="C0", alpha=0.25, s=18)
    ax.set_xlabel("Seeker noise scale (× baseline std)")
    ax.set_ylabel("Miss distance [m]")
    ax.set_title("PN miss distance vs seeker noise (α-β filtered)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    png_path = args.out_dir / "seeker_noise_sweep.png"
    fig.savefig(png_path, dpi=140)
    plt.close(fig)

    print(f"Wrote {csv_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
