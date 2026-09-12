"""Read-only evaluation and reporting helpers (no training)."""

from guidance_sim.evaluation.shadow_compare import (
    GUIDANCE_MODES,
    ShadowComparisonReport,
    ShadowRunMetrics,
    format_markdown_report,
    load_rl_baseline_pointer,
    run_shadow_comparison,
    write_shadow_report,
)

__all__ = [
    "GUIDANCE_MODES",
    "ShadowComparisonReport",
    "ShadowRunMetrics",
    "format_markdown_report",
    "load_rl_baseline_pointer",
    "run_shadow_comparison",
    "write_shadow_report",
]
