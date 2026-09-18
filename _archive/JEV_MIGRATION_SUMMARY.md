# Scorer-CLI: LLM → Jev Migration Summary

## Overview

This document summarizes the complete redesign of `scorer-cli` to use **TypeSafe Jev** (System One) instead of free-form LLM calls for hackathon submission scoring.

## What Changed

### Before (LLM Approach)
- **2 text-generation LLM calls** per submission (scoring + prose mixed together)
- **Expensive:** Two full LLM inference passes
- **Unpredictable:** Free-form prose means non-deterministic output; parsing back to numbers is fragile
- **Hard to compose:** Cannot reuse or adjust scoring weights without re-running both calls
- **Slow:** High latency per submission (10–30s each call)
- **No separation:** LLM tries to judge AND write prose → confused priorities

### After (Jev + LLM Approach)
- **2 Jev API calls** per submission (judgment only, structured)
  - **Call 1:** 6 parallel **Score** primitives (structure dimensions)
  - **Call 2:** 1 **Choice** + 5 **Noul** primitives (spec dimensions)
- **1 LLM API call** per submission (prose only, from structured data)
- **Fast:** Jev <1s each, LLM summarization <2s
- **Deterministic:** Jev's calibration designed for consistency; scoring logic in code, not hidden in LLM reasoning
- **Composable:** Code owns weighting; change `config.yaml`, no re-run needed
- **Interpretable:** Scores come with confidence levels; prose explains what they mean
- **Clean separation:** Jev judges (focused), LLM writes (focused)

## Key Design Decisions

### 1. Separation of Concerns: Jev Judges, LLM Writes

**Why this split?**
- **Jev is optimized for judgment:** Structured answers (yes/no, level 1–5) with calibrated confidence
- **LLM is optimized for prose:** Writing clear explanations from data
- **Clean API:** Jev outputs scored_data (JSON), LLM consumes scored_data, produces markdown
- **Testable:** Score and prose are independent; can test scoring without LLM, prose without scoring

**Flow:**
```
Metrics → [Jev Call 1: Structure] → Levels 1–5 with confidence
Metrics → [Jev Call 2: Spec] → Yes/no with confidence
Both → [Code: Arithmetic] → 0–10 scores + red flags
Scores → [LLM Call: Report Gen] → Markdown prose
```

### 3. Score Primitives for Structure (1–5 Levels)

Each structural dimension is a **Score** primitive with 5 ordered levels:
- Level 1 = Critical problems
- Level 2 = Poor
- Level 3 = Fair
- Level 4 = Good
- Level 5 = Excellent

**Mapping to 0–10 scale:**
- Level 1 → 0
- Level 2 → 2.5
- Level 3 → 5.0
- Level 4 → 7.5
- Level 5 → 10.0

**Why Scores, not free-form text?**
- Jev returns a probability distribution over levels → can pick top level and confidence
- No parsing prose for numbers — output contract is guaranteed
- Confidence guides manual review priority

### 2. Choice + Noul for Spec Quality

**Choice:** Identify the weakest SDD dimension (helps judges prioritize reading)

**Noul (yes/no for each dimension):**
- Threshold-based judgments
- "Are requirements concrete and testable?" → yes/no with confidence
- Maps to scores: yes (8) / no (3), adjusted by confidence

**Why Noul, not free-form?**
- Binary thresholds are easier for Jev to calibrate
- Confidence tells us how ambiguous the spec is
- No ambiguity about what "good" vs "bad" means

### 4. Deterministic Arithmetic in Code

Scoring is two-phase:
1. **Jev Phase:** Get raw judgments (levels, thresholds, confidence)
2. **Math Phase:** Code computes weighted totals using formulas from `config.yaml`

This separates **semantic judgment** (Jev) from **policy** (weighting). Want to change dimension weights? Edit `config.yaml` and recompute; no Jev calls needed.

## New Files

| File | Purpose |
|------|---------|
| `specs/002-jev-redesign.md` | Complete architecture and process flow |
| `code-structure-jev-questions.md` | 6 Score primitives: coupling, cycles, depth, CCN, function size, betweenness |
| `spec-jev-questions.md` | 1 Choice + 5 Noul for SDD quality (clarity, scope, consistency, traceability, substance) |
| `config.yaml.example` | TypeSafe API setup, dimension descriptions, thresholds, red flag rules |
| `SAMPLE_REPORT.md` | Example output showing how scores and justifications appear to judges |
| `JEV_MIGRATION_SUMMARY.md` | This file |

## Modified Files

| File | Changes |
|------|---------|
| `README.md` | Updated to reference Jev instead of LLM; changed dependency from `anthropic` to `typesafe` |
| `001-mvp.md` | Kept for historical reference (see `002-jev-redesign.md` for current design) |

## How Judges Read the Report

The output format is **unchanged**:
- Structure section: 6 dimension scores with justifications
- Spec section: 5 dimension scores with justifications
- Red flags list
- Combined weighted total

**Difference:** Justifications now say *"Jev rated Coupling as Level 4 (78% confidence) because..."* instead of "*The LLM judged coupling as moderate because...*"

Judges see the same information, with the added transparency of confidence levels.

## Implementation Checklist

### Phase 1: Setup
- [ ] Create TypeSafe account and obtain API key
- [ ] Update `pyproject.toml` to include `typesafe` SDK
- [ ] Copy `config.yaml.example` to `config.yaml` and fill in TypeSafe endpoint/credentials
- [ ] Update `requirements` or `dependencies` to remove `anthropic`, add `typesafe`

### Phase 2: Code Changes
- [ ] Refactor scoring pipeline to call Jev instead of LLM
  - Structure scoring: 6 Score primitives in one call → extract levels + confidence
  - Spec scoring: Choice + 5 Noul in one call → extract answers + confidence
- [ ] Implement level-to-score mapping (1–5 → 0–10)
- [ ] Implement threshold-to-score mapping (yes/no → 8/3, adjusted by confidence)
- [ ] Update report generation to include Jev confidence in justifications
- [ ] Add Jev API error handling (retry, fallback to null scores)

### Phase 3: Testing & Validation
- [ ] Run Jev scorer on sample fixture; compare outputs to original LLM scorer
- [ ] Verify scores are similar (not identical — Jev is different model)
- [ ] Ensure red flags match original rules
- [ ] Test batch processing with multiple submissions
- [ ] Verify `--dry-run` still works (metrics only, no Jev calls)

### Phase 4: Deployment
- [ ] Deploy alongside original (A/B by config flag) for side-by-side validation
- [ ] Collect feedback from judges on usefulness of confidence levels
- [ ] Sunset original LLM scorer
- [ ] Remove `anthropic` SDK dependency entirely

## Token & Cost Savings

### Before (2 LLM calls per submission)
- Full LLM inference: ~5 min-tokens per call (structure) + ~5 min-tokens (spec) = ~10 min-tokens total
- For a 50-team hackathon: 500 min-tokens
- At typical Claude pricing: ~$0.15/1M min-tokens → ~$0.08 per team, ~$4 total

### After (2 Jev + 1 LLM per submission)
- Jev: ~1 min-token per call (structured judgments, not prose) × 2 calls = ~2 min-tokens
- LLM: ~2–3 min-tokens per call (summarization from structured data, not full scoring)
- **Total: ~4–5 min-tokens per submission**
- For a 50-team hackathon: ~200–250 min-tokens
- TypeSafe pricing + Claude pricing (combined) → estimated ~$0.02–0.03 per team, <$2 total

**Expected savings: 50–60% reduction in API costs** (and much better latency).

**Latency improvement:**
- Before: 10–30s per LLM call × 2 = 20–60s per submission
- After: <1s per Jev call × 2 + <2s per LLM call = <4s per submission (5–15× faster)

## Confidence & Uncertainty Handling

Jev returns confidence for each answer. Use this to:

1. **Identify ambiguous submissions:** High confidence → clear signal. Low confidence → worth manual inspection.
2. **Prioritize judge effort:** Sort submissions by average confidence; review low-confidence ones manually first.
3. **Red flag weak signals:** If weakest dimension choice has < 0.45 confidence, flag "dimensions are close" in red flags.

Example in `config.yaml`:
```yaml
red_flags:
  choice_confidence_low: 0.45  # Flag if weakest_dimension confidence < this
```

## Known Limitations & Future Work

### Current (MVP)
- Single Jev call per dimension (no averaging across multiple runs)
- No confidence-based automatic rerun (e.g., rerun if confidence < threshold)
- Red flags still use deterministic metrics, not Jev signals

### Future Enhancements
- Average 2–3 Jev calls per submission for consistency
- Auto-rerun low-confidence dimensions
- Judge dashboard showing Jev confidence scores alongside metrics
- Per-judge override feedback: "Jev said X, but I disagree because Y" → feed back to calibrate

## Questions & Troubleshooting

**Q: Why Score (1–5) instead of direct 0–10 score?**
A: Jev is calibrated for discrete ordered levels, not continuous ranges. Mapping 1–5 → 0–10 is more reliable than asking for a direct 0–10 score.

**Q: Why Choice for weakest dimension instead of Noul on each?**
A: Choice is more efficient (one question covers all options). Weakest dimension is a *diagnostic*, not a score — it helps judges prioritize reading, not a final judgment.

**Q: What if metrics are missing (e.g., no source code)?**
A: Jev questions can skip metrics gracefully if state values are null. Report notes will say "CCN scoring skipped — no source code provided."

**Q: Can I run this offline?**
A: No — Jev requires API calls to TypeSafe's endpoint. Metrics computation (graph + complexity) is local; scoring is remote.

**Q: How do I debug a Jev call that returned unexpected answers?**
A: Check the exact state JSON sent to Jev (log it in debug mode). Verify field names, units, and value ranges match the question definitions. Jev's confidence should be lower if state is ambiguous.

---

## Contact & Support

For questions about this redesign or TypeSafe Jev integration, reach out to the hackathon organizing team.

For TypeSafe SDK docs, see: https://docs.typesafe.ai/
