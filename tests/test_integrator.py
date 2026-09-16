"""Analytic checks for the generic steppers, independent of vehicle models."""

import numpy as np
import pytest

from guidance_sim.physics.integrator import IntegratorType, integrate, integrate_state


def advance(state, acceleration, dt, method, interface):
    if interface == "flat":
        return integrate_state(
            state,
            lambda y: np.concatenate((y[3:], acceleration(y[:3], y[3:]))),
            dt,
            method,
        )
    position, velocity = integrate(state[:3], state[3:], acceleration, dt, method)
    return np.concatenate((position, velocity))


@pytest.mark.parametrize("interface", ["flat", "position_velocity"])
@pytest.mark.parametrize(
    "method, ratio_bounds",
    [(IntegratorType.EULER, (1.8, 2.2)), (IntegratorType.RK4, (14.0, 18.0))],
)
def test_harmonic_oscillator_convergence_order(interface, method, ratio_bounds):
    # Unit frequency: x(t) = x0*cos(t) + v0*sin(t), independently per axis.
    initial = np.array([1.0, -2.0, 0.5, 0.3, 0.7, -1.0])
    duration = 2.0
    expected = np.concatenate((
        initial[:3] * np.cos(duration) + initial[3:] * np.sin(duration),
        -initial[:3] * np.sin(duration) + initial[3:] * np.cos(duration),
    ))
    errors = []
    for dt in (0.1, 0.05):
        state = initial.copy()
        for _ in range(round(duration / dt)):
            state = advance(state, lambda x, v: -x, dt, method, interface)
        errors.append(np.linalg.norm(state - expected))

    # Halving h should reduce global error by ~2 for Euler and ~16 for RK4.
    assert ratio_bounds[0] < errors[0] / errors[1] < ratio_bounds[1]


@pytest.mark.parametrize("interface", ["flat", "position_velocity"])
def test_rk4_free_fall_matches_analytic_solution_without_mutating_inputs(interface):
    initial = np.array([1.0, 2.0, 100.0, 3.0, -4.0, 5.0])
    original = initial.copy()
    acceleration = np.array([0.0, 0.0, -9.80665])
    state = initial
    dt = 0.125
    for _ in range(16):
        state = advance(
            state, lambda x, v: acceleration, dt, IntegratorType.RK4, interface
        )

    duration = 2.0
    expected = np.concatenate((
        initial[:3] + duration * initial[3:] + 0.5 * acceleration * duration**2,
        initial[3:] + acceleration * duration,
    ))
    np.testing.assert_allclose(state, expected, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(initial, original)
    np.testing.assert_array_equal(acceleration, [0.0, 0.0, -9.80665])
