"""Tests for the shadow-mode classical vs RL comparison harness."""

from __future__ import annotations

from pathlib import Path

from guidance_sim.evaluation.shadow_compare import (
    GUIDANCE_MODES,
    ShadowComparisonReport,
    ShadowRunMetrics,
    format_markdown_report,
    load_rl_baseline_pointer,
    run_classical_case,
    write_shadow_report,
)
from guidance_sim.rl.training import (
    FIXED_EVALUATION_CASES,
    GROUP_A_MANEUVERS,
    GROUP_B_MANEUVERS,
    PPOTrainingConfig,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_POINTER = REPO_ROOT / "outputs" / "CURRENT_RL_BASELINE.json"


def test_fixed_eval_matrix_matches_rl_groups():
    """Shadow scope must be exactly the nine frozen RL eval cases."""

    assert len(FIXED_EVALUATION_CASES) == 9
    group_a = [c for c in FIXED_EVALUATION_CASES if c.maneuver in GROUP_A_MANEUVERS]
    group_b = [c for c in FIXED_EVALUATION_CASES if c.maneuver in GROUP_B_MANEUVERS]
    assert len(group_a) == 6
    assert len(group_b) == 3
    assert {c.maneuver for c in group_a} == {"none", "weave"}
    assert {c.maneuver for c in group_b} == {"constant_turn"}
    assert PPOTrainingConfig().max_time == 25.0


def test_baseline_pointer_is_evasive_zemtgo10_seed8_checkpoint_08():
    """Promoted 2026-09-16: fresh seed, precision-bonus + low-noise fine-tune.

    88.7% n=300 vs PN's 72.7% (McNemar p=9e-8); see NOTES.md 2026-09-16.
    """

    pointer = load_rl_baseline_pointer(BASELINE_POINTER)
    assert pointer["model_path"].endswith(
        "evasive_zemtgo10_seed8/checkpoints/rl_checkpoint_08.zip"
    )
    assert pointer["use_target_turn_rate_obs"] is False
    assert pointer["tracking_enabled"] is True
    assert pointer["observation_dim"] == 12
    model = REPO_ROOT / pointer["model_path"]
    assert model.is_file()


def test_classical_pn_hits_no_maneuver_center():
    case = next(c for c in FIXED_EVALUATION_CASES if c.name == "no_maneuver_center")
    config = PPOTrainingConfig().simulation_config()
    metrics = run_classical_case(case, "PN", config=config, seed=91_000)
    assert metrics.guidance_mode == "PN"
    assert metrics.group == "A"
    assert metrics.hit
    assert metrics.miss_distance_m <= config.intercept_radius
    assert metrics.time_s < config.max_time
    assert metrics.peak_cmd_lateral_m_s2 >= 0.0
    assert metrics.peak_achieved_lateral_m_s2 >= 0.0


def test_classical_pn_misses_constant_turn_under_25s_budget():
    """Group B time-budget ceiling: PN does not hit 3 g turn in 25 s."""

    case = next(c for c in FIXED_EVALUATION_CASES if c.name == "constant_turn_left_3g")
    config = PPOTrainingConfig().simulation_config()
    metrics = run_classical_case(case, "PN", config=config, seed=91_000 + 3)
    assert metrics.group == "B"
    assert not metrics.hit
    assert metrics.outcome == "timeout"
    assert metrics.time_s >= config.max_time - 1e-6
    # Documented classical PN ceiling ~973 m on this case.
    assert 900.0 < metrics.miss_distance_m < 1100.0


def test_markdown_and_artifacts_from_synthetic_report(tmp_path: Path):
    rows = (
        ShadowRunMetrics(
            scenario="no_maneuver_center",
            group="A",
            maneuver="none",
            guidance_mode="PN",
            hit=True,
            outcome="hit",
            miss_distance_m=3.0,
            time_s=16.0,
            peak_cmd_lateral_m_s2=40.0,
            mean_cmd_lateral_m_s2=12.0,
            peak_achieved_lateral_m_s2=35.0,
        ),
        ShadowRunMetrics(
            scenario="no_maneuver_center",
            group="A",
            maneuver="none",
            guidance_mode="RL",
            hit=True,
            outcome="hit",
            miss_distance_m=3.1,
            time_s=16.2,
            peak_cmd_lateral_m_s2=50.0,
            mean_cmd_lateral_m_s2=15.0,
            peak_achieved_lateral_m_s2=40.0,
        ),
        ShadowRunMetrics(
            scenario="constant_turn_left_3g",
            group="B",
            maneuver="constant_turn",
            guidance_mode="PN",
            hit=False,
            outcome="timeout",
            miss_distance_m=973.0,
            time_s=25.0,
            peak_cmd_lateral_m_s2=80.0,
            mean_cmd_lateral_m_s2=40.0,
            peak_achieved_lateral_m_s2=70.0,
        ),
        ShadowRunMetrics(
            scenario="constant_turn_left_3g",
            group="B",
            maneuver="constant_turn",
            guidance_mode="RL",
            hit=False,
            outcome="timeout",
            miss_distance_m=832.0,
            time_s=25.0,
            peak_cmd_lateral_m_s2=90.0,
            mean_cmd_lateral_m_s2=45.0,
            peak_achieved_lateral_m_s2=80.0,
        ),
    )
    report = ShadowComparisonReport(
        cases=rows,
        guidance_modes=("PN", "RL"),
        baseline_pointer=str(BASELINE_POINTER),
        baseline_model_path="outputs/observation_target_turn_rate/checkpoints/rl_checkpoint_05.zip",
        max_time_s=25.0,
        dt_s=0.02,
        n_scenarios=2,
        eval_seed=91_000,
    )
    md = format_markdown_report(report)
    assert "Shadow-mode guidance comparison" in md
    assert "constant_turn_left_3g" in md
    assert "HIT / 3.0 m" in md
    assert "MISS / 832.0 m" in md
    assert "Group B (ConstantTurn)" in md
    assert "Where RL beats classical" in md

    paths = write_shadow_report(report, output_dir=tmp_path)
    assert paths["markdown"].is_file()
    assert paths["json"].is_file()
    assert paths["csv"].is_file()
    csv_text = paths["csv"].read_text(encoding="utf-8")
    assert "peak_cmd_lateral_m_s2" in csv_text
    assert "832.0" in csv_text


def test_guidance_modes_contract():
    assert GUIDANCE_MODES == ("PN", "APN", "OGL", "RL")
