import os
from types import SimpleNamespace

import pytest

from app.llm_reporter import build_prompt, generate_fallback_narrative, generate_narrative

STRUCTURE_SCORES = {
    "coupling": {"score_0_10": 7.7},
    "circular_dependencies": {"score_0_10": 10.0},
    "dependency_depth": {"score_0_10": 9.8},
    "cyclomatic_complexity": {"score_0_10": 6.5},
    "function_size_discipline": {"score_0_10": 10.0},
    "betweenness_centrality": {"score_0_10": 9.5},
}
SPEC_SCORES = {
    "weakest_dimension": {"choice": "Traceability", "confidence": 0.2},
    "clarity_testability": {"score_0_10": 8.4},
    "scope_boundary": {"score_0_10": 8.9},
    "internal_consistency": {"score_0_10": 8.3},
    "traceability": {"score_0_10": 2.4},
    "substance_over_polish": {"score_0_10": 8.8},
}


class FakeAnthropicClient:
    def __init__(self, text: str):
        self.messages = SimpleNamespace(create=self._create)
        self._text = text
        self.last_call = None

    def _create(self, **kwargs):
        self.last_call = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text=self._text)])


def test_build_prompt_includes_scores_and_flags():
    prompt = build_prompt(STRUCTURE_SCORES, SPEC_SCORES, ["some red flag"])
    assert "coupling" in prompt
    assert "7.7" in prompt
    assert "some red flag" in prompt


def test_build_prompt_handles_missing_sections():
    prompt = build_prompt(None, None, [])
    assert "None" in prompt  # red flags placeholder


def test_generate_narrative_calls_client_and_returns_text():
    client = FakeAnthropicClient("## Summary\n\nGood job.")
    result = generate_narrative(STRUCTURE_SCORES, None, [], client, model="claude-opus-5")
    assert result == "## Summary\n\nGood job."
    assert client.last_call["model"] == "claude-opus-5"


def test_generate_fallback_narrative_has_scores_no_llm():
    text = generate_fallback_narrative(STRUCTURE_SCORES, None)
    assert "LLM unavailable" in text
    assert "Structure weighted total" in text


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="requires ANTHROPIC_API_KEY")
def test_live_smoke_against_real_anthropic_api():
    from anthropic import Anthropic

    client = Anthropic()
    result = generate_narrative(STRUCTURE_SCORES, SPEC_SCORES, ["example flag"], client)
    assert isinstance(result, str)
    assert len(result) > 0
