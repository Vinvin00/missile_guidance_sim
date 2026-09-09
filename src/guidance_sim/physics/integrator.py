"""
Generic RK4 integrator for a second-order 3D kinematic system:

    dx/dt = v
    dv/dt = a(x, v)

`accel_fn(position, velocity) -> acceleration` is evaluated at each
of the four RK4 stages, so gravity- and drag-driven acceleration
(which depend on altitude and speed) are integrated properly across
the step. The commanded lateral acceleration is expected to be
*frozen* for the duration of one step by the caller (entities.py) --
that's the standard zero-order-hold assumption for a guidance command
that's recomputed once per control-loop tick, not a limitation of the
integrator itself.

An Euler stepper is also provided for comparison/debugging.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable

import numpy as np

AccelFn = Callable[[np.ndarray, np.ndarray], np.ndarray]


class IntegratorType(str, Enum):
    EULER = "euler"
    RK4 = "rk4"


def euler_step(position: np.ndarray, velocity: np.ndarray, accel_fn: AccelFn, dt: float):
    accel = accel_fn(position, velocity)
    new_position = position + velocity * dt
    new_velocity = velocity + accel * dt
    return new_position, new_velocity


def rk4_step(position: np.ndarray, velocity: np.ndarray, accel_fn: AccelFn, dt: float):
    k1_x = velocity
    k1_v = accel_fn(position, velocity)

    k2_x = velocity + 0.5 * dt * k1_v
    k2_v = accel_fn(position + 0.5 * dt * k1_x, velocity + 0.5 * dt * k1_v)

    k3_x = velocity + 0.5 * dt * k2_v
    k3_v = accel_fn(position + 0.5 * dt * k2_x, velocity + 0.5 * dt * k2_v)

    k4_x = velocity + dt * k3_v
    k4_v = accel_fn(position + dt * k3_x, velocity + dt * k3_v)

    new_position = position + (dt / 6.0) * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
    new_velocity = velocity + (dt / 6.0) * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)
    return new_position, new_velocity


def integrate(
    position: np.ndarray,
    velocity: np.ndarray,
    accel_fn: AccelFn,
    dt: float,
    method: IntegratorType = IntegratorType.RK4,
):
    if method == IntegratorType.EULER:
        return euler_step(position, velocity, accel_fn, dt)
    elif method == IntegratorType.RK4:
        return rk4_step(position, velocity, accel_fn, dt)
    raise ValueError(f"Unknown integrator method: {method}")
