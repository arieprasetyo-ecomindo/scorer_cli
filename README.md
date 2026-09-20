# scorer_cli

Automated hackathon submission scoring: code structure + Spec-Driven Development (SDD) quality.

## What It Does

Scores a team's submission using:
- **Jev** (TypeSafe System One) for structured judgment on code structure and spec quality
- **Claude** (Anthropic) for a concise, score-focused narrative summary
- **NetworkX** + **Lizard** for the local, deterministic metrics that feed Jev

**Pipeline:**
1. Parse `graph.json` (Graphify output) → file-level dependency graph → graph metrics (coupling, cycles, depth, betweenness) via NetworkX
2. Extract `source.zip` → complexity metrics (cyclomatic complexity, function size) via Lizard
3. Extract `sdd.zip` → concatenated spec text (framework-agnostic — works with OpenSpec, a plain `SPEC.md`, ADRs, anything)
4. Ask Jev to judge structure (6 Score dimensions) and spec quality (1 Choice + 5 Noul dimensions)
5. Rescale Jev's answers to 0–10, apply weights from `config.yaml`, compute a combined score
6. Ask Claude for a short narrative summary (falls back to a scores-only summary if the call fails)
7. Render a Rich-formatted report in the terminal, a chart (`matplotlib`), and a markdown report to disk

## Get Started

```bash
# Install
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repo> && cd scorer_cli
uv sync

# Configure
cp config.yaml.example config.yaml
cp .env.example .env
# then edit .env and fill in:
#   TYPESAFE_API_KEY=...   (from https://console.typesafe.ai/settings/keys)
#   ANTHROPIC_API_KEY=...  (from the Anthropic console)

# Run on the sample fixture
uv run score-cli report sample_team_phoenix
```

This prints a full Rich-formatted report to the terminal and writes:
- `reports/sample_team_phoenix.md` — the markdown report (chart + score tables + narrative)
- `reports/sample_team_phoenix_chart.png` — the score chart embedded in that report
- `fixtures/sample_team_phoenix/jev_log.json` — the raw Jev response (for judge auditability)

Missing `source.zip`, `sdd.zip`, or an API key doesn't crash the run — each stage is skipped
with a clear reason shown in its place, and whatever's available still gets scored.

## Documentation

All documentation lives in [`docs/`](docs/) — see [docs/INDEX.md](docs/INDEX.md) for full navigation.

| Document | For | Purpose |
|----------|-----|---------|
| **docs/HOW_IT_WORKS.md** | Hackathon participants | Simplified diagram + plain-language explanation |
| **docs/QUICKSTART.md** | Users, judges | Get started in 5 minutes |
| **docs/ARCHITECTURE.md** | Architects, leads | System design, 3-phase pipeline, data structures |
| **docs/DEVELOPER_CHECKLIST.md** | Developers | Step-by-step implementation guide |
| **docs/design/structure-scoring.md** | Developers | 6 Score primitives for code (detailed) |
| **docs/design/spec-scoring.md** | Developers | Choice + 5 Noul for spec (detailed) |
| **docs/design/report-generation.md** | Developers | LLM prompt, fallback, markdown validation |
| **docs/spec/rubrics.md** | Judges, developers | Complete rubric reference (11 dimensions) |
| **docs/examples/sample-report.md** | Judges | Illustrative example report |

> Some docs above (`QUICKSTART.md`, `HANDOFF.md`, `DEVELOPER_CHECKLIST.md`) predate the working
> implementation and still describe a planned `run` / `run-all` / `--dry-run` / `recompute` CLI
> that doesn't exist yet — see [Roadmap](#roadmap) below for the real state.

## Directory Structure

```
scorer_cli/
├── README.md (this file)
├── CLAUDE.md
├── config.yaml.example
├── config.yaml            # your local copy, gitignored secrets live in .env instead
├── .env.example
│
├── docs/                        # All documentation (see table above)
│
├── fixtures/                    # Team submissions to score
│   └── sample_team_phoenix/
│       ├── graph.json            (Graphify dependency graph)
│       ├── source.zip            (source code)
│       ├── sdd.zip                (spec documents)
│       └── jev_log.json           (generated: raw Jev response)
│
├── reports/                     # Generated output (gitignored)
│   ├── sample_team_phoenix.md
│   └── sample_team_phoenix_chart.png
│
├── app/                         # Application code
│   ├── __main__.py               CLI entry point
│   ├── config.py                 Loads config.yaml
│   ├── metrics.py                Graph metrics (NetworkX) + complexity metrics (Lizard) + spec text extraction
│   ├── jev_scorer.py              Jev API calls: structure (Score) + spec (Choice/Noul) scoring, weights, logging
│   ├── llm_reporter.py            Claude API call for the narrative summary + fallback
│   ├── chart_generator.py         matplotlib score chart (also runnable standalone)
│   ├── report_generator.py        Rich terminal report + red-flag rules
│   └── report_writer.py           Assembles the final markdown report
│
└── tests/                       # pytest suite (mocked API clients + live smoke tests gated on API keys)
```

## CLI Commands

```bash
# Score one submission (looks for fixtures/<team_name>/)
uv run score-cli report <team_name>

# e.g.
uv run score-cli report sample_team_phoenix
```

That's the only command today — see [Roadmap](#roadmap) for `run-all`/batch scoring.

## Scoring Dimensions

**Structure (Code Quality) — 6 dimensions:**
1. Coupling (interdependencies)
2. Circular Dependencies (loops)
3. Dependency Depth (chain length)
4. Cyclomatic Complexity (function branching)
5. Function Size (NLOC + parameters)
6. Betweenness Centrality (bottlenecks)

**Spec (SDD Quality) — 5 dimensions:**
1. Clarity & Testability (concrete requirements)
2. Scope Boundary (in/out of scope)
3. Internal Consistency (no contradictions)
4. Traceability (spec ↔ code mapping)
5. Substance Over Polish (real content, not filler)

See `docs/spec/rubrics.md` for the complete rubric, and `docs/design/spec-scoring.md` for how
spec scoring actually derives an answer + confidence from Jev's single Noul probability.

## Configuration

Copy `config.yaml.example` to `config.yaml`. Fields actually read by the code today:

```yaml
report_generation:
  model: "claude-opus-5"   # or claude-haiku for cost
  max_tokens: 2000

weights:
  structure: 0.5            # combined_score = structure_total * this ...
  spec: 0.5                 # ... + spec_total * this

spec_rubric:                # per-dimension yes/no score interpolation ranges
  clarity_testability:
    yes_score_range: [7.5, 9.0]
    no_score_range: [1.0, 4.0]
  # ... one entry per spec dimension

red_flags:                  # thresholds used by the red-flag checks
  circular_deps_involving_more_than: 3
  max_ccn_threshold: 20
  fan_coupling_multiple: 5.0
  betweenness_multiple: 10.0
  min_modules_mentioned: 2
  choice_confidence_low: 0.45
  templated_boilerplate: true
```

Not yet wired up (present in `config.yaml.example` but currently ignored): `typesafe.*`
(the SDK reads `TYPESAFE_API_KEY`/model defaults directly), `max_retries`/`retry_delay_seconds`
on either API, `spec_rubric.*.threshold`, `batch.*`, `logging.*`. Per-dimension *weights* for
structure (21/17/13/21/13/15%) and spec (25/15/15/25/20%) are hardcoded in `app/jev_scorer.py`,
not read from `config.yaml`.

Real API notes worth knowing if you edit this file:
- `typesafe.model` must be `"jev-latest"` (or a pinned version) — the real `typesafe-sdk`
  rejects the bare name `"jev"`.
- There is no `temperature` field for `report_generation` — the real `anthropic-sdk` (checked
  at v1.6.0) doesn't have that parameter anymore.

## Input Format

```
fixtures/
  <team_name>/
    graph.json      (dependency graph from Graphify — required)
    source.zip       (source code — optional; skips complexity + structure Jev scoring if absent)
    sdd.zip           (spec documents — optional; skips spec Jev scoring if absent)
```

## Output

Running `report` prints a full Rich terminal report (graph metrics, complexity metrics,
Structure/Spec Quality tables with inline score bars, a combined-score meter, and red flags),
and — whenever there's at least one Jev score to report — writes to disk:

```
reports/
  <team_name>.md          (markdown report: chart + score tables + narrative + red flags)
  <team_name>_chart.png    (score chart, embedded in the .md above)

fixtures/<team_name>/
  jev_log.json             (raw Jev response: model, token usage, per-dimension scores/confidence/probabilities)
```

Example report: `docs/examples/sample-report.md` (illustrative — written before the real
implementation, so exact formatting may differ slightly from what `report` produces today).

## Roadmap

**Done:**
- ✅ Graph metrics (NetworkX) from Graphify's `graph.json`
- ✅ Complexity metrics (Lizard) from `source.zip`
- ✅ Framework-agnostic spec text extraction from `sdd.zip`
- ✅ Jev structure scoring (6 Score primitives)
- ✅ Jev spec/SDD scoring (1 Choice + 5 Noul primitives)
- ✅ `config.yaml`-driven weights, spec score ranges, and red-flag thresholds
- ✅ Structure + spec red flags
- ✅ Raw Jev response logging (`jev_log.json`) for judge auditability
- ✅ Claude narrative summary, with a scores-only fallback if the API call fails
- ✅ matplotlib score chart + Rich terminal bars, embedded in the markdown report
- ✅ End-to-end tests (mocked clients for CI + live smoke tests gated on real API keys)

**Not yet done:**
- ⬜ Batch mode (`run-all` across every folder in `fixtures/`)
- ⬜ `metrics.json` persistence + a `recompute` command (re-score from cached metrics without
  new API calls when you only change `config.yaml` weights)
- ⬜ Retry-policy wiring (`max_retries`/`retry_delay_seconds` in `config.yaml` aren't read yet —
  each API call is tried once, then falls back)
- ⬜ `docs/API.md`, `docs/FAQ.md`, `docs/design/scoring-math.md` (referenced as "ready to write"
  since the original handoff, still unwritten)
- ⬜ `docs/design/report-generation.md`'s prompt template still shows the old verbose
  per-dimension prose style, not the concise prompt `app/llm_reporter.py` actually uses
- ⬜ `docs/QUICKSTART.md`, `docs/HANDOFF.md`, `docs/DEVELOPER_CHECKLIST.md` still describe the
  pre-implementation planned CLI (`run`/`run-all`/`--dry-run`/`recompute`) rather than the real
  `report` command

## License

[License TBD]

## Support

- Questions? → Check `docs/QUICKSTART.md` or `docs/INDEX.md`
- Bug? → Open an issue / check the test suite (`uv run pytest tests/ -v`)
- Contributing? → See `CONTRIBUTING.md` (TBD)
