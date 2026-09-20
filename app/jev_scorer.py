"""Call TypeSafe's Jev model (System One) to judge spec/SDD quality.

Structure (code metrics) scoring is deterministic - see app/structure_scorer.py -
because every structure dimension already has an exact numeric rubric. Spec quality
is the one place Jev genuinely earns its keep: judging unstructured prose (is this
testable? does it contradict itself?) isn't a lookup-table problem.

See docs/design/spec-scoring.md for the rubric these criteria encode.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from typesafe_sdk import Choice, Noul, TypeSafeClient

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


def _usage_dict(response) -> dict | None:
    usage = getattr(response, "usage", None)
    return {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None


def build_jev_log(team_name: str, spec_response=None) -> dict:
    """Raw, judge-auditable record of what Jev actually returned for a submission.

    Structure scoring is deterministic (app/structure_scorer.py) and never calls
    Jev, so this log only ever covers the spec/SDD Choice+Noul call.
    """
    log: dict = {"team": team_name, "generated_at": datetime.now(timezone.utc).isoformat()}

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
