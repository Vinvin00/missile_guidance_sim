"""Step 1: visualization plotter writes artifacts without error."""

from pathlib import Path

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.simulation.engine import Simulation, SimulationConfig
from guidance_sim.visualization.plotter import (
    animate_3d,
    plot_diagnostics,
    plot_trajectory_3d,
)


def _short_result():
    pursuer = PointMassEntity(
        name="pursuer",
        state=State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0]),
        vehicle=VehicleParams(
            mass=50.0, reference_area=0.05, drag_coefficient=0.3,
            max_normal_force_coefficient=15.0, max_load_factor=25.0,
        ),
    )
    target = PointMassEntity(
        name="target",
        state=State(position=[3000.0, 200.0, 3100.0], velocity=[-200.0, 0.0, 0.0]),
        vehicle=VehicleParams(
            mass=40.0, reference_area=0.06, drag_coefficient=0.35,
            max_normal_force_coefficient=10.0, max_load_factor=9.0,
        ),
    )
    return Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=ProportionalNavigation(navigation_constant=4.0),
        target_maneuver=NoManeuver(),
        config=SimulationConfig(
            dt=0.05, max_time=20.0, intercept_radius=5.0, autopilot_tau=0.0
        ),
    ).run()


def test_plotters_write_files(tmp_path: Path):
    result = _short_result()
    assert len(result.times) > 2

    traj = tmp_path / "traj.png"
    diag = tmp_path / "diag.png"
    gif = tmp_path / "anim.gif"

    plot_trajectory_3d(result, str(traj), title="test")
    plot_diagnostics(result, str(diag))
    animate_3d(result, str(gif), fps=10)

    assert traj.is_file() and traj.stat().st_size > 0
    assert diag.is_file() and diag.stat().st_size > 0
    assert gif.is_file() and gif.stat().st_size > 0


def test_demo_acceptance_qualitative_shape():
    """
    Acceptance cues from Step 1: hit, mostly monotonic range decrease,
    altitude sag, speed bleed (final speed < initial estimate).
    """
    result = _short_result()
    assert result.hit

    ranges = np.linalg.norm(result.target_trajectory - result.pursuer_trajectory, axis=1)
    # Allow tiny numerical wiggles; overall trend should be closing.
    early = float(np.mean(ranges[: max(3, len(ranges) // 10)]))
    late = float(np.mean(ranges[-max(3, len(ranges) // 10) :]))
    assert late < early

    alt = result.pursuer_trajectory[:, 2]
    assert alt[-1] < alt[0]

    # Speed from position gradient should drop under drag.
    if len(result.times) >= 3:
        dt = float(np.median(np.diff(result.times)))
        speeds = np.linalg.norm(np.gradient(result.pursuer_trajectory, axis=0), axis=1) / dt
        assert speeds[-2] < speeds[1]
