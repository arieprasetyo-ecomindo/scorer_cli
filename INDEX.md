# scorer_cli Documentation Index

Quick navigation for all documentation.

## Start Here

- **[README.md](README.md)** — Project overview, features, get started in 5 minutes
- **[docs/QUICKSTART.md](docs/QUICKSTART.md)** — First-time user guide (5 min walkthrough)

## For Different Audiences

### Judges (Reading Reports)
- [examples/sample-report.md](examples/sample-report.md) — Example report output
- [spec/rubrics.md](spec/rubrics.md) — Understanding the scoring dimensions
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Optional: deep dive into methodology

### Project Leads / Architects
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design, 3-phase pipeline, data structures
- [docs/FAQ.md](docs/FAQ.md) — Common questions & troubleshooting
- [config.yaml.example](config.yaml.example) — Configuration reference

### Developers (Building It)
- [IMPLEMENTATION_GUIDE.md](_archive/IMPLEMENTATION_GUIDE.md) — Step-by-step code implementation
- [design/structure-scoring.md](design/structure-scoring.md) — Jev Score primitives (6 dimensions)
- [design/spec-scoring.md](design/spec-scoring.md) — Jev Choice + Noul primitives (5 dimensions)
- [design/report-generation.md](design/report-generation.md) — LLM prompt, fallback, validation
- [design/scoring-math.md](design/scoring-math.md) — Formulas, weights, thresholds

### Compliance / Audit
- [spec/rubrics.md](spec/rubrics.md) — Complete rubric definitions
- [config.yaml.example](config.yaml.example) — Scoring configuration & weights
- [examples/sample-report.md](examples/sample-report.md) — Example outputs

## Documentation Map

```
scorer_cli/
├── README.md                           ← Start here
├── INDEX.md (this file)                ← Navigation
├── config.yaml.example                 ← Configuration
│
├── docs/
│   ├── ARCHITECTURE.md                 ← System design (detailed)
│   ├── QUICKSTART.md                   ← First-time user (5 min)
│   ├── API.md                          ← TypeSafe + Anthropic setup
│   └── FAQ.md                          ← Troubleshooting
│
├── design/                             ← Implementation details (for devs)
│   ├── structure-scoring.md            ← 6 Code quality dimensions
│   ├── spec-scoring.md                 ← 5 SDD quality dimensions
│   ├── report-generation.md            ← LLM prose generation
│   └── scoring-math.md                 ← Formulas & arithmetic
│
├── spec/
│   └── rubrics.md                      ← Complete scoring reference
│
├── examples/
│   └── sample-report.md                ← Example output (for judges)
│
├── _archive/                           ← Old/deprecated files
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── JEV_MIGRATION_SUMMARY.md
│   ├── PIPELINE_OVERVIEW.md
│   └── [other old docs]
│
└── score_cli/                          ← Application source code
    ├── __main__.py
    ├── scorer.py
    ├── metrics.py
    ├── jev_scorer.py
    ├── scoring_engine.py
    ├── llm_reporter.py
    └── report_generator.py
```

## Quick Links

### Running scorer_cli

| Task | Command | See |
|------|---------|-----|
| Score all submissions | `uv run score-cli run-all` | [QUICKSTART](docs/QUICKSTART.md) |
| Score one submission | `uv run score-cli run team-a-007` | [QUICKSTART](docs/QUICKSTART.md) |
| Compute metrics only | `uv run score-cli run team-a-007 --dry-run` | [QUICKSTART](docs/QUICKSTART.md) |
| Recompute from metrics | `uv run score-cli recompute reports/metrics/*.json` | [QUICKSTART](docs/QUICKSTART.md) |

### Understanding Reports

| Concept | Document |
|---------|----------|
| What's in a report? | [Sample Report](examples/sample-report.md) |
| What do scores mean? | [Rubrics](spec/rubrics.md) |
| What's confidence? | [ARCHITECTURE](docs/ARCHITECTURE.md#confidence-levels) |
| Why did team X get score Y? | [Rubrics](spec/rubrics.md) + report |

### Configuration

| Setting | Document |
|---------|----------|
| API keys | [docs/API.md](docs/API.md) |
| Weights | [spec/rubrics.md](spec/rubrics.md#combined-score-formula) |
| Thresholds | [design/scoring-math.md](design/scoring-math.md) |
| LLM model | [config.yaml.example](config.yaml.example) |

### Troubleshooting

| Issue | See |
|-------|-----|
| "Module not found" | [QUICKSTART](docs/QUICKSTART.md#troubleshooting) |
| API key errors | [docs/API.md](docs/API.md) |
| Jev timeout | [docs/FAQ.md](docs/FAQ.md) (or [FAQ](docs/FAQ.md#jev-api-timeout)) |
| LLM failures | [design/report-generation.md#fallback-strategy](design/report-generation.md#fallback-strategy) |
| Low confidence scores | [ARCHITECTURE.md#confidence-levels](docs/ARCHITECTURE.md#confidence-levels) |

## Document Types

### User Guides (Non-Technical)
- **README.md** — Overview, features, installation
- **docs/QUICKSTART.md** — Get running in 5 minutes
- **examples/sample-report.md** — See example output

### Reference
- **spec/rubrics.md** — Scoring dimensions explained
- **config.yaml.example** — Configuration options
- **docs/FAQ.md** — Common questions

### Technical Design (For Developers)
- **docs/ARCHITECTURE.md** — System design & data flow
- **design/structure-scoring.md** — Structure scoring details
- **design/spec-scoring.md** — Spec scoring details
- **design/report-generation.md** — Report generation logic
- **design/scoring-math.md** — Formulas & weights

### Implementation (For Coders)
- **_archive/IMPLEMENTATION_GUIDE.md** — Step-by-step code walkthrough
- **design/*.md** — Detailed requirements for each module

## For New Team Members

**First day?**
1. Read [README.md](README.md) (5 min)
2. Read [docs/QUICKSTART.md](docs/QUICKSTART.md) (5 min)
3. Run sample: `uv run score-cli run fixtures/team-sample-001`
4. Look at [examples/sample-report.md](examples/sample-report.md)

**First week (if implementing)?**
1. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (30 min)
2. Read [spec/rubrics.md](spec/rubrics.md) (20 min)
3. Read [design/structure-scoring.md](design/structure-scoring.md) (20 min)
4. Read [design/spec-scoring.md](design/spec-scoring.md) (20 min)
5. Start implementing per [_archive/IMPLEMENTATION_GUIDE.md](_archive/IMPLEMENTATION_GUIDE.md)

## File Changelog

**Current structure (organized, development-ready):**
- ✅ Main docs in `docs/`
- ✅ Design docs in `design/`
- ✅ Rubrics in `spec/`
- ✅ Examples in `examples/`
- ✅ Old docs archived in `_archive/`
- ✅ Code lives in `score_cli/`

**Consolidated & removed:**
- `code-structure-jev-questions.md` → Merged into `design/structure-scoring.md`
- `spec-jev-questions.md` → Merged into `design/spec-scoring.md`
- `code-structure-scoring-instructions.md` → Archived (replaced by design docs)
- `spec-scoring-instructions.md` → Archived (replaced by design docs)
- `scoring-guide.md` → Merged into `spec/rubrics.md`
- `SAMPLE_REPORT.md` → Moved to `examples/sample-report.md`
- `IMPLEMENTATION_GUIDE.md` → Archived (still useful, but consolidated design docs replace parts)
- `PIPELINE_OVERVIEW.md` → Content merged into `docs/ARCHITECTURE.md`
- `JEV_MIGRATION_SUMMARY.md` → Content merged into `docs/ARCHITECTURE.md`
- `001-mvp.md` → Archived (historical, replaced by 002-jev-redesign)
- `002-jev-redesign.md` → Archived (content refactored into modular docs)

## Summary

**Development-ready structure:**
- Clear separation: user docs (docs/) vs. design (design/) vs. reference (spec/)
- No redundancy: consolidated into single source of truth per topic
- Easy to find: INDEX.md + README.md guide you
- Easy to update: each document has one purpose
- For teams: design docs are detailed enough to implement from, examples show what success looks like

---

**Questions?** Check [docs/FAQ.md](docs/FAQ.md) or start with [README.md](README.md).
