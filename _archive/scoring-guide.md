# Scoring Guide — How to Read a Report

This document is for **judges**, not the LLM. It explains what the numbers in `reports/<team>.md` mean and how much weight to put on them. For how the scores are *produced*, see `code-structure-scoring-instructions.md`, `spec-scoring-instructions.md`, and `specs/001-mvp.md`.

## The big picture

Every report has three numbers:

```
structure_weighted_total   (0–10, from 6 dimensions — code/graph metrics)
spec_weighted_total         (0–10, from 5 dimensions — SDD document quality)
combined_score               (0–10, weighted average of the two — see config.yaml: weights.combined)
```

**Treat `combined_score` as a starting point for discussion, not a verdict.** It's a deterministic weighted sum of two independent LLM judgments, each grounded in different evidence (numeric metrics vs. spec text). It cannot see whether the app actually works, so a high score does not mean "good submission" on its own — pair it with a quick look at the demo.

## Score bands (all dimensions and totals, 0–10 scale)

| Range | Meaning |
|---|---|
| 9.0–10 | Excellent — no notable issues found in what this rubric can see |
| 7.0–8.9 | Good — solid, minor issues that wouldn't block shipping |
| 5.0–6.9 | Fair — real issues present; worth a closer look before ranking highly |
| 3.0–4.9 | Poor — significant problems in this dimension |
| 0–2.9 | Critical — this dimension is a strong signal something is wrong |

These bands are consistent across both rubrics, so a 6.5 means the same rough thing whether it's a structure dimension or a spec dimension.

## Structure dimensions — what a low score means, and what to check

| Dimension | Weight | Low score suggests | Worth manually checking? |
|---|---|---|---|
| Coupling | 21% | Some modules depend on/are depended on by many others (god-modules) | Open the flagged `max_fan_in`/`max_fan_out` node — is it a genuine shared utility or a design smell? |
| Circular Dependencies | 17% | Modules depend on each other in a loop | Look at the `circular_dependencies` list directly — cycles are usually unambiguous problems |
| Dependency Depth | 13% | Long chains of dependencies (A→B→C→D→...) relative to project size | Usually low-stakes for a 3-hour hackathon project; don't weight this heavily in final judging |
| Cyclomatic Complexity | 21% | Functions with many branching paths — harder to test and reason about | Check `functions_above_complexity_threshold` — read the specific function if the score is below 5 |
| Function Size Discipline | 13% | Long functions and/or many parameters | Lower priority given hackathon time constraints; a few long functions under time pressure is normal |
| Betweenness Centrality | 15% | A small number of nodes sit on most paths between other parts of the system — architectural bottlenecks | **Check the node's name first.** An entry point (`server.js`, `main`, a router) is *expected* to have high betweenness — the LLM is instructed to account for this, but verify the justification actually reasons about it rather than penalizing blindly |

## Spec dimensions — what a low score means, and what to check

| Dimension | Weight | Low score suggests | Worth manually checking? |
|---|---|---|---|
| Clarity & Testability | 25% | Requirements are vague or unfalsifiable | Skim the spec yourself — is "handle errors well" the kind of language used throughout? |
| Scope Boundary | 15% | Unclear what was in/out of scope for the MVP | Lower-stakes; mostly informs whether the team planned deliberately |
| Internal Consistency | 15% | Spec contradicts itself | Check the specific contradiction cited in the justification |
| Traceability | 25% | Spec doesn't match the actual codebase structure | **Important one** — read the `codebase_modules` match/mismatch list in the justification; this is the closest proxy this rubric has to "did they actually practice SDD" |
| Substance Over Polish | 20% | Well-formatted but low-content spec | If this scores low alongside high Clarity/Testability, treat that as a contradiction worth a manual look — it suggests the LLM may be inconsistent |

## Red flags

`red_flags` is a list of specific conditions the LLM checks regardless of how they affected the numeric score (e.g. "a node's betweenness centrality is 12x the graph average," or "spec has fewer than 2 codebase_modules mentioned"). **Always read this list, even for high-scoring submissions** — a submission can have a good weighted average while still tripping a flag worth a human look. Treat flags as "go verify this," not "penalize this."

## What this scoring cannot tell you

- Whether the app actually runs or solves the stated problem
- Code readability, naming quality, or style (deliberately out of scope — see `code-structure-scoring-instructions.md`)
- Whether the spec was genuinely written before the code, or reconstructed afterward (the LLM can only flag it as a *possibility* based on tone, not confirm it)
- Anything about team collaboration, presentation, or demo quality

Use these scores to **narrow down which submissions deserve a closer manual look**, not to auto-rank the leaderboard.
