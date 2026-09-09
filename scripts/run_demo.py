"""
Quick manual demo: run one PN-guided 3D intercept under realistic
gravity/drag/g-limit dynamics, print the result, and write plots.

Usage:
    python scripts/run_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.simulation.engine import Simulation, SimulationConfig
from guidance_sim.visualization.plotter import (
    animate_3d,
    plot_diagnostics,
    plot_trajectory_3d,
)


def main() -> None:
    pursuer_vehicle = VehicleParams(
        mass=50.0, reference_area=0.05, drag_coefficient=0.3,
        max_normal_force_coefficient=15.0, max_load_factor=25.0,
    )
    target_vehicle = VehicleParams(
        mass=40.0, reference_area=0.06, drag_coefficient=0.35,
        max_normal_force_coefficient=10.0, max_load_factor=9.0,
    )

    # Non-maneuvering target: PN should fly a near-straight lead course.
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0]),
        vehicle=pursuer_vehicle,
    )
    target = PointMassEntity(
        name="target",
        state=State(position=[7000.0, 400.0, 3300.0], velocity=[-200.0, 0.0, 0.0]),
        vehicle=target_vehicle,
    )
    guidance = ProportionalNavigation(navigation_constant=4.0)
    maneuver = NoManeuver()

    sim = Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=guidance,
        target_maneuver=maneuver,
        config=SimulationConfig(dt=0.01, max_time=45.0, intercept_radius=5.0),
    )
    result = sim.run()

    print(f"Hit: {result.hit}")
    print(f"Miss distance: {result.miss_distance:.2f} m")
    print(f"Time to intercept: {result.time_to_intercept}")
    print(f"Final sim time: {result.final_time:.2f} s")
    print(f"Trajectory points recorded: {len(result.times)}")

    out_dir = Path(__file__).resolve().parent.parent / "outputs"
    plot_trajectory_3d(
        result, str(out_dir / "demo_trajectory_3d.png"), title="PN lead intercept"
    )
    plot_diagnostics(result, str(out_dir / "demo_diagnostics.png"))
    animate_3d(result, str(out_dir / "demo_animation.gif"), fps=20)
    print(f"Wrote plots under {out_dir}")


if __name__ == "__main__":
    main()
