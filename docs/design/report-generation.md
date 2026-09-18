# Report Generation: LLM Prose from Structured Scores

This document defines how Claude generates readable markdown reports from Jev scores.

## Overview

After Jev scoring and deterministic arithmetic, we have `scored_data.json`:

```json
{
  "submission_id": "team-42",
  "structure": {
    "scores": {"coupling": {"score": 7.5, "level": 4, "confidence": 0.78}, ...},
    "weighted_total": 7.8
  },
  "spec": {
    "scores": {"clarity": {"score": 8.0, "answer": "yes", "confidence": 0.72}, ...},
    "weighted_total": 7.6,
    "weakest_dimension": {"answer": "Traceability", "confidence": 0.52}
  },
  "combined_score": 7.7,
  "red_flags": [...]
}
```

The LLM's job: **Convert this JSON into readable markdown.**

## Prompt Design

The Claude call receives:

```
Input:
  - scored_data (concise JSON, all numbers + confidence)
  - metrics snapshot (key stats: nodes, CCN, cycles)
  - config.yaml rubric descriptions
  
Output:
  - Markdown (2–3 sentences per dimension + 3–4 summary)
  - No preamble, no JSON, pure markdown
```

## Prompt Template

```python
prompt = f"""
You are a hackathon judge report writer. Generate markdown explaining structured scoring data.

SCORING DATA:
{json.dumps(scored_data, indent=2)}

METRICS SNAPSHOT:
{json.dumps(metrics_snapshot, indent=2)}

TASK:
1. Build one summary table for structure (6 rows) and one for spec (5 rows):
   columns are Dimension | Weight | Score | Jev Level (or Jev Answer) | Confidence.

2. For each structure dimension (6 total), under a #### header:
   - Write 2–3 sentences explaining the Jev level and score
   - Reference specific metrics (coupling ratio, CCN values, etc.)
   - Cite confidence level
   - End with actionable feedback for judges

3. For each spec dimension (5 total), under a #### header:
   - Write 2–3 sentences
   - State whether threshold was met (yes/no)
   - Explain what it means for judges
   - Cite confidence

4. Summary (3–4 sentences):
   - Key strengths
   - Key weaknesses
   - Recommendation for judges

FORMAT:
Use markdown. One score/level/confidence table per section (structure, spec), followed
by a ### justification per dimension — do not repeat the table per dimension.

Example:
```markdown
| Dimension | Weight | Score | Jev Level | Confidence |
|---|---|---|---|---|
| Coupling | 21% | 7.5 / 10 | 4 (Good) | 78% |

#### Coupling
[2–3 sentences]
```

OUTPUT:
Markdown only. Start with ## Structure Quality, then ## Spec Quality, then ## Summary.
No preamble, no JSON, no code fences.
"""
```

## Configuration

In `config.yaml`:

```yaml
report_generation:
  model: "claude-opus-5"  # or claude-haiku for cost
  temperature: 0.3        # Low: factual, consistent tone
  max_tokens: 2000        # Usually 1200–1800 used
  max_retries: 1
  retry_delay_seconds: 2
```

**Why low temperature:** We want factual explanations grounded in numbers, not creative flourishes.

## Fallback Strategy

If LLM fails (timeout, API error):

```python
def generate_report_markdown(...):
    try:
        response = client.messages.create(...)
        return response.content[0].text
    except Exception as e:
        logger.error(f"LLM failed: {e}")
        return generate_fallback_markdown(scored_data)

def generate_fallback_markdown(scored_data):
    """Auto-generated markdown if LLM is unavailable."""
    md = f"# Report for {scored_data['submission_id']}\n\n"
    md += f"**Combined Score:** {scored_data['combined_score']:.1f} / 10\n"
    md += f"**Structure:** {scored_data['structure']['weighted_total']:.1f} / 10\n"
    md += f"**Spec:** {scored_data['spec']['weighted_total']:.1f} / 10\n\n"
    
    md += "## Structure Scores\n"
    for dim, data in scored_data['structure']['scores'].items():
        md += f"- {dim}: {data['score']:.1f}/10 (Level {data['level']}, {data['confidence']:.0%})\n"
    
    md += "\n## Spec Scores\n"
    for dim, data in scored_data['spec']['scores'].items():
        md += f"- {dim}: {data['score']:.1f}/10 ({data['answer']}, {data['confidence']:.0%})\n"
    
    md += "\n## Red Flags\n"
    for flag in scored_data.get('red_flags', []):
        md += f"- {flag}\n"
    
    return md
```

## Output Format

Final report has this structure:

```markdown
# Hackathon Submission Report: team-X

**Generated:** [timestamp]  
**Submission ID:** team-X

---

## Structure Quality (Code Metrics)

Scores derived from dependency graph + complexity metrics, judged by Jev.

| Dimension | Weight | Score | Jev Level | Confidence |
|---|---|---|---|---|
| Coupling | 21% | 7.5 / 10 | 4 (Good) | 78% |
| [5 more structure dimensions...] | | | | |

#### Coupling
[Claude's 2–3 sentences explaining the level + metrics + feedback]

#### [5 more structure dimensions...]

---

## Spec Quality (SDD Scoring)

Scores from Spec-Driven Development quality, judged by Jev.

### Weakest Dimension (Diagnostic)

**Jev Choice:** Traceability (confidence 52%)

The model identified Traceability as the weakest dimension with moderate confidence...

| Dimension | Weight | Score | Jev Answer | Confidence |
|---|---|---|---|---|
| Clarity & Testability | 25% | 8.0 / 10 | Yes | 72% |
| [4 more spec dimensions...] | | | | |

#### Clarity & Testability
[Claude's 2–3 sentences]

#### [4 more spec dimensions...]

---

## Summary for Judges

[Claude's 3–4 sentences on strengths, weaknesses, recommendation]

---

## Red Flags

- Function X has CCN > 20
- [...]

---

## Scoring Metadata

| Field | Value |
|-------|-------|
| **Jev Model** | jev |
| **LLM Model** | claude-opus-5 |
| **Structure Confidence Avg** | 74% |
| **Spec Confidence Avg** | 67% |
| **Generated By** | score-cli v0.2.0 |

---

*This report is an assistive tool for human judges, not a final verdict.*
```

## Markdown Validation

Before writing to disk, validate:

```python
def validate_markdown(text: str) -> bool:
    """Check that Claude output is valid markdown."""
    # Must contain expected headers
    required = ["## Structure Quality", "## Spec Quality", "## Summary"]
    if not all(h in text for h in required):
        return False
    
    # Must not contain code fences (no JSON/output leaking)
    if "```json" in text or "```python" in text:
        return False
    
    # Must have reasonable length (not truncated)
    if len(text) < 500:
        return False
    
    return True

if not validate_markdown(markdown):
    logger.warning(f"Claude output failed validation, using fallback")
    markdown = generate_fallback_markdown(scored_data)
```

## LLM Behavior Notes

- **Temperature 0.3:** Claude produces factual, consistent explanations
- **No system prompt override:** Use default Claude instructions (stable)
- **Input is JSON, not prose:** Claude is excellent at consuming structured data
- **Confidence levels in input:** Claude naturally incorporates these ("78% confident" language)
- **Keep metrics concise:** Send only key stats, not raw metrics.json

## Error Cases

| Case | Behavior |
|------|----------|
| LLM timeout | Retry once, then fallback markdown |
| LLM refuses task | Fallback markdown (shouldn't happen; prompt is benign) |
| LLM output is truncated | Check max_tokens; increase if needed |
| Invalid markdown from LLM | Validate and fall back |
| Scores don't match Claude explanation | This is OK; prose is best-effort from LLM |

## Cost Optimization

Current: `claude-opus-5`

**To save 50% on LLM costs:**
```yaml
report_generation:
  model: "claude-haiku"  # Haiku is ~5× cheaper
  temperature: 0.3
  max_tokens: 1500
```

Haiku should handle this task fine (structured input, straightforward prose output).

## Future Enhancements

1. **Template selection:** Choose prose style based on audience ("executive summary" vs. "detailed")
2. **Multi-language:** Haiku might support report generation in other languages
3. **Comment in output:** Include judge commentary fields where judges can add notes
4. **Streaming:** Stream LLM output to file as it's generated (for large batches)
