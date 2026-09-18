import json
import os
from types import SimpleNamespace

import pytest

from app.jev_scorer import (
    STRUCTURE_LEVEL_CRITERIA,
    build_jev_log,
    rescale_score,
    score_structure,
    score_structure_with_response,
    weighted_structure_total,
    write_jev_log,
)


class FakeClient:
    """Stands in for typesafe_sdk.TypeSafeClient so tests don't call the real API."""

    def __init__(self, canned: dict[str, dict]):
        self._canned = canned

    def system_one(self, state, questions, **kwargs):
        scores = {
            dim: SimpleNamespace(
                score=v["score"],
                confidence=v["confidence"],
                legend=dict(enumerate(STRUCTURE_LEVEL_CRITERIA[dim])),
                probabilities={0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.6},
            )
            for dim, v in self._canned.items()
        }
        usage = SimpleNamespace(input_tokens=100, output_tokens=20)
        return SimpleNamespace(scores=scores, answers=dict(scores), model="fake-model", usage=usage)


def test_rescale_score_endpoints():
    assert rescale_score(0, 5) == 0
    assert rescale_score(4, 5) == 10
    assert rescale_score(2, 5) == 5


def test_score_structure_rescales_each_dimension():
    canned = {dim: {"score": 4, "confidence": 0.9} for dim in STRUCTURE_LEVEL_CRITERIA}
    result = score_structure({}, {}, FakeClient(canned))
    assert set(result.keys()) == set(STRUCTURE_LEVEL_CRITERIA.keys())
    for dim_result in result.values():
        assert dim_result["score_0_10"] == 10
        assert dim_result["confidence"] == 0.9


def test_weighted_structure_total():
    canned = {dim: {"score": 4, "confidence": 1.0} for dim in STRUCTURE_LEVEL_CRITERIA}
    result = score_structure({}, {}, FakeClient(canned))
    assert weighted_structure_total(result) == pytest.approx(10.0)


def test_weighted_structure_total_mixed_scores():
    # coupling excellent (4->10), everything else critical (0->0)
    canned = {dim: {"score": 0, "confidence": 1.0} for dim in STRUCTURE_LEVEL_CRITERIA}
    canned["coupling"] = {"score": 4, "confidence": 1.0}
    result = score_structure({}, {}, FakeClient(canned))
    assert weighted_structure_total(result) == pytest.approx(10 * 0.21)


def test_build_jev_log_captures_raw_response():
    canned = {dim: {"score": 3, "confidence": 0.8} for dim in STRUCTURE_LEVEL_CRITERIA}
    _, response = score_structure_with_response({}, {}, FakeClient(canned))

    log = build_jev_log("sample_team_phoenix", response)

    assert log["team"] == "sample_team_phoenix"
    assert log["model"] == "fake-model"
    assert log["usage"] == {"input_tokens": 100, "output_tokens": 20}
    assert set(log["structure"].keys()) == set(STRUCTURE_LEVEL_CRITERIA.keys())
    assert log["structure"]["coupling"]["score"] == 3
    assert log["structure"]["coupling"]["probabilities"] == {0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.6}


def test_write_jev_log_writes_json_file(tmp_path):
    log = {"team": "x", "structure": {}}
    path = write_jev_log(tmp_path, log)
    assert path == tmp_path / "jev_log.json"
    assert json.loads(path.read_text()) == log


@pytest.mark.skipif(not os.environ.get("TYPESAFE_API_KEY"), reason="requires TYPESAFE_API_KEY")
def test_live_smoke_against_real_jev_api():
    from typesafe_sdk import TypeSafeClient

    client = TypeSafeClient()
    graph_metrics = {"avg_fan_in": 1.6, "max_fan_in": 12, "circular_dependencies": []}
    complexity_metrics = {"avg_cyclomatic_complexity": 3.0, "max_cyclomatic_complexity": 6}
    result = score_structure(graph_metrics, complexity_metrics, client)
    assert set(result.keys()) == set(STRUCTURE_LEVEL_CRITERIA.keys())
    for dim_result in result.values():
        assert 0 <= dim_result["score_0_10"] <= 10
        assert 0 <= dim_result["confidence"] <= 1
