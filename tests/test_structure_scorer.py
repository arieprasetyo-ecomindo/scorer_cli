from pathlib import Path

import pytest

from app.metrics import (
    build_file_graph,
    compute_complexity_metrics_from_zip,
    compute_graph_metrics,
    load_graph,
)
from app.structure_scorer import (
    STRUCTURE_WEIGHTS,
    score_betweenness_centrality,
    score_circular_dependencies,
    score_coupling,
    score_cyclomatic_complexity,
    score_dependency_depth,
    score_function_size_discipline,
    score_structure,
    weighted_structure_total,
)

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "sample_team_phoenix"


def graph_metrics(**overrides) -> dict:
    base = {
        "avg_fan_in": 1.0,
        "max_fan_in": 1.0,
        "avg_fan_out": 1.0,
        "max_fan_out": 1.0,
        "circular_dependencies": [],
        "node_count": 100,
        "longest_dependency_path": 1,
        "avg_betweenness_centrality": 0.0,
        "max_betweenness_centrality": 0.0,
    }
    base.update(overrides)
    return base


def complexity_metrics(**overrides) -> dict:
    base = {
        "avg_cyclomatic_complexity": 0.0,
        "total_functions": 0,
        "functions_above_complexity_threshold": [],
        "avg_function_length_nloc": 0.0,
        "avg_parameter_count": 0.0,
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "max_val,expected_level",
    [(2, 4), (3, 3), (5, 2), (8, 1), (11, 0)],
)
def test_coupling_ratio_buckets(max_val, expected_level):
    m = graph_metrics(avg_fan_in=1, max_fan_in=max_val, avg_fan_out=1, max_fan_out=max_val)
    assert score_coupling(m) == expected_level


def test_coupling_forced_critical_on_high_average_even_if_ratio_is_low():
    m = graph_metrics(avg_fan_in=3, max_fan_in=3, avg_fan_out=3, max_fan_out=3)
    assert score_coupling(m) == 0


def test_coupling_zero_edges_is_excellent():
    m = graph_metrics(avg_fan_in=0, max_fan_in=0, avg_fan_out=0, max_fan_out=0)
    assert score_coupling(m) == 4


@pytest.mark.parametrize(
    "count,expected_level",
    [(0, 4), (1, 3), (2, 2), (3, 2), (4, 1), (6, 1), (7, 0)],
)
def test_circular_dependencies_buckets(count, expected_level):
    m = graph_metrics(circular_dependencies=[["a", "b", "a"]] * count)
    assert score_circular_dependencies(m) == expected_level


def test_dependency_depth_shallow_is_excellent():
    m = graph_metrics(node_count=100, longest_dependency_path=1)
    assert score_dependency_depth(m) == 4


def test_dependency_depth_deep_is_critical():
    m = graph_metrics(node_count=100, longest_dependency_path=60)
    assert score_dependency_depth(m) == 0


def test_dependency_depth_single_node_uses_baseline_of_one():
    m = graph_metrics(node_count=1, longest_dependency_path=1)
    assert score_dependency_depth(m) == 4


def test_cyclomatic_complexity_low_avg_no_outliers_is_excellent():
    c = complexity_metrics(avg_cyclomatic_complexity=3, total_functions=10)
    assert score_cyclomatic_complexity(c) == 4


def test_cyclomatic_complexity_worse_of_avg_and_pct_wins():
    # low avg CCN, but 20% of functions are above threshold -> pct signal dominates
    c = complexity_metrics(
        avg_cyclomatic_complexity=3,
        total_functions=10,
        functions_above_complexity_threshold=[{"name": "f", "file": "x.py", "ccn": 15, "nloc": 5}] * 2,
    )
    assert score_cyclomatic_complexity(c) == 1


def test_cyclomatic_complexity_no_functions_is_excellent():
    c = complexity_metrics(avg_cyclomatic_complexity=0, total_functions=0)
    assert score_cyclomatic_complexity(c) == 4


def test_function_size_worse_of_nloc_and_params_wins():
    # small functions but too many params
    c = complexity_metrics(avg_function_length_nloc=10, avg_parameter_count=9)
    assert score_function_size_discipline(c) == 0


def test_betweenness_no_bottleneck_is_excellent():
    m = graph_metrics(avg_betweenness_centrality=0.1, max_betweenness_centrality=0.2)
    assert score_betweenness_centrality(m) == 4


def test_betweenness_severe_bottleneck_is_critical():
    m = graph_metrics(avg_betweenness_centrality=0.1, max_betweenness_centrality=4.0)
    assert score_betweenness_centrality(m) == 0


def test_betweenness_zero_average_is_excellent():
    m = graph_metrics(avg_betweenness_centrality=0.0, max_betweenness_centrality=0.0)
    assert score_betweenness_centrality(m) == 4


def test_score_structure_shape_and_scale():
    result = score_structure(graph_metrics(), complexity_metrics())
    assert set(result.keys()) == set(STRUCTURE_WEIGHTS.keys())
    for answer in result.values():
        assert answer["score_0_10"] in (0, 2.5, 5, 7.5, 10)
        assert 0 <= answer["level"] <= 4
        assert isinstance(answer["level_label"], str)


def test_score_structure_is_deterministic():
    g, c = graph_metrics(avg_fan_in=1, max_fan_in=5), complexity_metrics(avg_cyclomatic_complexity=6)
    assert score_structure(g, c) == score_structure(g, c)


def test_weighted_structure_total_all_excellent():
    result = score_structure(graph_metrics(), complexity_metrics())
    assert weighted_structure_total(result) == pytest.approx(10.0)


def test_smoke_on_real_sample_metrics():
    raw = load_graph(FIXTURE_DIR / "graph.json")
    g = build_file_graph(raw)
    gm = compute_graph_metrics(g)
    cm = compute_complexity_metrics_from_zip(FIXTURE_DIR / "source.zip")

    result = score_structure(gm, cm)
    assert set(result.keys()) == set(STRUCTURE_WEIGHTS.keys())
    total = weighted_structure_total(result)
    assert 0 <= total <= 10
