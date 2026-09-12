#!/usr/bin/env python3
"""Run PN/APN/OGL vs frozen RL baseline on the fixed eval matrix.

Read-only: does not train or modify CURRENT_RL_BASELINE.json.

  .venv/bin/python scripts/run_shadow_comparison.py
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from guidance_sim.evaluation.shadow_compare import (
    run_shadow_comparison,
    write_shadow_report,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repo_root / "outputs" / "shadow_comparison",
        help="Directory for markdown/JSON/CSV artifacts",
    )
    parser.add_argument(
        "--baseline-pointer",
        type=Path,
        default=repo_root / "outputs" / "CURRENT_RL_BASELINE.json",
        help="Path to CURRENT_RL_BASELINE.json (read-only)",
    )
    parser.add_argument(
        "--skip-rl",
        action="store_true",
        help="Classical-only matrix (for fast smoke checks)",
    )
    args = parser.parse_args()

    print("Running shadow comparison (PN / APN / OGL / RL)…")
    report = run_shadow_comparison(
        baseline_pointer_path=args.baseline_pointer,
        repo_root=repo_root,
        include_rl=not args.skip_rl,
    )
    paths = write_shadow_report(report, output_dir=args.output_dir)
    print(f"Wrote {paths['markdown']}")
    print(f"Wrote {paths['json']}")
    print(f"Wrote {paths['csv']}")

    # Compact console preview of the hit/miss table.
    by_scenario: dict[str, dict[str, object]] = {}
    for row in report.cases:
        bucket = by_scenario.setdefault(row.scenario, {"group": row.group})
        tag = "HIT" if row.hit else "MISS"
        bucket[row.guidance_mode] = f"{tag}/{row.miss_distance_m:.1f}m"
    modes = report.guidance_modes
    print()
    print("scenario".ljust(28), "G", *[m.ljust(14) for m in modes], sep="  ")
    for name, bucket in by_scenario.items():
        cells = [str(bucket.get(m, "—")).ljust(14) for m in modes]
        print(name.ljust(28), bucket["group"], *cells, sep="  ")


if __name__ == "__main__":
    main()
