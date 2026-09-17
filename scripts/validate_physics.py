"""
Envelope sweep (Step 2) + guidance comparison (Step 3).

Axes: lateral offset (target y) × initial range (target x) on the demo IC family.

Usage:
    python scripts/validate_physics.py              # PN / NoManeuver (Step 2)
    python scripts/validate_physics.py --compare    # PN/APN/OGL × NoManeuver/Weave
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.factories import classical_law_factories
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity, State, VehicleParams
from guidance_sim.physics.maneuvers import ManeuverProfile, NoManeuver, SinusoidalWeave
from guidance_sim.simulation.engine import Simulation, SimulationConfig

HIT_THRESHOLD_M = 5.0
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
PURSUER_POS0 = np.array([0.0, 0.0, 3000.0])
PURSUER_VEL0 = np.array([350.0, 0.0, 0.0])
TARGET_ALT = 3300.0
TARGET_VEL0 = np.array([-200.0, 0.0, 0.0])
NAV_CONSTANT = 4.0
SWEEP_DT = 0.02
SWEEP_MAX_TIME = 45.0


def classify_hit(miss_distance: float, threshold_m: float = HIT_THRESHOLD_M) -> bool:
    return float(miss_distance) <= float(threshold_m)


GuidanceFactory = Callable[[PointMassEntity], GuidanceLaw]
ManeuverFactory = Callable[[], ManeuverProfile]


def run_engagement(
    lateral_offset_m: float,
    initial_range_m: float,
    *,
    guidance_factory: Optional[GuidanceFactory] = None,
    maneuver_factory: Optional[ManeuverFactory] = None,
    dt: float = SWEEP_DT,
    max_time: float = SWEEP_MAX_TIME,
    intercept_radius: float = HIT_THRESHOLD_M,
    autopilot_tau: float = 0.0,
) -> float:
    """
    One engagement; returns miss distance (m).

    Default guidance/maneuver: PN + NoManeuver (Step 2). Factories receive
    the live target entity so APN/OGL can bind truth a_target_est.
    """
    if guidance_factory is None:
        guidance_factory = lambda _t: ProportionalNavigation(NAV_CONSTANT)
    if maneuver_factory is None:
        maneuver_factory = NoManeuver

    pursuer = PointMassEntity(
        name="pursuer",
        state=State(position=PURSUER_POS0.copy(), velocity=PURSUER_VEL0.copy()),
        vehicle=PURSUER_VEHICLE,
    )
    target = PointMassEntity(
        name="target",
        state=State(
            position=[float(initial_range_m), float(lateral_offset_m), TARGET_ALT],
            velocity=TARGET_VEL0.copy(),
        ),
        vehicle=TARGET_VEHICLE,
    )
    result = Simulation(
        pursuer=pursuer,
        target=target,
        guidance_law=guidance_factory(target),
        target_maneuver=maneuver_factory(),
        config=SimulationConfig(
            dt=dt,
            max_time=max_time,
            intercept_radius=intercept_radius,
            autopilot_tau=autopilot_tau,
        ),
    ).run()
    return float(result.miss_distance)


@dataclass
class SweepResult:
    lateral_offsets: np.ndarray
    initial_ranges: np.ndarray
    miss_distances: np.ndarray
    hits: np.ndarray
    threshold_m: float
    label: str = ""

    @property
    def hit_rate(self) -> float:
        return float(np.mean(self.hits))


def run_sweep(
    lateral_offsets: np.ndarray,
    initial_ranges: np.ndarray,
    *,
    threshold_m: float = HIT_THRESHOLD_M,
    dt: float = SWEEP_DT,
    max_time: float = SWEEP_MAX_TIME,
    guidance_factory: Optional[GuidanceFactory] = None,
    maneuver_factory: Optional[ManeuverFactory] = None,
    autopilot_tau: float = 0.0,
    label: str = "",
) -> SweepResult:
    offsets = np.asarray(lateral_offsets, dtype=float).reshape(-1)
    ranges = np.asarray(initial_ranges, dtype=float).reshape(-1)
    miss = np.empty((len(offsets), len(ranges)), dtype=float)
    for j, y_off in enumerate(offsets):
        for i, x_rng in enumerate(ranges):
            miss[j, i] = run_engagement(
                y_off,
                x_rng,
                dt=dt,
                max_time=max_time,
                intercept_radius=threshold_m,
                guidance_factory=guidance_factory,
                maneuver_factory=maneuver_factory,
                autopilot_tau=autopilot_tau,
            )
    hits = np.vectorize(lambda m: classify_hit(m, threshold_m))(miss).astype(bool)
    return SweepResult(
        lateral_offsets=offsets,
        initial_ranges=ranges,
        miss_distances=miss,
        hits=hits,
        threshold_m=threshold_m,
        label=label,
    )


def describe_boundary(result: SweepResult) -> str:
    header = f"[{result.label}] " if result.label else ""
    lines = [
        f"{header}Hit rate: {100.0 * result.hit_rate:.1f}% "
        f"({int(result.hits.sum())}/{result.hits.size})  "
        f"threshold={result.threshold_m:.1f} m",
    ]
    boundary_notes = []
    for i, rng in enumerate(result.initial_ranges):
        col = result.hits[:, i]
        if not np.any(col):
            boundary_notes.append(f"  range={rng:.0f} m: all miss")
            continue
        if np.all(col):
            boundary_notes.append(
                f"  range={rng:.0f} m: all hit (offset ≤ {result.lateral_offsets[-1]:.0f} m)"
            )
            continue
        hit_idxs = np.where(col)[0]
        max_hit_offset = float(result.lateral_offsets[hit_idxs.max()])
        miss_above = [
            float(result.lateral_offsets[j])
            for j in range(hit_idxs.max() + 1, len(result.lateral_offsets))
            if not col[j]
        ]
        if miss_above:
            boundary_notes.append(
                f"  range={rng:.0f} m: hit up to offset≈{max_hit_offset:.0f} m, "
                f"miss by {miss_above[0]:.0f} m"
            )
        else:
            boundary_notes.append(
                f"  range={rng:.0f} m: hit up to offset≈{max_hit_offset:.0f} m"
            )

    if len(boundary_notes) > 7:
        mid = len(boundary_notes) // 2
        shown = (
            boundary_notes[:2]
            + ["  ..."]
            + [boundary_notes[mid]]
            + ["  ..."]
            + boundary_notes[-2:]
        )
    else:
        shown = boundary_notes
    lines.append("Boundary (hit→miss vs lateral offset at fixed range):")
    lines.extend(shown)
    return "\n".join(lines)


def plot_heatmap(result: SweepResult, out_path: str, title: str = "") -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 6))
    data = result.hits.astype(float)
    x = result.initial_ranges
    y = result.lateral_offsets
    if len(x) > 1 and len(y) > 1:
        dx = 0.5 * (x[1] - x[0])
        dy = 0.5 * (y[1] - y[0])
        extent = (x[0] - dx, x[-1] + dx, y[0] - dy, y[-1] + dy)
    else:
        extent = None
    im = ax.imshow(
        data,
        origin="lower",
        aspect="auto",
        cmap="RdYlGn",
        vmin=0.0,
        vmax=1.0,
        extent=extent,
        interpolation="nearest",
    )
    cbar = fig.colorbar(im, ax=ax, ticks=[0, 1])
    cbar.ax.set_yticklabels(["miss", "hit"])
    ax.set_xlabel("initial range (target x) [m]")
    ax.set_ylabel("lateral offset (target y) [m]")
    ax.set_title(
        title
        or (
            f"{result.label or 'envelope'}  hit≤{result.threshold_m:.0f} m  "
            f"rate={100.0 * result.hit_rate:.0f}%"
        )
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_comparison_grid(
    results: list[SweepResult],
    out_path: str,
    nrows: int,
    ncols: int,
) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)
    for ax, result in zip(axes.ravel(), results):
        x = result.initial_ranges
        y = result.lateral_offsets
        dx = 0.5 * (x[1] - x[0]) if len(x) > 1 else 1.0
        dy = 0.5 * (y[1] - y[0]) if len(y) > 1 else 1.0
        extent = (x[0] - dx, x[-1] + dx, y[0] - dy, y[-1] + dy)
        ax.imshow(
            result.hits.astype(float),
            origin="lower",
            aspect="auto",
            cmap="RdYlGn",
            vmin=0.0,
            vmax=1.0,
            extent=extent,
            interpolation="nearest",
        )
        ax.set_title(f"{result.label}\n{100.0 * result.hit_rate:.0f}% hit", fontsize=10)
        ax.set_xlabel("range [m]", fontsize=8)
        ax.set_ylabel("offset [m]", fontsize=8)
    for ax in axes.ravel()[len(results) :]:
        ax.axis("off")
    fig.suptitle(
        f"Guidance comparison (τ={COMPARE_TAU}s, hit≤{HIT_THRESHOLD_M:.0f} m)",
        fontsize=12,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def default_grid(n: int = 15) -> Tuple[np.ndarray, np.ndarray]:
    lateral_offsets = np.linspace(0.0, 8000.0, n)
    initial_ranges = np.linspace(2000.0, 13000.0, n)
    return lateral_offsets, initial_ranges


_CLASSICAL_FACTORIES = classical_law_factories(lambda target: target, pn_n=NAV_CONSTANT)
_pn_factory = _CLASSICAL_FACTORIES["PN"]
_apn_factory = _CLASSICAL_FACTORIES["APN"]
_ogl_factory = _CLASSICAL_FACTORIES["OGL"]


COMPARE_TAU = 0.2


def run_comparison(n: int = 8) -> list[SweepResult]:
    """PN/APN/OGL × NoManeuver/Weave with autopilot lag active."""
    offsets, ranges = default_grid(n=n)
    cases = [
        ("PN / NoManeuver", _pn_factory, NoManeuver),
        ("APN / NoManeuver", _apn_factory, NoManeuver),
        ("OGL / NoManeuver", _ogl_factory, NoManeuver),
        ("PN / Weave", _pn_factory, lambda: SinusoidalWeave(40.0, 0.25)),
        ("APN / Weave", _apn_factory, lambda: SinusoidalWeave(40.0, 0.25)),
        ("OGL / Weave", _ogl_factory, lambda: SinusoidalWeave(40.0, 0.25)),
    ]
    results: list[SweepResult] = []
    for label, gfac, mfac in cases:
        print(f"Running {label} ...")
        result = run_sweep(
            offsets,
            ranges,
            guidance_factory=gfac,
            maneuver_factory=mfac,
            autopilot_tau=COMPARE_TAU,
            label=label,
        )
        print(describe_boundary(result))
        results.append(result)
    return results


def _count_holes(result: SweepResult) -> int:
    holes = 0
    ny, nx = result.hits.shape
    for j in range(1, ny - 1):
        for i in range(1, nx - 1):
            if result.hits[j, i]:
                continue
            neighbors = [
                result.hits[j - 1, i],
                result.hits[j + 1, i],
                result.hits[j, i - 1],
                result.hits[j, i + 1],
            ]
            if all(neighbors):
                holes += 1
    return holes


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Sweep PN/APN/OGL × NoManeuver/Weave with autopilot_tau=0.2",
    )
    parser.add_argument("--n", type=int, default=None, help="Grid points per axis")
    args = parser.parse_args(argv)
    out_dir = Path(__file__).resolve().parent.parent / "outputs"

    if args.compare:
        n = args.n or 8
        results = run_comparison(n=n)
        # Summary table
        print("\n=== Hit-rate summary (tau=0.2) ===")
        for r in results:
            print(f"  {r.label:20s}  {100.0 * r.hit_rate:5.1f}%")
        plot_comparison_grid(
            results,
            str(out_dir / "validate_physics_compare.png"),
            nrows=2,
            ncols=3,
        )
        print(f"Wrote {out_dir / 'validate_physics_compare.png'}")
        return

    n = args.n or 15
    offsets, ranges = default_grid(n=n)
    print(
        "Sweep axes: lateral offset (target y) × initial range (target x)\n"
        f"Grid: {len(offsets)} × {len(ranges)}  dt={SWEEP_DT}  "
        f"threshold={HIT_THRESHOLD_M} m  tau=0 (legacy Step 2)"
    )
    result = run_sweep(offsets, ranges, autopilot_tau=0.0, label="PN / NoManeuver")
    print(describe_boundary(result))
    holes = _count_holes(result)
    if holes:
        print(f"WARNING: {holes} mid-envelope miss hole(s).")
    else:
        print("No mid-envelope miss holes detected (4-neighborhood).")
    out = out_dir / "validate_physics_heatmap.png"
    plot_heatmap(result, str(out))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
