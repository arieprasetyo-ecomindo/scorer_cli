"""Call Claude to write a concise narrative markdown summary from Jev scores."""

import json

from anthropic import Anthropic

from app.jev_scorer import (
    SPEC_WEIGHTS,
    STRUCTURE_WEIGHTS,
    weighted_spec_total,
    weighted_structure_total,
)

PROMPT_TEMPLATE = """You are writing a concise hackathon judge report. Be brief - this is a \
summary, not an essay. Use plain, direct language.

STRUCTURE SCORES (code quality, 0-10):
{structure_json}

SPEC SCORES (SDD quality, 0-10):
{spec_json}

RED FLAGS:
{red_flags}

TASK:
Write markdown with exactly these sections:
## Summary
2-3 sentences: overall verdict, the single biggest strength, and the single biggest weakness.

## Structure Notes
One sentence per dimension that scored below 7/10 (skip dimensions that scored 7 or above). \
If all structure dimensions scored 7+, write one sentence saying structure is solid.

## Spec Notes
One sentence per dimension that scored below 7/10 (skip dimensions that scored 7 or above). \
If all spec dimensions scored 7+, write one sentence saying the spec is solid.

## Recommendation
One sentence of actionable advice for the team.

Keep total output under 200 words. Markdown prose only - no preamble, no JSON, no code fences.
"""


def build_prompt(jev_scores: dict | None, spec_scores: dict | None, red_flags: list[str]) -> str:
    structure_summary = (
        {dim: round(jev_scores[dim]["score_0_10"], 1) for dim in STRUCTURE_WEIGHTS}
        if jev_scores
        else {}
    )
    spec_summary = (
        {dim: round(spec_scores[dim]["score_0_10"], 1) for dim in SPEC_WEIGHTS}
        if spec_scores
        else {}
    )
    return PROMPT_TEMPLATE.format(
        structure_json=json.dumps(structure_summary, indent=2),
        spec_json=json.dumps(spec_summary, indent=2),
        red_flags="\n".join(f"- {f}" for f in red_flags) if red_flags else "None",
    )


def generate_narrative(
    jev_scores: dict | None,
    spec_scores: dict | None,
    red_flags: list[str],
    client: Anthropic,
    model: str = "claude-opus-5",
    max_tokens: int = 600,
) -> str:
    # Note: the real anthropic-sdk (checked at v1.6.0) has no `temperature` param on
    # messages.create() - it's been replaced by an `effort` level in output_config,
    # which controls reasoning depth, not randomness. There's no direct equivalent
    # for "low temperature = consistent output" here, so we don't set one.
    prompt = build_prompt(jev_scores, spec_scores, red_flags)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_fallback_narrative(jev_scores: dict | None, spec_scores: dict | None) -> str:
    """Auto-generated markdown if the LLM call fails - scores only, no prose."""
    lines = ["## Summary", "", "_LLM unavailable - auto-generated summary (scores only)._"]
    if jev_scores:
        lines += ["", f"**Structure weighted total:** {weighted_structure_total(jev_scores):.1f} / 10"]
    if spec_scores:
        lines += ["", f"**Spec weighted total:** {weighted_spec_total(spec_scores):.1f} / 10"]
    return "\n".join(lines)
