import pytest

from app.chart_generator import _score_color, generate_score_chart

JEV_SCORES = {
    "coupling": {"score_0_10": 7.7},
    "circular_dependencies": {"score_0_10": 10.0},
    "dependency_depth": {"score_0_10": 9.8},
    "cyclomatic_complexity": {"score_0_10": 6.5},
    "function_size_discipline": {"score_0_10": 10.0},
    "betweenness_centrality": {"score_0_10": 9.5},
}

SPEC_SCORES = {
    "clarity_testability": {"score_0_10": 8.4},
    "scope_boundary": {"score_0_10": 8.9},
    "internal_consistency": {"score_0_10": 8.3},
    "traceability": {"score_0_10": 2.4},
    "substance_over_polish": {"score_0_10": 8.8},
}


def test_score_color_tiers():
    assert _score_color(2.0) != _score_color(5.0) != _score_color(9.0)


def test_generate_chart_with_both_sections(tmp_path):
    path = generate_score_chart("team-x", JEV_SCORES, SPEC_SCORES, tmp_path / "chart.png")
    assert path.exists()
    assert path.stat().st_size > 0


def test_generate_chart_structure_only(tmp_path):
    path = generate_score_chart("team-x", JEV_SCORES, None, tmp_path / "chart.png")
    assert path.exists()


def test_generate_chart_requires_some_scores(tmp_path):
    with pytest.raises(ValueError):
        generate_score_chart("team-x", None, None, tmp_path / "chart.png")
