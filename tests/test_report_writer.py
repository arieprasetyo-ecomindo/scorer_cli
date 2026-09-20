from app.report_writer import write_markdown_report

JEV_SCORES = {
    "coupling": {"score_0_10": 7.7, "level": 3, "level_label": "Good", "confidence": 0.9},
    "circular_dependencies": {"score_0_10": 10.0, "level": 4, "level_label": "Excellent", "confidence": 1.0},
    "dependency_depth": {"score_0_10": 9.8, "level": 4, "level_label": "Excellent", "confidence": 0.9},
    "cyclomatic_complexity": {"score_0_10": 6.5, "level": 3, "level_label": "Fair", "confidence": 0.6},
    "function_size_discipline": {"score_0_10": 10.0, "level": 4, "level_label": "Excellent", "confidence": 1.0},
    "betweenness_centrality": {"score_0_10": 9.5, "level": 4, "level_label": "Excellent", "confidence": 0.85},
}

SPEC_SCORES = {
    "weakest_dimension": {"choice": "Traceability", "confidence": 0.23},
    "clarity_testability": {"score_0_10": 8.4, "answer": "yes", "confidence": 0.62},
    "scope_boundary": {"score_0_10": 8.9, "answer": "yes", "confidence": 0.94},
    "internal_consistency": {"score_0_10": 8.3, "answer": "yes", "confidence": 0.52},
    "traceability": {"score_0_10": 2.4, "answer": "no", "confidence": 0.48},
    "substance_over_polish": {"score_0_10": 8.8, "answer": "yes", "confidence": 0.86},
}

WEIGHTS = {"structure": 0.5, "spec": 0.5}


def test_write_markdown_report_includes_all_sections(tmp_path):
    path = write_markdown_report(
        "team-x", tmp_path, JEV_SCORES, SPEC_SCORES, "## Summary\n\nSolid.", ["a flag"], WEIGHTS
    )
    text = path.read_text()

    assert path == tmp_path / "team-x.md"
    assert "# Hackathon Submission Report: team-x" in text
    assert "![Score Breakdown](team-x_chart.png)" in text
    assert (tmp_path / "team-x_chart.png").exists()
    assert "## Structure Quality (Code Metrics)" in text
    assert "## Spec Quality (SDD Scoring)" in text
    assert "Combined Score:" in text
    assert "## Summary" in text
    assert "Solid." in text
    assert "- a flag" in text


def test_write_markdown_report_no_red_flags(tmp_path):
    path = write_markdown_report("team-x", tmp_path, JEV_SCORES, None, "## Summary\n\nOk.", [], WEIGHTS)
    text = path.read_text()
    assert "None detected." in text
    assert "## Spec Quality" not in text
    assert "Combined Score:" not in text
