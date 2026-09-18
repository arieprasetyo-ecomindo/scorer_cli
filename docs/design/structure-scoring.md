# Structure Scoring: 6 Jev Score Primitives

This document defines the 6 **Score** primitives used to judge code structure quality.

## Overview

Each dimension is scored 1–5 (Critical → Excellent). Jev returns:
- Top level (1–5)
- Confidence (0–1)

Code then maps: Level 1→0, Level 2→2.5, Level 3→5, Level 4→7.5, Level 5→10.

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

**Criteria:**
- **Level 5 (Excellent):** max fan-in/out within ~2× average (no hotspots)
- **Level 4 (Good):** One or two hotspot nodes (3–4× avg); not dominant
- **Level 3 (Fair):** Several hotspots (5–7× avg); some god-modules
- **Level 2 (Poor):** Pervasive high coupling (max fan-in/out > 7× avg)
- **Level 1 (Critical):** Tangled mess (max fan-in/out > 10× avg)

**Key metrics:** `avg_fan_in`, `max_fan_in`, `avg_fan_out`, `max_fan_out`

---

## Question 2: Circular Dependencies

**ID:** `circular_dependencies`

**Criteria:**
- **Level 5 (Excellent):** Zero cycles
- **Level 4 (Good):** 1 isolated cycle (non-core area)
- **Level 3 (Fair):** 2–3 cycles
- **Level 2 (Poor):** 4–6 cycles
- **Level 1 (Critical):** >6 cycles or spanning multiple core modules

**Key metric:** `circular_dependencies` array length

---

## Question 3: Dependency Depth

**ID:** `dependency_depth`

**Criteria:**
- **Level 5 (Excellent):** Longest path ≤ log(node_count) × 2 (baseline)
- **Level 4 (Good):** Path 1.5–2× baseline
- **Level 3 (Fair):** Path 2–4× baseline
- **Level 2 (Poor):** Path 4–6× baseline
- **Level 1 (Critical):** Path >> baseline (spaghetti-like)

**Key metrics:** `longest_dependency_path`, `node_count`

**Example:** 87 nodes → baseline ≈ log(87)×2 ≈ 8.5. Path of 5 is good (Level 4). Path of 15 is poor (Level 2).

---

## Question 4: Cyclomatic Complexity

**ID:** `cyclomatic_complexity`

**Criteria:**
- **Level 5 (Excellent):** avg CCN ≤ 4, no function above 10
- **Level 4 (Good):** avg CCN 4–7, < 5% above threshold (CCN > 10)
- **Level 3 (Fair):** avg CCN 7–12, or 5–15% above threshold
- **Level 2 (Poor):** avg CCN > 12 or > 15% above threshold
- **Level 1 (Critical):** avg CCN >> 15 + max CCN > 20

**Key metrics:** `avg_cyclomatic_complexity`, `max_cyclomatic_complexity`, `functions_above_complexity_threshold` (count & percentage)

---

## Question 5: Function Size Discipline

**ID:** `function_size_discipline`

**Criteria:**
- **Level 5 (Excellent):** avg NLOC ≤ 20, avg params ≤ 3
- **Level 4 (Good):** avg NLOC 20–40, avg params 3–4
- **Level 3 (Fair):** avg NLOC 40–70, avg params 4–6
- **Level 2 (Poor):** avg NLOC > 70 or avg params > 6
- **Level 1 (Critical):** avg NLOC >> 100 or avg params >> 8

**Key metrics:** `avg_function_length_nloc`, `avg_parameter_count`

---

## Question 6: Betweenness Centrality (Architectural Bottlenecks)

**ID:** `betweenness_centrality`

**Criteria:**
- **Level 5 (Excellent):** max/avg ratio < 3 (no single point of failure)
- **Level 4 (Good):** ratio 3–6; top nodes plausibly legitimate (server.js, main, router)
- **Level 3 (Fair):** ratio 6–15; pronounced bottleneck
- **Level 2 (Poor):** ratio 15–30 or multiple nodes at 10–15×
- **Level 1 (Critical):** ratio > 30× or severe multi-node bottlenecks

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
structure_score = Σ(level_to_score[level_i] × weight_i)
where level_to_score = {1: 0, 2: 2.5, 3: 5, 4: 7.5, 5: 10}
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

```python
from typesafe import jev_client

questions = [
    {
        "id": "coupling",
        "type": "score",
        "instructions": "Rate the severity of coupling (interdependencies)...",
        "state": metrics_state,
        "criteria": [
            {"level": 1, "description": "Pervasive high coupling (max > 10× avg)"},
            {"level": 2, "description": "Several god-modules; high coupling"},
            {"level": 3, "description": "One or two hotspots; moderate"},
            {"level": 4, "description": "Isolated hotspots; mostly even"},
            {"level": 5, "description": "Low, even coupling; excellent"},
        ]
    },
    # ... (questions 2–6, similar structure)
]

response = jev_client.ask(model="jev", questions=questions)

for q_id, answer in response.items():
    level = answer.level  # 1–5
    confidence = answer.confidence  # 0–1
    score_0_10 = (level - 1) * 2.5
    print(f"{q_id}: Level {level} ({confidence:.0%}) → {score_0_10}")
```

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
