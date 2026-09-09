"""Step 3a: first-order autopilot lag."""

from __future__ import annotations

import numpy as np

from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams, lag_step
from guidance_sim.physics.maneuvers import NoManeuver
from guidance_sim.simulation.engine import Simulation, SimulationConfig


PURSUER_VEHICLE = VehicleParams(
    mass=50.0, reference_area=0.05, drag_coefficient=0.3,
    max_normal_force_coefficient=15.0, max_load_factor=25.0,
)
TARGET_VEHICLE = VehicleParams(
    mass=40.0, reference_area=0.06, drag_coefficient=0.35,
    max_normal_force_coefficient=10.0, max_load_factor=9.0,
)


def test_lag_step_bypass_when_tau_zero():
    a0 = np.array([1.0, 2.0, 3.0])
    cmd = np.array([10.0, 0.0, 0.0])
    out = lag_step(a0, cmd, dt=0.01, tau=0.0)
    np.testing.assert_allclose(out, cmd)


def test_lag_step_response_approaches_command():
    """Isolated step response: first-order lag → cmd with time constant tau."""
    tau = 0.2
    dt = 0.01
    cmd = np.array([10.0, 0.0, 0.0])
    a = np.zeros(3)
    history = []
    t = 0.0
    while t < 1.5:
        a = lag_step(a, cmd, dt, tau)
        history.append(a.copy())
        t += dt
    history = np.array(history)
    # After ~1 tau, ~63% of step; after ~5 tau, essentially settled.
    idx_1tau = int(round(tau / dt)) - 1
    assert 0.55 < history[idx_1tau, 0] / cmd[0] < 0.75
    assert abs(history[-1, 0] - cmd[0]) < 0.05


def test_demo_pn_still_hits_with_default_lag():
    """Demo scenario with tau=0.2 still intercepts; report degradation vs tau=0."""
    def run(tau: float):
        pursuer = PointMassEntity(
            name="pursuer",
            state=State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0]),
            vehicle=PURSUER_VEHICLE,
        )
        target = PointMassEntity(
            name="target",
            state=State(position=[7000.0, 400.0, 3300.0], velocity=[-200.0, 0.0, 0.0]),
            vehicle=TARGET_VEHICLE,
        )
        return Simulation(
            pursuer=pursuer,
            target=target,
            guidance_law=ProportionalNavigation(4.0),
            target_maneuver=NoManeuver(),
            config=SimulationConfig(
                dt=0.01, max_time=45.0, intercept_radius=5.0, autopilot_tau=tau
            ),
        ).run()

    r0 = run(0.0)
    r_lag = run(0.2)
    assert r0.hit and r_lag.hit
    # Lag should not improve miss vs ideal (allow tiny numerical noise).
    assert r_lag.miss_distance >= r0.miss_distance - 0.5
    # Stash delta for humans reading pytest -q output via assertion message.
    delta = r_lag.miss_distance - r0.miss_distance
    assert delta >= -0.5, f"unexpected improvement: delta={delta:.3f} m"


def test_miss_increases_monotonically_with_tau():
    # Demo lead geometry: miss rises smoothly with tau (hit tube still made).
    taus = [0.0, 0.1, 0.2, 0.35, 0.5]
    misses = []
    for tau in taus:
        pursuer = PointMassEntity(
            name="pursuer",
            state=State(position=[0.0, 0.0, 3000.0], velocity=[350.0, 0.0, 0.0]),
            vehicle=PURSUER_VEHICLE,
        )
        target = PointMassEntity(
            name="target",
            state=State(position=[7000.0, 400.0, 3300.0], velocity=[-200.0, 0.0, 0.0]),
            vehicle=TARGET_VEHICLE,
        )
        result = Simulation(
            pursuer=pursuer,
            target=target,
            guidance_law=ProportionalNavigation(4.0),
            target_maneuver=NoManeuver(),
            config=SimulationConfig(
                dt=0.01, max_time=45.0, intercept_radius=5.0, autopilot_tau=tau
            ),
        ).run()
        misses.append(result.miss_distance)
    for i in range(len(misses) - 1):
        assert misses[i + 1] + 1e-9 >= misses[i], (
            f"miss not monotonic in tau: {list(zip(taus, misses))}"
        )
