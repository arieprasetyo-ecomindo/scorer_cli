# Developer Checklist: Implementing scorer_cli

This checklist guides you through implementing scorer_cli from scratch.

## Phase 0: Preparation (1 hour)

- [ ] Read `README.md` (understand what this project does)
- [ ] Read `ARCHITECTURE.md` (understand the 3-phase pipeline)
- [ ] Read `spec/rubrics.md` (understand all 11 scoring dimensions)
- [ ] Review `design/structure-scoring.md` (understand 6 Score primitives)
- [ ] Review `design/spec-scoring.md` (understand Choice + 5 Noul)
- [ ] Review `design/report-generation.md` (understand LLM prose generation)

**Estimated time:** 90 minutes

## Phase 1: Setup (30 min)

- [ ] Clone repo
- [ ] `uv sync` to install dependencies
- [ ] `cp config.yaml.example config.yaml`
- [ ] Register for TypeSafe API (get TYPESAFE_API_KEY)
- [ ] Register for Anthropic API (get ANTHROPIC_API_KEY)
- [ ] Set environment variables:
  ```bash
  export TYPESAFE_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```
- [ ] Verify setup: `uv run score-cli --help` (should show CLI options)

**Estimated time:** 30 minutes

## Phase 2: Core Modules (4–6 hours)

### Module 1: `metrics.py` (Already exists? Check it)

**Purpose:** Extract graph + complexity metrics from submissions.

- [ ] Uses NetworkX to parse graph.json
- [ ] Collapses symbol-level graph to file-level
- [ ] Outputs metrics.json with all required fields
- [ ] Tests pass: `uv run pytest tests/test_metrics.py`

**Reference:** See `design/structure-scoring.md` input state section

**Estimated time:** 1 hour (or 0 if already done)

---

### Module 2: `jev_scorer.py` (NEW)

**Purpose:** Call Jev API for structured judgment.

**Tasks:**
- [ ] Initialize TypeSafe client with API key
- [ ] Build 6 Score questions for structure (from `design/structure-scoring.md`)
- [ ] Build Choice question for weakest spec dimension
- [ ] Build 5 Noul questions for spec quality (from `design/spec-scoring.md`)
- [ ] Call Jev API: `score_structure(metrics)` → returns 6 Score answers
- [ ] Call Jev API: `score_spec(spec_text, codebase_modules)` → returns Choice + 5 Noul answers
- [ ] Handle Jev errors: retry once, then null scores + log error
- [ ] Tests: `uv run pytest tests/test_jev_scorer.py`

**Reference:** `design/structure-scoring.md` and `design/spec-scoring.md`

**Estimated time:** 1–2 hours

---

### Module 3: `scoring_engine.py` (NEW)

**Purpose:** Map Jev answers to 0–10 scores, compute weights.

**Tasks:**
- [ ] Load config.yaml (weights, thresholds, rubric descriptions)
- [ ] Function `score_structure(jev_answers)`:
  - Map Level 1–5 → Score 0–10: `(level - 1) * 2.5`
  - Apply weights from config
  - Compute `structure_weighted_total`
  - Return scores dict with justifications
- [ ] Function `score_spec(jev_answers)`:
  - Map yes/no + confidence → 0–10 score
  - Apply thresholds from config
  - Compute `spec_weighted_total`
  - Return scores dict
- [ ] Function `combined_score(structure_total, spec_total)`:
  - Apply config.weights (default 0.5 / 0.5)
  - Return single 0–10 score
- [ ] Function `check_red_flags(metrics, scores)`:
  - Check rubric red flag rules (see `spec/rubrics.md`)
  - Return list of flag strings
- [ ] Tests: `uv run pytest tests/test_scoring_engine.py`

**Reference:** `design/scoring-math.md` for all formulas

**Estimated time:** 1–1.5 hours

---

### Module 4: `llm_reporter.py` (NEW)

**Purpose:** Call Claude to generate markdown prose from scores.

**Tasks:**
- [ ] Initialize Anthropic client with API key
- [ ] Function `generate_report_markdown(submission_id, scored_data, config, metrics)`:
  - Build concise JSON payload (scored_data + metrics snapshot)
  - Build prompt (see `design/report-generation.md`)
  - Call Claude with low temperature (0.3) for consistency
  - Validate markdown output
  - Return markdown string
- [ ] Implement fallback: `generate_fallback_markdown(scored_data)`
  - If Claude fails, generate auto-formatted markdown (scores only, no prose)
  - Ensure fallback is valid markdown
- [ ] Error handling: retry once, then fallback
- [ ] Tests: `uv run pytest tests/test_llm_reporter.py`

**Reference:** `design/report-generation.md`

**Estimated time:** 1–1.5 hours

---

### Module 5: `report_generator.py` (NEW)

**Purpose:** Format and write final markdown reports to disk.

**Tasks:**
- [ ] Function `write_report(submission_id, scored_data, markdown_content, output_dir)`:
  - Write to `reports/<submission_id>.md`
  - Include header (submission ID, timestamp)
  - Include LLM-generated markdown
  - Include scoring metadata footer
  - Ensure all required sections present
- [ ] Create directories as needed: `reports/`, `reports/metrics/`
- [ ] Save `metrics.json` alongside report for reproducibility
- [ ] Handle write errors gracefully
- [ ] Tests: `uv run pytest tests/test_report_generator.py`

**Estimated time:** 0.5–1 hour

---

### Module 6: `scorer.py` (Orchestration)

**Purpose:** Tie all modules together.

**Tasks:**
- [ ] Function `score_submission(submission_id, config)`:
  - Load submission files (graph.json, source.zip, sdd.zip)
  - Call `metrics.extract_metrics()` → metrics.json
  - Call `jev_scorer.score_structure(metrics)` → Jev answers
  - Call `jev_scorer.score_spec(spec_text, codebase_modules)` → Jev answers
  - Call `scoring_engine` functions → scored_data with 0–10 scores
  - Call `llm_reporter.generate_report_markdown()` → markdown
  - Call `report_generator.write_report()` → write to disk
  - Return report path
- [ ] Function `score_all_submissions(submissions_dir, config)`:
  - Batch process all folders in submissions/
  - Skip on error (log and continue)
  - Report progress
- [ ] Error handling: catch and log all exceptions
- [ ] Tests: `uv run pytest tests/test_scorer.py`

**Estimated time:** 1 hour

---

### Module 7: `__main__.py` (CLI)

**Purpose:** Command-line interface.

**Tasks:**
- [ ] CLI options:
  - `score-cli run <team-id>` — score one submission
  - `score-cli run-all` — score all
  - `score-cli run <team-id> --dry-run` — metrics only
  - `score-cli recompute <metrics-files>` — recompute from existing metrics
- [ ] Load config.yaml
- [ ] Parse arguments
- [ ] Call appropriate functions from `scorer.py`
- [ ] Print progress/results to stdout
- [ ] Exit with status code (0 = success, 1 = error)

**Estimated time:** 0.5 hours

**Estimated Phase 2 Total:** 4–6 hours

## Phase 3: Testing (2–3 hours)

### Unit Tests

- [ ] `tests/test_metrics.py` — metrics extraction
- [ ] `tests/test_jev_scorer.py` — Jev API calls (mock Jev responses)
- [ ] `tests/test_scoring_engine.py` — score mapping & arithmetic
- [ ] `tests/test_llm_reporter.py` — LLM call & markdown generation (mock Claude)
- [ ] `tests/test_report_generator.py` — file I/O & formatting
- [ ] `tests/test_scorer.py` — end-to-end orchestration

**Run all tests:**
```bash
uv run pytest tests/ -v
```

**Coverage target:** >80% (focus on logic, not edge cases)

**Estimated time:** 1 hour

### Integration Test

- [ ] Use sample fixture: `fixtures/team-sample-001/`
- [ ] Run: `uv run score-cli run team-sample-001`
- [ ] Check output:
  - [ ] `reports/team-sample-001.md` exists
  - [ ] Markdown is valid (no syntax errors)
  - [ ] Contains all sections (Structure, Spec, Summary)
  - [ ] Confidence levels present
  - [ ] Red flags (if any) listed
  - [ ] Scores are 0–10 and make sense
- [ ] Compare to `examples/sample-report.md` (format should match)

**Estimated time:** 1 hour

### Manual Testing

- [ ] Test error cases:
  - Missing graph.json → graceful error + continue batch
  - Jev timeout → retry + fallback
  - LLM timeout → fallback markdown
  - Invalid spec_text → graceful handling
- [ ] Test config changes:
  - Change weights in config.yaml
  - Recompute: `uv run score-cli recompute reports/metrics/team-*/metrics.json`
  - Verify scores changed, no API calls made
- [ ] Performance:
  - Time a full batch (50 teams)
  - Should be ~200 seconds (4s per submission)
  - Check API call counts in logs

**Estimated time:** 1 hour

**Estimated Phase 3 Total:** 2–3 hours

## Phase 4: Documentation & Handoff (1 hour)

- [ ] Update this checklist if the implementation process changed
- [ ] Verify all docs in `docs/`, `docs/design/`, `docs/spec/` are accurate
- [ ] Test docs: can someone use them to understand your code?
- [ ] Run lint/format:
  ```bash
  uv run black app/
  uv run flake8 app/
  ```
- [ ] Create CHANGELOG.md (what was implemented)
- [ ] Tag version: `git tag v0.2.0`
- [ ] Update pyproject.toml version

**Estimated time:** 1 hour

## Total Effort

**Phase 0 (Prep):** 1.5 hours  
**Phase 1 (Setup):** 0.5 hours  
**Phase 2 (Modules):** 4–6 hours  
**Phase 3 (Testing):** 2–3 hours  
**Phase 4 (Docs):** 1 hour  

**Total:** 9–12 hours (roughly 1–2 days for one developer)

## Quick Reference

### Key Files to Know

- `config.yaml.example` — All configuration
- `design/structure-scoring.md` — 6 Score primitives (criteria, metrics)
- `design/spec-scoring.md` — Choice + 5 Noul (criteria, mappings)
- `design/report-generation.md` — LLM prompt design
- `spec/rubrics.md` — Complete scoring reference (11 dimensions)

### Important Modules

```
app/
├── metrics.py              (extract metrics.json)
├── jev_scorer.py          (call Jev API)
├── scoring_engine.py      (map Jev → 0-10 scores)
├── llm_reporter.py        (call Claude API)
├── report_generator.py    (write reports to disk)
├── scorer.py              (orchestrate all above)
└── __main__.py            (CLI)
```

### API Keys

```bash
export TYPESAFE_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Run Sample

```bash
uv run score-cli run fixtures/team-sample-001
# Output: reports/team-sample-001.md
```

### Run Tests

```bash
uv run pytest tests/ -v
```

## Troubleshooting During Implementation

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError" | `uv sync` to install dependencies |
| Jev API 401 | Check TYPESAFE_API_KEY, verify it's from TypeSafe dashboard |
| Claude API 401 | Check ANTHROPIC_API_KEY, verify it's from Anthropic console |
| Jev timeout | Normal; retry logic handles it. Check if TypeSafe status page shows issues. |
| Markdown formatting odd | Check LLM prompt in `design/report-generation.md`, verify temperature is 0.3 |
| Scores don't match rubric | Check `design/scoring-math.md` formulas, verify weights in config.yaml |
| Tests fail | Run with `-v` flag, check assertion messages, read test file for expected behavior |

## Success Criteria

When complete, you should have:

- ✅ All 7 modules implemented (metrics, jev_scorer, scoring_engine, llm_reporter, report_generator, scorer, __main__)
- ✅ All tests pass (`uv run pytest`)
- ✅ Sample fixture produces valid report: `uv run score-cli run fixtures/team-sample-001`
- ✅ Report matches `examples/sample-report.md` format
- ✅ Batch scoring works: `uv run score-cli run-all` (on sample data)
- ✅ Recompute works: `uv run score-cli recompute reports/metrics/*.json` (no API calls, fast)
- ✅ Documentation is accurate and up-to-date
- ✅ Code is linted and formatted (`black`, `flake8`)

---

**Questions?** Check `ARCHITECTURE.md`.

**Ready?** Start with Phase 0 prep, then Phase 1 setup. Good luck! 🚀
