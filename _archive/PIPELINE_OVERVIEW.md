# Scorer-CLI: Complete Pipeline Overview

## The Three Phases

### Phase 1: Metrics Collection (Deterministic, Local)

```
Extract submissions/team-X/
├── graph.json
├── source.zip
└── sdd.zip

↓

NetworkX + Lizard
├── Collapse graph to file-level
├── Compute: coupling, cycles, depth, modularity, betweenness
└── Extract: CCN, function length, parameter count

↓

metrics.json (deterministic output)
```

**Cost:** Zero API calls. All local, reproducible.

---

### Phase 2: Jev Scoring (Structured Judgment)

```
metrics.json
├── graph_metrics
└── complexity_metrics

+ spec_text
+ codebase_modules

↓

[Jev Call 1: Structure Scoring]
6 Score primitives (parallel):
├── Coupling → Level 1–5 + confidence
├── Circular Dependencies → Level 1–5 + confidence
├── Dependency Depth → Level 1–5 + confidence
├── Cyclomatic Complexity → Level 1–5 + confidence
├── Function Size Discipline → Level 1–5 + confidence
└── Betweenness Centrality → Level 1–5 + confidence

[Jev Call 2: Spec Scoring]
1 Choice + 5 Noul (parallel):
├── Weakest SDD Dimension → Choice answer + confidence
├── Clarity & Testability → yes/no + confidence
├── Scope Boundary → yes/no + confidence
├── Internal Consistency → yes/no + confidence
├── Traceability → yes/no + confidence
└── Substance Over Polish → yes/no + confidence

↓

scored_data (JSON with levels and thresholds)
```

**Cost:** ~4 min-tokens total. Structured, deterministic, calibrated by TypeSafe.

---

### Phase 3: Report Generation (Deterministic Arithmetic + LLM Prose)

```
scored_data (JSON)
+ metrics (snapshot)
+ config (rubric descriptions)

↓

[Code Phase: Deterministic Arithmetic]
├── Map Levels 1–5 → Scores 0–10
├── Map yes/no thresholds → Scores 0–10
├── Compute dimension weights (config.yaml)
├── Compute structure_total, spec_total, combined_total
└── Check red flags (metrics + rubric rules)

↓

[LLM Call: Report Generation]
Input: scored_data JSON (structured, concise)
Output: Markdown prose (2–3 sentences per dimension + summary)

↓

reports/team-X.md (final output)
```

**Cost:** ~2–3 min-tokens. LLM only writes prose, doesn't judge.

---

## Data Flow Diagram

```
PHASE 1: METRICS (Local)
┌─────────────────────────────────────┐
│  graph.json + source.zip + sdd.zip │
│         (from submission)            │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │  NetworkX + Lizard │ (local, <1s)
    └────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │   metrics.json     │ (deterministic)
    └────────┬───────────┘
             │
             │
PHASE 2: JUDGMENT (Jev)
             │
             ├──────────────────────────────────┐
             │                                  │
             ▼                                  ▼
    ┌─────────────────┐           ┌──────────────────┐
    │ Jev Call 1:     │           │ Jev Call 2:      │
    │ Structure       │           │ Spec             │
    │ (6 Scores)      │           │ (1 Choice + 5    │
    │ <1s, ~1 min-tok │           │ Noul) <1s, ~1    │
    │                 │           │ min-tok          │
    └────────┬────────┘           └────────┬─────────┘
             │                             │
             ▼                             ▼
    ┌──────────────────────────────────────┐
    │  Jev Scores: Levels 1–5 + Confidence │
    │  Jev Thresholds: yes/no + Confidence │
    └──────────────┬───────────────────────┘
                   │
                   │
PHASE 3: REPORTING (Code + LLM)
                   │
                   ▼
    ┌──────────────────────────────────┐
    │ Code: Deterministic Arithmetic   │ (local)
    │ - Map levels/thresholds to 0–10  │
    │ - Apply weights (config.yaml)    │
    │ - Compute totals                 │
    │ - Check red flags                │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │    scored_data JSON               │ (deterministic)
    │ - All scores 0–10                │
    │ - Confidence levels              │
    │ - Red flags                      │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │ LLM Call: Report Generation      │
    │ Input: scored_data (concise JSON)│
    │ Output: Markdown prose           │
    │ ~2–3 min-tok, <2s                │
    └──────────────┬───────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │   reports/team-X.md              │ (final)
    │ - Scores + Confidence            │
    │ - LLM-written justifications     │
    │ - Red flags                      │
    │ - Combined score + summary       │
    └──────────────────────────────────┘
```

---

## Key Metrics

| Metric | Before (2 LLM) | After (2 Jev + 1 LLM) |
|--------|---|---|
| **Tokens per submission** | ~10 min-tokens | ~4–5 min-tokens |
| **API calls per submission** | 2 (expensive) | 3 (2 fast + 1 medium) |
| **Latency per submission** | 20–60s | ~4s |
| **Scoring determinism** | Non-deterministic prose | Deterministic Jev + code arithmetic |
| **Prose quality** | LLM judges + writes (mixed) | LLM only writes (focused) |
| **Composability** | Low (weights hidden in LLM) | High (weights in config.yaml) |
| **Cost per 50 teams** | ~$4 | ~$2 |

---

## Example Report Structure

```markdown
# Hackathon Submission Report: team-a-007

**Generated:** 2024-11-15T14:32:18Z  
**Submission ID:** team-a-007

---

## Structure Quality (Code Metrics)

### Coupling — Weight 21%

| | |
|--|--|
| **Score** | 7.5 / 10 |
| **Jev Level** | 4 (Good) |
| **Confidence** | 78% |
| **Justification** | [2–3 sentences from Claude LLM, grounded in Jev level + metrics] |

### Circular Dependencies — Weight 17%
...

## Spec Quality (SDD Scoring)

### Weakest Dimension (Diagnostic)

**Jev Choice:** Traceability (confidence 52%)

### Clarity & Testability — Weight 25%
...

## Combined Score: 7.7 / 10

**Summary:** [3–4 sentences from Claude LLM explaining strengths, weaknesses, recommendation]

---

## Scoring Metadata

| Field | Value |
|-------|-------|
| **Jev Model** | jev (TypeSafe System One) |
| **LLM Model** | claude-opus-5 |
| **Structure Confidence Avg** | 74% |
| **Spec Confidence Avg** | 67% |
| **Generated By** | score-cli v0.2.0 (Jev + LLM) |
```

---

## Confidence Interpretation for Judges

Each score comes with a **confidence level** (0–1). Use this to prioritize manual review:

| Avg Confidence | Interpretation |
|---|---|
| **> 0.85** | Jev and metrics are highly aligned; straightforward case. |
| **0.70–0.85** | Clear signal, but some ambiguity in the codebase/spec. |
| **0.50–0.70** | Weak signal; submit to manual review as high priority. |
| **< 0.50** | Very ambiguous; definitely needs human judgment. |

**Example:** If cyclomatic complexity confidence is 0.45, it means Jev found both good and bad signals in the metrics — flag it for a judge to check the actual functions.

---

## Deployment & Operations

### Minimal Setup

1. **Install:** `uv sync`
2. **Configure:** Set `TYPESAFE_API_KEY` and `ANTHROPIC_API_KEY`
3. **Run:** `uv run score-cli run-all`

### Monitoring

- Check logs for failed Jev calls (auto-retry once)
- Check logs for failed LLM calls (fall back to structured markdown)
- Monitor confidence levels; flag low-confidence submissions for review
- Archive `metrics.json` alongside reports for reproducibility

### Troubleshooting

- **Jev timeout:** Retry logic handles once; if persistent, check TypeSafe status
- **LLM timeout:** Fallback to auto-generated markdown (scores only, no prose)
- **Invalid markdown from LLM:** Validate and fall back; never corrupt reports
- **Red flags not appearing:** Check rubric rules in config.yaml

---

## Future Enhancements

1. **Multi-run averaging:** Average 2–3 Jev calls per submission for higher confidence
2. **Confidence-driven review:** Sort submissions by low confidence for manual prioritization
3. **Judge feedback loop:** "Jev said X, I override to Y" → feed back to calibrate
4. **Dashboard:** Live scoring progress + confidence heatmap
5. **Export:** CSV of all scores + confidence for analysis/trending

---

This architecture ensures **reproducibility** (metrics + arithmetic), **clarity** (structured scoring), and **quality** (LLM prose from structured data, not judgment).
