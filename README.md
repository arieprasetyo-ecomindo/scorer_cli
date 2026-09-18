# scorer_cli

Automated hackathon submission scoring: code structure + Spec-Driven Development quality.

## What It Does

Scores code and spec quality using:
- **Jev** (TypeSafe System One) for structured judgment → levels + confidence
- **Claude** for readable prose explanations → markdown reports

**Pipeline:**
1. Extract metrics from source code + spec documents
2. Ask Jev to judge code structure (6 dimensions) and spec quality (5 dimensions)
3. Map Jev scores to 0–10, compute weights
4. Ask Claude to write markdown explanations
5. Output: `reports/team-X.md` with scores + prose + confidence levels

## Get Started (5 min)

```bash
# Install
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repo> && cd scorer_cli
uv sync

# Configure
cp config.yaml.example config.yaml
export TYPESAFE_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
uv run score-cli run-all
```

Output: `reports/team-*.md`

**Full guide:** Read `docs/QUICKSTART.md`

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
| **docs/examples/sample-report.md** | Judges | Example output for a real submission |

## Directory Structure

```
scorer_cli/
├── README.md (this file)
├── CLAUDE.md
├── config.yaml.example
│
├── docs/                        # All documentation
│   ├── INDEX.md                 # Navigation guide
│   ├── HOW_IT_WORKS.md          # Simplified pipeline diagram (for participants)
│   ├── ARCHITECTURE.md          # System design, 3-phase pipeline
│   ├── QUICKSTART.md            # 5-minute first-time user guide
│   ├── HANDOFF.md               # Project handoff summary
│   ├── DEVELOPER_CHECKLIST.md   # Implementation guide
│   │
│   ├── design/                  # Implementation design (for devs)
│   │   ├── structure-scoring.md
│   │   ├── spec-scoring.md
│   │   └── report-generation.md
│   │
│   ├── spec/
│   │   └── rubrics.md           # Complete rubric reference
│   │
│   └── examples/
│       └── sample-report.md     # Example output
│
└── app/                         # Application code
    ├── __main__.py
    ├── scorer.py
    ├── metrics.py
    ├── jev_scorer.py
    ├── scoring_engine.py
    ├── llm_reporter.py
    └── report_generator.py
```

## CLI Commands

```bash
# Score one submission
uv run score-cli run team-a-007

# Score all submissions
uv run score-cli run-all

# Metrics only (no API calls)
uv run score-cli run team-a-007 --dry-run

# Recompute from existing metrics (no API calls)
uv run score-cli recompute reports/metrics/*.json
```

## Key Features

- **Deterministic scoring:** Metrics + Jev + code arithmetic = reproducible results
- **Confidence levels:** Every Jev answer includes confidence (0–1) for judges to prioritize review
- **Fast:** ~4s per submission (Jev <1s each, LLM <2s) vs. 20–60s with older approaches
- **Cheap:** ~4–5 min-tokens per submission (50–60% savings)
- **Fallback:** If LLM fails, auto-generates structured markdown (scores only)
- **Composable:** Change weights in `config.yaml`, recompute all scores in seconds (no API calls needed)

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

See `docs/spec/rubrics.md` for complete rubric.

## Configuration

Copy `config.yaml.example` to `config.yaml` and fill in:

```yaml
typesafe:
  api_key_env: "TYPESAFE_API_KEY"
  api_endpoint: "https://api.typesafe.ai"
  model: "jev-latest"

report_generation:
  api_key_env: "ANTHROPIC_API_KEY"
  model: "claude-opus-5"  # or claude-haiku for cost
  temperature: 0.3
  max_tokens: 2000

weights:
  structure: 0.5
  spec: 0.5
```

Full configuration reference: `docs/ARCHITECTURE.md#configuration-configyaml`

## Input Format

```
submissions/
  team-a-007/
    graph.json      (dependency graph from Graphify)
    source.zip      (source code)
    sdd.zip         (spec documents)
```

## Output Format

```
reports/
  team-a-007.md   (markdown report: scores + prose + confidence)
  metrics/
    team-a-007/
      metrics.json (for reproducibility/recomputation)
```

Example report: `docs/examples/sample-report.md`

## Development

**Implement these modules:**
- `jev_scorer.py` — Jev API calls (6 Score + Choice + 5 Noul)
- `scoring_engine.py` — Map Jev answers to 0–10 scores + weights
- `llm_reporter.py` — Claude API calls for markdown generation
- `report_generator.py` — Write reports to disk, format output

**See:** `docs/DEVELOPER_CHECKLIST.md` (step-by-step)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Modules not found | `uv sync` |
| API keys not set | `export TYPESAFE_API_KEY=... && export ANTHROPIC_API_KEY=...` |
| Jev timeout | Retries automatically; check TypeSafe status if persistent |
| LLM timeout | Falls back to auto-generated markdown (scores only) |
| Missing submission files | Ensure graph.json, source.zip, sdd.zip present |

Full troubleshooting: `docs/QUICKSTART.md#troubleshooting`

## Cost & Performance

| Metric | Value |
|--------|-------|
| Tokens/submission | ~4–5 (was 10) |
| API calls/submission | 3 (2 Jev + 1 LLM) |
| Latency/submission | ~4s (was 20–60s) |
| Cost/50 teams | ~$2 (was $4) |

## For Judges

Reports contain:
- **Score:** 0–10 rating per dimension
- **Level:** 1–5 qualitative level (Critical → Excellent)
- **Confidence:** 0–1 (how sure Jev is)
- **Justification:** 2–3 sentences explaining the score

**Use confidence to prioritize manual review:** Low confidence (<0.5) on critical dimensions means ambiguous signal → review manually.

Example: `docs/examples/sample-report.md`

## Next Steps

1. **New to scorer_cli?** → Read `docs/QUICKSTART.md` (5 min)
2. **Want to understand architecture?** → Read `docs/ARCHITECTURE.md`
3. **Going to implement it?** → Read `docs/DEVELOPER_CHECKLIST.md`
4. **Want to judge submissions?** → Read `docs/examples/sample-report.md` + `docs/spec/rubrics.md`

## License

[License TBD]

## Support

- Questions? → Check `docs/QUICKSTART.md` or `docs/INDEX.md`
- Bug? → Check logs at `scorer.log`
- Contributing? → See `CONTRIBUTING.md` (TBD)
