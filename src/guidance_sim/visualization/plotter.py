"""
Trajectory and diagnostics plots for SimulationResult.

Uses the Agg backend so scripts/tests work headless.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  # registers 3D projection

from guidance_sim.simulation.engine import SimulationResult


def _ensure_parent(out_path: str) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _range_history(result: SimulationResult) -> np.ndarray:
    return np.linalg.norm(result.target_trajectory - result.pursuer_trajectory, axis=1)


def _pursuer_speed(result: SimulationResult) -> np.ndarray:
    """Approximate speed from position history (central differences)."""
    times = result.times
    pos = result.pursuer_trajectory
    if len(times) < 2:
        return np.zeros(len(times))
    # np.gradient handles uneven endpoints; divide by dt along each axis.
    vx = np.gradient(pos[:, 0], times)
    vy = np.gradient(pos[:, 1], times)
    vz = np.gradient(pos[:, 2], times)
    return np.sqrt(vx * vx + vy * vy + vz * vz)


def plot_trajectory_3d(
    result: SimulationResult,
    out_path: str,
    title: str = "",
) -> None:
    path = _ensure_parent(out_path)
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    p = result.pursuer_trajectory
    tgt = result.target_trajectory
    ax.plot(p[:, 0], p[:, 1], p[:, 2], label="pursuer", color="C0", lw=1.8)
    ax.plot(tgt[:, 0], tgt[:, 1], tgt[:, 2], label="target", color="C3", lw=1.5)
    ax.scatter(p[0, 0], p[0, 1], p[0, 2], c="C0", marker="o", s=40, label="pursuer start")
    ax.scatter(tgt[0, 0], tgt[0, 1], tgt[0, 2], c="C3", marker="o", s=40, label="target start")
    if result.hit:
        ax.scatter(
            p[-1, 0], p[-1, 1], p[-1, 2],
            c="green", marker="*", s=120, label="intercept",
        )

    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z (altitude) [m]")
    ax.set_title(title or "3D trajectories")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_diagnostics(result: SimulationResult, out_path: str) -> None:
    path = _ensure_parent(out_path)
    t = result.times
    ranges = _range_history(result)
    speeds = _pursuer_speed(result)
    altitude = result.pursuer_trajectory[:, 2]
    cmd_mag = np.linalg.norm(result.pursuer_accel_cmd, axis=1)
    ach_mag = np.linalg.norm(result.pursuer_accel_achieved, axis=1)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), sharex=True)

    axes[0, 0].plot(t, ranges, color="C0")
    axes[0, 0].set_ylabel("range [m]")
    axes[0, 0].set_title("Range vs t")
    axes[0, 0].grid(True, alpha=0.3)

    axes[0, 1].plot(t, speeds, color="C1")
    axes[0, 1].set_ylabel("speed [m/s]")
    axes[0, 1].set_title("Pursuer speed vs t")
    axes[0, 1].grid(True, alpha=0.3)

    axes[1, 0].plot(t, altitude, color="C2")
    axes[1, 0].set_xlabel("t [s]")
    axes[1, 0].set_ylabel("altitude [m]")
    axes[1, 0].set_title("Pursuer altitude vs t")
    axes[1, 0].grid(True, alpha=0.3)

    axes[1, 1].plot(t, cmd_mag, label="commanded", color="C0", lw=1.5)
    axes[1, 1].plot(t, ach_mag, label="achieved", color="C3", lw=1.2, ls="--")
    axes[1, 1].set_xlabel("t [s]")
    axes[1, 1].set_ylabel("|a_lat| [m/s²]")
    axes[1, 1].set_title("Commanded vs achieved lateral accel")
    axes[1, 1].legend(loc="best", fontsize=8)
    axes[1, 1].grid(True, alpha=0.3)

    fig.suptitle(
        f"Diagnostics  hit={result.hit}  miss={result.miss_distance:.2f} m",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def animate_3d(result: SimulationResult, out_path: str, fps: int = 30) -> None:
    path = _ensure_parent(out_path)
    p = result.pursuer_trajectory
    tgt = result.target_trajectory
    n = len(result.times)
    # Subsample so GIF length stays reasonable (~fps * duration_cap).
    max_frames = max(fps * 8, 60)
    step = max(1, n // max_frames)
    indices = np.arange(0, n, step)
    if indices[-1] != n - 1:
        indices = np.append(indices, n - 1)

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    all_pts = np.vstack([p, tgt])
    pad = 200.0
    ax.set_xlim(all_pts[:, 0].min() - pad, all_pts[:, 0].max() + pad)
    ax.set_ylim(all_pts[:, 1].min() - pad, all_pts[:, 1].max() + pad)
    ax.set_zlim(all_pts[:, 2].min() - pad, all_pts[:, 2].max() + pad)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    ax.set_title("3D intercept animation")

    (pursuer_line,) = ax.plot([], [], [], color="C0", lw=2, label="pursuer")
    (target_line,) = ax.plot([], [], [], color="C3", lw=1.5, label="target")
    (pursuer_pt,) = ax.plot([], [], [], "o", color="C0", ms=6)
    (target_pt,) = ax.plot([], [], [], "o", color="C3", ms=6)
    ax.legend(loc="upper left", fontsize=8)

    def _init():
        pursuer_line.set_data_3d([], [], [])
        target_line.set_data_3d([], [], [])
        pursuer_pt.set_data_3d([], [], [])
        target_pt.set_data_3d([], [], [])
        return pursuer_line, target_line, pursuer_pt, target_pt

    def _update(frame_i: int):
        i = int(indices[frame_i])
        pursuer_line.set_data_3d(p[: i + 1, 0], p[: i + 1, 1], p[: i + 1, 2])
        target_line.set_data_3d(tgt[: i + 1, 0], tgt[: i + 1, 1], tgt[: i + 1, 2])
        pursuer_pt.set_data_3d([p[i, 0]], [p[i, 1]], [p[i, 2]])
        target_pt.set_data_3d([tgt[i, 0]], [tgt[i, 1]], [tgt[i, 2]])
        return pursuer_line, target_line, pursuer_pt, target_pt

    anim = animation.FuncAnimation(
        fig,
        _update,
        init_func=_init,
        frames=len(indices),
        interval=1000 / fps,
        blit=False,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
