"""Deterministic structure (code quality) scoring from NetworkX + Lizard metrics.

No LLM/Jev involved here on purpose: every one of these 6 dimensions already has an
exact numeric rubric in docs/spec/rubrics.md (e.g. "avg CCN <= 4 -> Excellent"), so
classifying them is a lookup-table problem, not a judgment call. That keeps scoring
free, instant, and 100% reproducible. Jev is reserved for Spec Quality, where the
input is unstructured prose and genuine judgment is actually required.

Level order is ascending (index 0 = Critical ... index 4 = Excellent), matching the
labels in STRUCTURE_LEVEL_CRITERIA below.
"""

import math

STRUCTURE_LEVEL_CRITERIA: dict[str, list[str]] = {
    "coupling": [
        "Critical: extreme coupling, tangled mess (max fan-in/out > 10x avg or avg fan-in/out > 2.5)",
        "Poor: pervasive high coupling; most nodes densely interconnected (max fan-in/out > 7x avg)",
        "Fair: several high fan-in/fan-out nodes (5-7x avg) suggesting god-modules or tangled responsibility",
        "Good: moderate coupling; one or two hotspot nodes (3-4x avg) but not dominant",
        "Excellent: low, even coupling; max fan-in/out within ~2x average, no architectural hotspots",
    ],
    "circular_dependencies": [
        "Critical: more than 6 cycles, or cycles involving multiple core modules",
        "Poor: 4-6 cycles, or cycles spanning large portions of the graph",
        "Fair: 2-3 cycles, or one cycle involving a core module",
        "Good: one isolated cycle in a non-core area",
        "Excellent: zero cycles, perfect architectural discipline",
    ],
    "dependency_depth": [
        "Critical: longest path far exceeds baseline (~log(node_count) x 2), spaghetti-like with no clear layers",
        "Poor: path is 4-6x the baseline, excessively deep, hard to trace data flow",
        "Fair: path is 2-4x the baseline, notably deep chains, poor layering visible",
        "Good: path is 1.5-2x the baseline, reasonable depth",
        "Excellent: longest path is at or below the baseline, shallow and flat structure",
    ],
    "cyclomatic_complexity": [
        "Critical: avg CCN far exceeds 15, or over 25% of functions exceed CCN 10, with some functions above CCN 20",
        "Poor: avg CCN above 12, or over 15% of functions exceed CCN 10",
        "Fair: avg CCN between 7 and 12, or 5-15% of functions exceed CCN 10",
        "Good: avg CCN between 4 and 7, and under 5% of functions exceed CCN 10",
        "Excellent: avg CCN at or below 4, no function exceeds CCN 10",
    ],
    "function_size_discipline": [
        "Critical: avg function length far exceeds 100 NLOC, or avg parameter count far exceeds 8",
        "Poor: avg function length above 70 NLOC, or avg parameter count above 6",
        "Fair: avg function length between 40 and 70 NLOC, avg parameter count between 4 and 6",
        "Good: avg function length between 20 and 40 NLOC, avg parameter count between 3 and 4",
        "Excellent: avg function length at or below 20 NLOC, avg parameter count at or below 3",
    ],
    "betweenness_centrality": [
        "Critical: max/avg betweenness ratio above 30x, or severe multi-node bottlenecks spanning the whole system",
        "Poor: ratio between 15x and 30x, or multiple nodes at 10-15x average",
        "Fair: ratio between 6x and 15x, a pronounced single point of architectural failure",
        "Good: ratio between 3x and 6x; one or two nodes above average but plausibly legitimate (entry points, shared utilities)",
        "Excellent: max/avg ratio below 3x, no single point of failure, evenly distributed",
    ],
}

STRUCTURE_WEIGHTS: dict[str, float] = {
    "coupling": 0.21,
    "circular_dependencies": 0.17,
    "dependency_depth": 0.13,
    "cyclomatic_complexity": 0.21,
    "function_size_discipline": 0.13,
    "betweenness_centrality": 0.15,
}


def _bucket(value: float, breakpoints: list[float]) -> int:
    """Highest level (4..0) whose breakpoint value is >= the metric's value.

    breakpoints has 4 ascending thresholds for levels [4, 3, 2, 1]; anything above
    the last one is level 0.
    """
    for level, bp in zip((4, 3, 2, 1), breakpoints):
        if value <= bp:
            return level
    return 0


def score_coupling(graph_metrics: dict) -> int:
    avg_val = max(graph_metrics["avg_fan_in"], graph_metrics["avg_fan_out"])
    max_val = max(graph_metrics["max_fan_in"], graph_metrics["max_fan_out"])
    if avg_val > 2.5:
        return 0
    ratio = max_val / avg_val if avg_val > 0 else 0
    return _bucket(ratio, [2, 4, 7, 10])


def score_circular_dependencies(graph_metrics: dict) -> int:
    count = len(graph_metrics["circular_dependencies"])
    return _bucket(count, [0, 1, 3, 6])


def score_dependency_depth(graph_metrics: dict) -> int:
    node_count = graph_metrics["node_count"]
    baseline = math.log(node_count) * 2 if node_count > 1 else 1
    ratio = graph_metrics["longest_dependency_path"] / baseline
    return _bucket(ratio, [1, 2, 4, 6])


def score_cyclomatic_complexity(complexity_metrics: dict) -> int:
    avg = complexity_metrics["avg_cyclomatic_complexity"]
    total = complexity_metrics["total_functions"]
    pct_above = (
        len(complexity_metrics["functions_above_complexity_threshold"]) / total * 100
        if total > 0
        else 0
    )
    level_from_avg = _bucket(avg, [4, 7, 12, 15])
    level_from_pct = _bucket(pct_above, [0, 5, 15, 25])
    return min(level_from_avg, level_from_pct)


def score_function_size_discipline(complexity_metrics: dict) -> int:
    level_from_nloc = _bucket(complexity_metrics["avg_function_length_nloc"], [20, 40, 70, 100])
    level_from_params = _bucket(complexity_metrics["avg_parameter_count"], [3, 4, 6, 8])
    return min(level_from_nloc, level_from_params)


def score_betweenness_centrality(graph_metrics: dict) -> int:
    avg_b = graph_metrics["avg_betweenness_centrality"]
    max_b = graph_metrics["max_betweenness_centrality"]
    ratio = max_b / avg_b if avg_b > 0 else 0
    return _bucket(ratio, [3, 6, 15, 30])


_CLASSIFIERS = {
    "coupling": lambda g, c: score_coupling(g),
    "circular_dependencies": lambda g, c: score_circular_dependencies(g),
    "dependency_depth": lambda g, c: score_dependency_depth(g),
    "cyclomatic_complexity": lambda g, c: score_cyclomatic_complexity(c),
    "function_size_discipline": lambda g, c: score_function_size_discipline(c),
    "betweenness_centrality": lambda g, c: score_betweenness_centrality(g),
}


def score_structure(graph_metrics: dict, complexity_metrics: dict) -> dict[str, dict]:
    """Classify all 6 structure dimensions from metrics alone - no API call.

    Returns {dimension: {"score_0_10": float, "level": int, "level_label": str}}.
    """
    results = {}
    for dim, classify in _CLASSIFIERS.items():
        level = classify(graph_metrics, complexity_metrics)
        label = STRUCTURE_LEVEL_CRITERIA[dim][level].split(":", 1)[0]
        results[dim] = {
            "score_0_10": level / 4 * 10,
            "level": level,
            "level_label": label,
        }
    return results


def weighted_structure_total(scores: dict[str, dict]) -> float:
    return sum(scores[dim]["score_0_10"] * weight for dim, weight in STRUCTURE_WEIGHTS.items())
