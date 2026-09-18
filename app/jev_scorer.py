"""Call TypeSafe's Jev model (System One) to judge code structure quality.

See docs/design/structure-scoring.md for the rubric these criteria encode.
Level order is ascending (index 0 = Critical ... index N-1 = Excellent) to
match typesafe_sdk.Score's zero-indexed criteria sequence.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from typesafe_sdk import Score, TypeSafeClient

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


def rescale_score(raw_score: float, num_levels: int) -> float:
    """Rescale Jev's 0..(num_levels-1) continuous score to 0..10."""
    return raw_score / (num_levels - 1) * 10


def _level_label(raw_score: float, legend: dict[int, str]) -> str:
    """Nearest integer level's short label (the text before the colon)."""
    level = round(raw_score)
    return legend[level].split(":", 1)[0]


def _call_structure_jev(graph_metrics: dict, complexity_metrics: dict, client: TypeSafeClient):
    state = {"graph_metrics": graph_metrics, "complexity_metrics": complexity_metrics}
    questions = {
        dim: Score(
            instructions=(
                f"Rate the {dim.replace('_', ' ')} of this codebase using graph_metrics "
                "and complexity_metrics in state, against the given criteria levels."
            ),
            criteria=levels,
        )
        for dim, levels in STRUCTURE_LEVEL_CRITERIA.items()
    }
    return client.system_one(state, questions)


def _parse_structure_response(response) -> dict[str, dict]:
    results = {}
    for dim, levels in STRUCTURE_LEVEL_CRITERIA.items():
        answer = response.scores[dim]
        results[dim] = {
            "score_0_10": rescale_score(answer.score, len(levels)),
            "level": round(answer.score),
            "level_label": _level_label(answer.score, answer.legend),
            "confidence": answer.confidence,
            "legend": answer.legend,
        }
    return results


def score_structure(
    graph_metrics: dict, complexity_metrics: dict, client: TypeSafeClient
) -> dict[str, dict]:
    """Judge code structure quality via Jev's 6 Score primitives.

    Returns {dimension: {"score_0_10": float, "confidence": float, "legend": dict}}.
    """
    response = _call_structure_jev(graph_metrics, complexity_metrics, client)
    return _parse_structure_response(response)


def score_structure_with_response(graph_metrics: dict, complexity_metrics: dict, client: TypeSafeClient):
    """Like score_structure(), but also returns the raw SystemOneResponse for logging."""
    response = _call_structure_jev(graph_metrics, complexity_metrics, client)
    return _parse_structure_response(response), response


def build_jev_log(team_name: str, response) -> dict:
    """Raw, judge-auditable record of what Jev actually returned for a submission."""
    usage = getattr(response, "usage", None)
    return {
        "team": team_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": response.model,
        "usage": (
            {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
            if usage
            else None
        ),
        "structure": {
            dim: {
                "score": answer.score,
                "confidence": answer.confidence,
                "legend": answer.legend,
                "probabilities": answer.probabilities,
            }
            for dim, answer in response.scores.items()
        },
    }


def write_jev_log(team_dir: Path, log: dict) -> Path:
    log_path = team_dir / "jev_log.json"
    log_path.write_text(json.dumps(log, indent=2))
    return log_path


def weighted_structure_total(scores: dict[str, dict]) -> float:
    return sum(scores[dim]["score_0_10"] * weight for dim, weight in STRUCTURE_WEIGHTS.items())
