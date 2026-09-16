#!/usr/bin/env python3
"""Paired hit-rate comparison of held-out eval JSONs against the PN baseline.

Every eval in this lineage runs the identical case list and seeds, so the
right test is McNemar's exact test on discordant pairs, not an unpaired
two-proportion z-test.

Usage:
    python scripts/compare_vs_pn.py outputs/precision_ft/*/eval300_cp*.json
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path


def mcnemar_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value for b vs c discordant pairs."""

    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(b, c) + 1)) / 2**n
    return min(1.0, 2.0 * tail)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evals", nargs="+", type=Path)
    parser.add_argument(
        "--pn", type=Path, default=Path("outputs/evasive_largeeval_300/pn_baseline.json")
    )
    args = parser.parse_args()

    pn = {case["name"]: case["hit"] for case in json.loads(args.pn.read_text())["cases"]}
    print(f"PN: {sum(pn.values())}/{len(pn)} ({100 * sum(pn.values()) / len(pn):.1f}%)")
    print(f"{'eval':60s} {'hits':>9s} {'rate':>6s} {'+rl':>4s} {'+pn':>4s} {'p':>8s} {'max miss':>8s}")
    for path in args.evals:
        cases = json.loads(path.read_text())["cases"]
        missing = [c["name"] for c in cases if c["name"] not in pn]
        if missing or len(cases) != len(pn):
            print(f"{str(path):60s} skipped: case set differs from PN baseline")
            continue
        hits = sum(c["hit"] for c in cases)
        rl_only = sum(c["hit"] and not pn[c["name"]] for c in cases)
        pn_only = sum(pn[c["name"]] and not c["hit"] for c in cases)
        worst = max(c["miss_distance_m"] for c in cases)
        print(
            f"{str(path):60s} {hits:4d}/{len(cases):<4d} {100 * hits / len(cases):5.1f}% "
            f"{rl_only:4d} {pn_only:4d} {mcnemar_p(rl_only, pn_only):8.2g} {worst:7.1f}m"
        )


if __name__ == "__main__":
    assert abs(mcnemar_p(10, 10) - 1.0) < 1e-12
    assert abs(mcnemar_p(0, 5) - 0.0625) < 1e-12
    main()
