# scorer_cli Documentation Index

Quick navigation for all documentation. (All paths below are relative to `docs/`, except `README.md` which is one level up at the repo root.)

## Start Here

- **[../README.md](../README.md)** — Project overview, features, get started in 5 minutes
- **[QUICKSTART.md](QUICKSTART.md)** — First-time user guide (5 min walkthrough)

## For Different Audiences

### Hackathon Participants
- [HOW_IT_WORKS.md](HOW_IT_WORKS.md) — Simplified diagram of the scoring pipeline

### Judges (Reading Reports)
- [examples/sample-report.md](examples/sample-report.md) — Example report output
- [spec/rubrics.md](spec/rubrics.md) — Understanding the scoring dimensions
- [ARCHITECTURE.md](ARCHITECTURE.md) — Optional: deep dive into methodology

### Project Leads / Architects
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design, 3-phase pipeline, data structures
- [../config.yaml.example](../config.yaml.example) — Configuration reference

### Developers (Building It)
- [DEVELOPER_CHECKLIST.md](DEVELOPER_CHECKLIST.md) — Step-by-step implementation guide
- [design/structure-scoring.md](design/structure-scoring.md) — Jev Score primitives (6 dimensions)
- [design/spec-scoring.md](design/spec-scoring.md) — Jev Choice + Noul primitives (5 dimensions)
- [design/report-generation.md](design/report-generation.md) — LLM prompt, fallback, validation

### Compliance / Audit
- [spec/rubrics.md](spec/rubrics.md) — Complete rubric definitions
- [../config.yaml.example](../config.yaml.example) — Scoring configuration & weights
- [examples/sample-report.md](examples/sample-report.md) — Example outputs

## Documentation Map

```
scorer_cli/
├── README.md                           ← Start here (repo root)
├── CLAUDE.md                           ← Claude Code project instructions (repo root)
├── config.yaml.example                 ← Configuration (repo root)
│
├── docs/
│   ├── INDEX.md (this file)            ← Navigation
│   ├── HOW_IT_WORKS.md                 ← Simplified pipeline diagram (for participants)
│   ├── ARCHITECTURE.md                 ← System design (detailed)
│   ├── QUICKSTART.md                   ← First-time user (5 min)
│   ├── HANDOFF.md                      ← Project handoff summary
│   ├── DEVELOPER_CHECKLIST.md          ← Implementation guide
│   │
│   ├── design/                         ← Implementation details (for devs)
│   │   ├── structure-scoring.md        ← 6 Code quality dimensions
│   │   ├── spec-scoring.md             ← 5 SDD quality dimensions
│   │   └── report-generation.md        ← LLM prose generation
│   │
│   ├── spec/
│   │   └── rubrics.md                  ← Complete scoring reference
│   │
│   └── examples/
│       └── sample-report.md            ← Example output (for judges)
│
└── app/                                ← Application source code
    ├── __main__.py
    ├── scorer.py
    ├── metrics.py
    ├── jev_scorer.py
    ├── scoring_engine.py
    ├── llm_reporter.py
    └── report_generator.py
```

> **Not yet written:** `ARCHITECTURE.md`'s config section is the source of truth for API setup and troubleshooting today — dedicated `API.md`/`FAQ.md` docs and a `design/scoring-math.md` formula reference don't exist yet. See [HANDOFF.md](HANDOFF.md) for what's outstanding.

## Quick Links

### Running scorer_cli

| Task | Command | See |
|------|---------|-----|
| Score all submissions | `uv run score-cli run-all` | [QUICKSTART](QUICKSTART.md) |
| Score one submission | `uv run score-cli run team-a-007` | [QUICKSTART](QUICKSTART.md) |
| Compute metrics only | `uv run score-cli run team-a-007 --dry-run` | [QUICKSTART](QUICKSTART.md) |
| Recompute from metrics | `uv run score-cli recompute reports/metrics/*.json` | [QUICKSTART](QUICKSTART.md) |

### Understanding Reports

| Concept | Document |
|---------|----------|
| What's in a report? | [Sample Report](examples/sample-report.md) |
| What do scores mean? | [Rubrics](spec/rubrics.md) |
| What's confidence? | [ARCHITECTURE](ARCHITECTURE.md#confidence-levels) |
| Why did team X get score Y? | [Rubrics](spec/rubrics.md) + report |

### Configuration

| Setting | Document |
|---------|----------|
| API keys | [ARCHITECTURE.md](ARCHITECTURE.md#configuration-configyaml) |
| Weights | [spec/rubrics.md](spec/rubrics.md#combined-score-formula) |
| Thresholds | [design/structure-scoring.md](design/structure-scoring.md#weights) |
| LLM model | [../config.yaml.example](../config.yaml.example) |

### Troubleshooting

| Issue | See |
|-------|-----|
| "Module not found" | [QUICKSTART](QUICKSTART.md#troubleshooting) |
| API key errors | [ARCHITECTURE.md](ARCHITECTURE.md#configuration-configyaml) |
| Jev timeout | [QUICKSTART](QUICKSTART.md#troubleshooting) |
| LLM failures | [design/report-generation.md#fallback-strategy](design/report-generation.md#fallback-strategy) |
| Low confidence scores | [ARCHITECTURE.md#confidence-levels](ARCHITECTURE.md#confidence-levels) |

## Document Types

### User Guides (Non-Technical)
- **../README.md** — Overview, features, installation
- **QUICKSTART.md** — Get running in 5 minutes
- **examples/sample-report.md** — See example output

### Reference
- **spec/rubrics.md** — Scoring dimensions explained
- **../config.yaml.example** — Configuration options

### Technical Design (For Developers)
- **ARCHITECTURE.md** — System design & data flow
- **design/structure-scoring.md** — Structure scoring details
- **design/spec-scoring.md** — Spec scoring details
- **design/report-generation.md** — Report generation logic

### Implementation (For Coders)
- **DEVELOPER_CHECKLIST.md** — Step-by-step implementation guide
- **design/*.md** — Detailed requirements for each module

## For New Team Members

**First day?**
1. Read [../README.md](../README.md) (5 min)
2. Read [QUICKSTART.md](QUICKSTART.md) (5 min)
3. Run sample: `uv run score-cli run fixtures/team-sample-001`
4. Look at [examples/sample-report.md](examples/sample-report.md)

**First week (if implementing)?**
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) (30 min)
2. Read [spec/rubrics.md](spec/rubrics.md) (20 min)
3. Read [design/structure-scoring.md](design/structure-scoring.md) (20 min)
4. Read [design/spec-scoring.md](design/spec-scoring.md) (20 min)
5. Start implementing per [DEVELOPER_CHECKLIST.md](DEVELOPER_CHECKLIST.md)

## File Changelog

**Current structure (organized, development-ready):**
- ✅ All documentation lives in `docs/` (design docs in `docs/design/`, rubrics in `docs/spec/`, examples in `docs/examples/`)
- ✅ `README.md` and `CLAUDE.md` stay at the repo root
- ✅ Code lives in `app/`

**Consolidated & removed (pre-handoff history):**
- `code-structure-jev-questions.md` → merged into `design/structure-scoring.md`
- `spec-jev-questions.md` → merged into `design/spec-scoring.md`
- `code-structure-scoring-instructions.md`, `spec-scoring-instructions.md`, `scoring-guide.md` → superseded by `design/*.md` and `spec/rubrics.md`
- `SAMPLE_REPORT.md` → moved to `examples/sample-report.md`
- `IMPLEMENTATION_GUIDE.md`, `PIPELINE_OVERVIEW.md`, `JEV_MIGRATION_SUMMARY.md` → content merged into `ARCHITECTURE.md` / `DEVELOPER_CHECKLIST.md`; the `_archive/` folder that held these has since been deleted
- `001-mvp.md`, `002-jev-redesign.md` → superseded by `ARCHITECTURE.md` and `design/*.md`; removed

## Summary

**Development-ready structure:**
- Clear separation within `docs/`: user guides (top-level), design (`design/`), reference (`spec/`), examples (`examples/`)
- Easy to find: this index + `../README.md` guide you
- Easy to update: each document has one purpose
- For teams: design docs are detailed enough to implement from, examples show what success looks like

---

**Questions?** Check [ARCHITECTURE.md](ARCHITECTURE.md) or start with [../README.md](../README.md).
