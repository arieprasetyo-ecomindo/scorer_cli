import os
from types import SimpleNamespace

import pytest

from app.jev_scorer import (
    SPEC_NOUL_INSTRUCTIONS,
    SPEC_WEIGHTS,
    build_jev_log,
    noul_score,
    noul_to_answer_and_confidence,
    score_spec,
    score_spec_with_response,
    weighted_spec_total,
)


class FakeSpecClient:
    """Stands in for typesafe_sdk.TypeSafeClient so tests don't call the real API."""

    def __init__(self, weakest: dict, nouls: dict[str, float]):
        self._weakest = weakest
        self._nouls = nouls

    def system_one(self, state, questions, **kwargs):
        choice = SimpleNamespace(
            choice=self._weakest["choice"],
            confidence=self._weakest["confidence"],
            probabilities=self._weakest.get("probabilities", {}),
        )
        nouls = {
            f"{dim}_met": SimpleNamespace(noul=value) for dim, value in self._nouls.items()
        }
        usage = SimpleNamespace(input_tokens=50, output_tokens=10)
        return SimpleNamespace(
            choices={"weakest_sdd_dimension": choice},
            nouls=nouls,
            model="fake-model",
            usage=usage,
        )


def default_nouls(value: float) -> dict[str, float]:
    return {dim: value for dim in SPEC_NOUL_INSTRUCTIONS}


def test_noul_to_answer_and_confidence_yes():
    answer, confidence = noul_to_answer_and_confidence(0.9)
    assert answer == "yes"
    assert confidence == pytest.approx(0.8)


def test_noul_to_answer_and_confidence_no():
    answer, confidence = noul_to_answer_and_confidence(0.1)
    assert answer == "no"
    assert confidence == pytest.approx(0.8)


def test_noul_to_answer_and_confidence_uncertain():
    answer, confidence = noul_to_answer_and_confidence(0.5)
    assert answer == "yes"
    assert confidence == 0.0


def test_noul_score_interpolation_matches_docs_examples():
    cfg = {"yes_score_range": [7.5, 9.0], "no_score_range": [1.0, 4.0]}
    assert noul_score("yes", 0.8, cfg) == pytest.approx(8.7)
    assert noul_score("no", 0.6, cfg) == pytest.approx(2.8)


def test_score_spec_shape():
    client = FakeSpecClient(
        weakest={"choice": "Traceability", "confidence": 0.52, "probabilities": {"Traceability": 0.52}},
        nouls=default_nouls(0.9),
    )
    result = score_spec("spec text", ["a.py", "b.py"], client)

    assert result["weakest_dimension"]["choice"] == "Traceability"
    assert result["weakest_dimension"]["confidence"] == 0.52
    for dim in SPEC_NOUL_INSTRUCTIONS:
        assert result[dim]["answer"] == "yes"
        assert 0 <= result[dim]["score_0_10"] <= 10


def test_score_spec_uses_custom_score_range_from_config():
    client = FakeSpecClient(
        weakest={"choice": "Clarity & Testability", "confidence": 0.5},
        nouls=default_nouls(1.0),  # noul=1.0 -> answer=yes, confidence=1.0
    )
    custom_rubric = {"clarity_testability": {"yes_score_range": [5.0, 5.0], "no_score_range": [0.0, 0.0]}}
    result = score_spec("spec text", [], client, spec_rubric_config=custom_rubric)
    assert result["clarity_testability"]["score_0_10"] == 5.0


def test_weighted_spec_total():
    client = FakeSpecClient(
        weakest={"choice": "Traceability", "confidence": 0.9},
        nouls=default_nouls(1.0),  # every dim: yes, confidence=1.0 -> score 9.0
    )
    result = score_spec("spec text", [], client)
    assert weighted_spec_total(result) == pytest.approx(9.0)


def test_build_jev_log_captures_raw_spec_response():
    client = FakeSpecClient(
        weakest={"choice": "Traceability", "confidence": 0.52, "probabilities": {"Traceability": 0.52}},
        nouls=default_nouls(0.7),
    )
    _, response = score_spec_with_response("spec text", ["a.py"], client)

    log = build_jev_log("sample_team_phoenix", spec_response=response)

    assert log["spec"]["model"] == "fake-model"
    assert log["spec"]["weakest_dimension"]["choice"] == "Traceability"
    assert set(log["spec"]["answers"].keys()) == {f"{d}_met" for d in SPEC_NOUL_INSTRUCTIONS}
    assert log["spec"]["answers"]["clarity_testability_met"]["noul"] == 0.7
    assert "structure" not in log


@pytest.mark.skipif(not os.environ.get("TYPESAFE_API_KEY"), reason="requires TYPESAFE_API_KEY")
def test_live_smoke_against_real_jev_api():
    from typesafe_sdk import TypeSafeClient

    client = TypeSafeClient()
    spec_text = (
        "## spec.md\n\nThe system SHALL provide a Start control. "
        "MVP: timer only. Out of scope: multi-user support."
    )
    result = score_spec(spec_text, ["app/main.py", "app/timer.py"], client)
    assert set(result.keys()) == {"weakest_dimension", *SPEC_NOUL_INSTRUCTIONS.keys()}
    for dim in SPEC_NOUL_INSTRUCTIONS:
        assert result[dim]["answer"] in ("yes", "no")
        assert 0 <= result[dim]["score_0_10"] <= 10
