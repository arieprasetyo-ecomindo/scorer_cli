# Structure Scoring: 6 Jev Score Primitives

This document defines the 6 **Score** primitives used to judge code structure quality.

## Overview

Each dimension has 5 rubric levels, Critical → Excellent. Via the real `typesafe-sdk`
package, each is a `Score` question whose `criteria` is an ordered list of 5 level
descriptions, indexed 0 (Critical) through 4 (Excellent) — the SDK is zero-indexed,
not 1–5.

Jev's `ScoreAnswer` returns:
- **`score`** (float): a *continuous*, probability-weighted average over the 5
  levels (e.g. `3.4`, not a single picked level)
- **`confidence`** (float, 0–1): a separate certainty measure
- **`legend`** (`dict[int, str]`): the criteria text, keyed by level index
- **`probabilities`** (`dict[int, float]`): likelihood of each level

Code rescales `score` (0..4) to 0..10 for reporting:
`score_0_10 = score / (num_levels - 1) * 10` — e.g. `score=4` → `10`, `score=2` → `5`.
For display, we also derive a nearest integer level via `round(score)` and label it
from `legend`, but the underlying value used for weighting is the continuous score,
not the rounded level.

See `app/jev_scorer.py` for the implementation.

## Input State

All 6 questions receive the same state:

```json
{
  "submission_id": "string",
  "graph_metrics": {
    "node_count": number,
    "avg_fan_in": number,
    "max_fan_in": number,
    "avg_fan_out": number,
    "max_fan_out": number,
    "longest_dependency_path": number,
    "circular_dependencies": [["moduleA", "moduleB", "moduleA"], ...],
    "modularity_score": number,
    "avg_betweenness_centrality": number,
    "max_betweenness_centrality": number,
    "top_betweenness_nodes": [{"node": "string", "betweenness": number}, ...]
  },
  "complexity_metrics": {
    "total_functions": number,
    "avg_cyclomatic_complexity": number,
    "max_cyclomatic_complexity": number,
    "functions_above_complexity_threshold": [
      {"name": "string", "file": "string", "ccn": number, "nloc": number}, ...
    ],
    "avg_function_length_nloc": number,
    "avg_parameter_count": number
  }
}
```

---

## Question 1: Coupling

**ID:** `coupling`

**Criteria** (index: label):
- **4 (Excellent):** max fan-in/out within ~2× average (no hotspots)
- **3 (Good):** One or two hotspot nodes (3–4× avg); not dominant
- **2 (Fair):** Several hotspots (5–7× avg); some god-modules
- **1 (Poor):** Pervasive high coupling (max fan-in/out > 7× avg)
- **0 (Critical):** Tangled mess (max fan-in/out > 10× avg)

**Key metrics:** `avg_fan_in`, `max_fan_in`, `avg_fan_out`, `max_fan_out`

---

## Question 2: Circular Dependencies

**ID:** `circular_dependencies`

**Criteria** (index: label):
- **4 (Excellent):** Zero cycles
- **3 (Good):** 1 isolated cycle (non-core area)
- **2 (Fair):** 2–3 cycles
- **1 (Poor):** 4–6 cycles
- **0 (Critical):** >6 cycles or spanning multiple core modules

**Key metric:** `circular_dependencies` array length

---

## Question 3: Dependency Depth

**ID:** `dependency_depth`

**Criteria** (index: label):
- **4 (Excellent):** Longest path ≤ log(node_count) × 2 (baseline)
- **3 (Good):** Path 1.5–2× baseline
- **2 (Fair):** Path 2–4× baseline
- **1 (Poor):** Path 4–6× baseline
- **0 (Critical):** Path >> baseline (spaghetti-like)

**Key metrics:** `longest_dependency_path`, `node_count`

**Example:** 87 nodes → baseline ≈ log(87)×2 ≈ 8.5. Path of 5 is good (index 3). Path of 15 is poor (index 1).

---

## Question 4: Cyclomatic Complexity

**ID:** `cyclomatic_complexity`

**Criteria** (index: label):
- **4 (Excellent):** avg CCN ≤ 4, no function above 10
- **3 (Good):** avg CCN 4–7, < 5% above threshold (CCN > 10)
- **2 (Fair):** avg CCN 7–12, or 5–15% above threshold
- **1 (Poor):** avg CCN > 12 or > 15% above threshold
- **0 (Critical):** avg CCN >> 15 + max CCN > 20

**Key metrics:** `avg_cyclomatic_complexity`, `max_cyclomatic_complexity`, `functions_above_complexity_threshold` (count & percentage)

---

## Question 5: Function Size Discipline

**ID:** `function_size_discipline`

**Criteria** (index: label):
- **4 (Excellent):** avg NLOC ≤ 20, avg params ≤ 3
- **3 (Good):** avg NLOC 20–40, avg params 3–4
- **2 (Fair):** avg NLOC 40–70, avg params 4–6
- **1 (Poor):** avg NLOC > 70 or avg params > 6
- **0 (Critical):** avg NLOC >> 100 or avg params >> 8

**Key metrics:** `avg_function_length_nloc`, `avg_parameter_count`

---

## Question 6: Betweenness Centrality (Architectural Bottlenecks)

**ID:** `betweenness_centrality`

**Criteria** (index: label):
- **4 (Excellent):** max/avg ratio < 3 (no single point of failure)
- **3 (Good):** ratio 3–6; top nodes plausibly legitimate (server.js, main, router)
- **2 (Fair):** ratio 6–15; pronounced bottleneck
- **1 (Poor):** ratio 15–30 or multiple nodes at 10–15×
- **0 (Critical):** ratio > 30× or severe multi-node bottlenecks

**Important caveat:** Entry points (server.js, main) naturally have high betweenness. Check node *names* — if legitimate role, don't penalize.

**Key metrics:** `max_betweenness_centrality`, `avg_betweenness_centrality`, `top_betweenness_nodes`

---

## Weights

Applied after all 6 questions return:

```yaml
weights:
  coupling: 0.21
  circular_dependencies: 0.17
  dependency_depth: 0.13
  cyclomatic_complexity: 0.21
  function_size_discipline: 0.13
  betweenness_centrality: 0.15
```

**Weighted Total Formula:**
```
score_0_10_i = raw_score_i / (num_levels - 1) * 10   # raw_score_i is Jev's continuous 0..4 score
structure_score = Σ(score_0_10_i × weight_i)
```

---

## Red Flags

Automatically checked (not via Jev) after scoring:

- **Circular dependency > 3 modules:** Check `circular_dependencies` list
- **Function CCN > 20:** Check `functions_above_complexity_threshold`
- **Node fan-in/out > 5× avg:** Check `max_fan_in/out` vs. `avg_fan_in/out`
- **Betweenness centrality > 10× avg:** Check `max_betweenness_centrality` vs. `avg_betweenness_centrality`

---

## Implementation Example

Real package: `typesafe-sdk` (`uv add typesafe-sdk`). Note `typesafe` on PyPI is an
unrelated package — do not install it.

```python
from typesafe_sdk import Score, TypeSafeClient

client = TypeSafeClient()  # reads TYPESAFE_API_KEY; model defaults to "jev-latest"

questions = {
    "coupling": Score(
        instructions="Rate the coupling of this codebase using graph_metrics in state.",
        criteria=[
            "Critical: tangled mess (max > 10x avg)",       # index 0
            "Poor: pervasive high coupling (max > 7x avg)",  # index 1
            "Fair: several hotspots (5-7x avg)",             # index 2
            "Good: one or two hotspots (3-4x avg)",          # index 3
            "Excellent: low, even coupling (~2x avg)",       # index 4
        ],
    ),
    # ... (5 more Score questions, same shape)
}

response = client.system_one(metrics_state, questions)

for dim, answer in response.scores.items():
    score_0_10 = answer.score / (len(questions[dim].criteria) - 1) * 10
    print(f"{dim}: raw={answer.score:.2f} confidence={answer.confidence:.0%} -> {score_0_10:.1f}/10")
```

See `app/jev_scorer.py` for the actual implementation (`score_structure()`).

---

## Debugging Low Confidence

If Jev returns low confidence on a dimension:

- **Coupling:** Check if node has legitimate high fan-in (library, middleware) vs. architectural accident
- **Circular Dependencies:** Ambiguous if cycles touch both core and non-core modules
- **Dependency Depth:** Ambiguous if mixed layering (some deep, some shallow paths)
- **Cyclomatic Complexity:** Ambiguous if one outlier function inflates average
- **Function Size:** Ambiguous if mix of tiny and large functions
- **Betweenness:** Ambiguous if top nodes have mixed roles

**Action:** Flag low-confidence dimensions for judge manual review.
