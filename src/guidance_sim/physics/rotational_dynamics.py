"""
Rigid-body rotational kinematics and kinetics. Pure functions: state in,
derivative out.

Frames (the #1 source of 6-DOF bugs, so spelled out once, here):

- World W: the project's existing frame. x, y horizontal, z UP.
  Positions and the public `State` live here.
- Local-level N: NED-style companion to W, N = (x_W, -y_W, -z_W). It is
  right-handed, and gravity is +z_N. Attitude is expressed relative to N
  so that every aero/attitude formula is textbook aerospace (Stevens &
  Lewis, *Aircraft Control and Simulation*, ch. 1-2).
- Body B: FRD. x out the nose, y out the right wing, z down.

Quaternion convention: **Hamilton**, scalar-first `q = [w, x, y, z]`,
active rotation, `q_NB` maps body vectors into N: `v_N = R(q) v_B`.
Kinematics: `q_dot = 1/2 * q ⊗ [0, omega_B]` with omega the body-frame
rate of B relative to N. (JPL convention would flip the product order
and the handedness of the vector part. Do not mix sources.)

Identity quaternion = wings level, nose along +x_W.
"""

from __future__ import annotations

import numpy as np

# C_WN: N -> W. Its own inverse.
C_WN = np.diag([1.0, -1.0, -1.0])


def quat_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product a ⊗ b, scalar-first."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return np.array([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ])


def quat_normalize(q: np.ndarray) -> np.ndarray:
    return q / np.linalg.norm(q)


def quat_to_rotation_matrix(q: np.ndarray) -> np.ndarray:
    """R_NB (body -> N) from a unit Hamilton quaternion."""
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
        [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
    ])


def quat_from_euler(phi: float, theta: float, psi: float) -> np.ndarray:
    """q_NB from aerospace ZYX Euler angles (yaw psi, pitch theta, roll phi)."""
    cr, sr = np.cos(phi / 2), np.sin(phi / 2)
    cp, sp = np.cos(theta / 2), np.sin(theta / 2)
    cy, sy = np.cos(psi / 2), np.sin(psi / 2)
    return np.array([
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    ])


def quat_to_euler(q: np.ndarray) -> tuple[float, float, float]:
    """
    (phi, theta, psi) ZYX Euler angles from q_NB. Telemetry/logging only.
    The state stays a quaternion, so theta = ±90 deg (the Cobra's regime)
    is singular here but not in the dynamics.

    psi is heading measured from +x_W toward -y_W (positive clockwise seen
    from above in world z-up axes), because N's y axis is -y_W.
    """
    w, x, y, z = q
    phi = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    theta = np.arcsin(np.clip(2 * (w * y - x * z), -1.0, 1.0))
    psi = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return float(phi), float(theta), float(psi)


def body_to_world_matrix(q: np.ndarray) -> np.ndarray:
    """R_WB: body FRD -> world z-up. Columns are nose, right wing, belly in W."""
    return C_WN @ quat_to_rotation_matrix(q)


def quat_derivative(q: np.ndarray, omega_body: np.ndarray) -> np.ndarray:
    """q_dot = 1/2 q ⊗ [0, omega] (Hamilton, body rates)."""
    return 0.5 * quat_multiply(q, np.array([0.0, *omega_body]))


def angular_acceleration(
    inertia: np.ndarray,
    omega_body: np.ndarray,
    moment_body: np.ndarray,
    inertia_inv: np.ndarray | None = None,
) -> np.ndarray:
    """Euler's equations: solve I·w_dot + w × (I·w) = M for w_dot."""
    if inertia_inv is None:
        inertia_inv = np.linalg.inv(inertia)
    return inertia_inv @ (moment_body - np.cross(omega_body, inertia @ omega_body))


def inertia_tensor(ixx: float, iyy: float, izz: float, ixz: float = 0.0) -> np.ndarray:
    """
    Body-axis inertia matrix for an airframe symmetric about its x-z plane.
    Stevens & Lewis sign convention: the off-diagonal entry is -Ixz, where
    Ixz is the positive product of inertia they tabulate.
    """
    return np.array([
        [ixx, 0.0, -ixz],
        [0.0, iyy, 0.0],
        [-ixz, 0.0, izz],
    ])
