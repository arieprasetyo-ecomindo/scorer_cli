"""Call TypeSafe's Jev model (System One) to judge code structure quality.

See docs/design/structure-scoring.md for the rubric these criteria encode.
Level order is ascending (index 0 = Critical ... index N-1 = Excellent) to
match typesafe_sdk.Score's zero-indexed criteria sequence.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

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


def _usage_dict(response) -> dict | None:
    usage = getattr(response, "usage", None)
    return {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None


def build_jev_log(team_name: str, structure_response=None, spec_response=None) -> dict:
    """Raw, judge-auditable record of what Jev actually returned for a submission."""
    log: dict = {"team": team_name, "generated_at": datetime.now(timezone.utc).isoformat()}

    if structure_response is not None:
        log["structure"] = {
            "model": structure_response.model,
            "usage": _usage_dict(structure_response),
            "answers": {
                dim: {
                    "score": answer.score,
                    "confidence": answer.confidence,
                    "legend": answer.legend,
                    "probabilities": answer.probabilities,
                }
                for dim, answer in structure_response.scores.items()
            },
        }

    if spec_response is not None:
        weakest = spec_response.choices["weakest_sdd_dimension"]
        log["spec"] = {
            "model": spec_response.model,
            "usage": _usage_dict(spec_response),
            "weakest_dimension": {
                "choice": weakest.choice,
                "confidence": weakest.confidence,
                "probabilities": weakest.probabilities,
            },
            "answers": {
                dim: {"noul": answer.noul}
                for dim, answer in spec_response.nouls.items()
            },
        }

    return log


def write_jev_log(team_dir: Path, log: dict) -> Path:
    log_path = team_dir / "jev_log.json"
    log_path.write_text(json.dumps(log, indent=2))
    return log_path


def weighted_structure_total(scores: dict[str, dict]) -> float:
    return sum(scores[dim]["score_0_10"] * weight for dim, weight in STRUCTURE_WEIGHTS.items())


# --- Spec / SDD scoring: 1 Choice + 5 Noul primitives ---------------------
# See docs/design/spec-scoring.md.

WEAKEST_DIMENSION_CRITERIA: dict[str, str] = {
    "Clarity & Testability": "Requirements are vague, aspirational, or unfalsifiable",
    "Scope Boundary": "In-scope/out-of-scope is unclear",
    "Internal Consistency": "Spec contradicts itself",
    "Traceability": "Spec doesn't map to the actual codebase",
    "Substance Over Polish": "More formatting than concrete content",
}

SPEC_NOUL_INSTRUCTIONS: dict[str, str] = {
    "clarity_testability": (
        "Are requirements in spec_text concrete and testable throughout (e.g. "
        "'API returns 400 on missing email'), rather than vague ('handle errors well')?"
    ),
    "scope_boundary": (
        "Is in-scope vs. out-of-scope explicitly stated or clearly inferable from spec_text's structure?"
    ),
    "internal_consistency": (
        "Is spec_text free of significant internal contradictions (same entity described "
        "consistently, requirements and data models aligned)?"
    ),
    "traceability": (
        "Do most components named in spec_text plausibly map to files in codebase_modules?"
    ),
    "substance_over_polish": (
        "Is spec_text substantive (concrete detail) rather than well-formatted but vague or padded?"
    ),
}

SPEC_WEIGHTS: dict[str, float] = {
    "clarity_testability": 0.25,
    "scope_boundary": 0.15,
    "internal_consistency": 0.15,
    "traceability": 0.25,
    "substance_over_polish": 0.20,
}

DEFAULT_SCORE_RANGE = {"yes_score_range": [7.5, 9.0], "no_score_range": [1.0, 4.0]}


def noul_to_answer_and_confidence(noul_value: float) -> tuple[str, float]:
    """Derive a yes/no answer and confidence from Jev's single yes-probability.

    Noul only returns one float (probability of "yes"); there's no separate
    confidence field in the real API. See docs/design/spec-scoring.md.
    """
    answer = "yes" if noul_value >= 0.5 else "no"
    confidence = abs(noul_value - 0.5) * 2
    return answer, confidence


def noul_score(answer: str, confidence: float, score_range_cfg: dict) -> float:
    """Map a derived (answer, confidence) to 0-10 per docs/design/spec-scoring.md."""
    lo, hi = score_range_cfg["yes_score_range" if answer == "yes" else "no_score_range"]
    return lo + (hi - lo) * confidence


def _call_spec_jev(spec_text: str, codebase_modules: list[str], client: TypeSafeClient):
    state = {"spec_text": spec_text, "codebase_modules": codebase_modules}
    questions = {
        "weakest_sdd_dimension": Choice(
            instructions="Identify which SDD dimension is weakest or most concerning in spec_text.",
            criteria=WEAKEST_DIMENSION_CRITERIA,
        ),
        **{
            f"{dim}_met": Noul(instructions=instructions)
            for dim, instructions in SPEC_NOUL_INSTRUCTIONS.items()
        },
    }
    return client.system_one(state, questions)


def _parse_spec_response(response, spec_rubric_config: dict | None) -> dict:
    spec_rubric_config = spec_rubric_config or {}
    weakest = response.choices["weakest_sdd_dimension"]

    results: dict = {
        "weakest_dimension": {
            "choice": weakest.choice,
            "confidence": weakest.confidence,
            "probabilities": weakest.probabilities,
        }
    }
    for dim in SPEC_NOUL_INSTRUCTIONS:
        noul_value = response.nouls[f"{dim}_met"].noul
        answer, confidence = noul_to_answer_and_confidence(noul_value)
        range_cfg = spec_rubric_config.get(dim, DEFAULT_SCORE_RANGE)
        results[dim] = {
            "answer": answer,
            "confidence": confidence,
            "noul_raw": noul_value,
            "score_0_10": noul_score(answer, confidence, range_cfg),
        }
    return results


def score_spec(
    spec_text: str,
    codebase_modules: list[str],
    client: TypeSafeClient,
    spec_rubric_config: dict | None = None,
) -> dict:
    """Judge spec quality via Jev's Choice (weakest dimension) + 5 Noul primitives."""
    response = _call_spec_jev(spec_text, codebase_modules, client)
    return _parse_spec_response(response, spec_rubric_config)


def score_spec_with_response(
    spec_text: str,
    codebase_modules: list[str],
    client: TypeSafeClient,
    spec_rubric_config: dict | None = None,
):
    """Like score_spec(), but also returns the raw SystemOneResponse for logging."""
    response = _call_spec_jev(spec_text, codebase_modules, client)
    return _parse_spec_response(response, spec_rubric_config), response


def weighted_spec_total(scores: dict) -> float:
    return sum(scores[dim]["score_0_10"] * weight for dim, weight in SPEC_WEIGHTS.items())
