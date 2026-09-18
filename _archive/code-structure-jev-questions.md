# Jev Questions: Code Structure Scoring

These six **Score** primitives rate code structure quality across the original rubric dimensions. All run **in parallel** against the same metrics state.

## Input State

```json
{
  "submission_id": "string",
  "graph_metrics": {
    "node_count": number,
    "edge_count": number,
    "avg_fan_in": number,
    "avg_fan_out": number,
    "max_fan_in": number,
    "max_fan_out": number,
    "longest_dependency_path": number,
    "circular_dependencies": [["moduleA", "moduleB", "moduleA"], ...],
    "orphan_nodes": ["string", ...],
    "modularity_score": number,
    "avg_betweenness_centrality": number,
    "max_betweenness_centrality": number,
    "top_betweenness_nodes": [
      {"node": "string", "betweenness": number}, ...
    ]
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

## Question 1: Coupling

**Question ID:** `coupling`

**Instructions:**
Rate the severity of coupling (interdependencies between modules). Low coupling is good; high coupling (god-modules, tangled responsibilities) is bad.

Reference `graph_metrics.avg_fan_in`, `graph_metrics.avg_fan_out`, `graph_metrics.max_fan_in`, `graph_metrics.max_fan_out`.

Use this calibration:
- **Level 5 (Excellent):** Low, even coupling; max fan-in/out within ~2× average (no hotspots).
- **Level 4 (Good):** Moderate coupling; one or two hotspot nodes but not dominant. Max fan-in/out within ~3–4× average.
- **Level 3 (Fair):** Several high fan-in/fan-out nodes suggesting god-modules. Max fan-in/out within 5–7× average.
- **Level 2 (Poor):** Pervasive high coupling; most nodes densely interconnected. Max fan-in/out > 7× average, or avg fan-in/out > 3.
- **Level 1 (Critical):** Extreme coupling everywhere; the codebase is a tangled mess.

**Criteria:**
- Level 1: Pervasive high coupling (max fan-in/out > 10× avg)
- Level 2: Several hotspots, avg fan-in/out > 2.5
- Level 3: One or two hotspots, 3–5× avg
- Level 4: Isolated hotspots, ~2× avg
- Level 5: Low, even coupling

---

## Question 2: Circular Dependencies

**Question ID:** `circular_dependencies`

**Instructions:**
Rate the problem severity of circular dependencies (modules depending on each other in loops). Zero cycles is best; many cycles or cycles involving core modules are problematic.

Reference `graph_metrics.circular_dependencies` (list of cycles).

Use this calibration:
- **Level 5 (Excellent):** Zero cycles.
- **Level 4 (Good):** 1 cycle, isolated to a minor/non-core area.
- **Level 3 (Fair):** 2–3 cycles, or a cycle involving one core module (but not spanning multiple).
- **Level 2 (Poor):** 4+ cycles, or a cycle spanning large parts of the graph.
- **Level 1 (Critical):** Many cycles (>10) or cycles involving all major modules.

**Criteria:**
- Level 1: > 6 cycles
- Level 2: 4–6 cycles
- Level 3: 2–3 cycles
- Level 4: 1 cycle
- Level 5: 0 cycles

---

## Question 3: Dependency Depth

**Question ID:** `dependency_depth`

**Instructions:**
Rate whether the longest dependency chain is appropriate for the project size. Deep chains (A→B→C→D→...) suggest poor layering and harder-to-understand data flow.

Reference `graph_metrics.longest_dependency_path` and `graph_metrics.node_count`.

Baseline: suitable depth is roughly ≤ log(node_count) × 2.

Use this calibration:
- **Level 5 (Excellent):** Shallow, flat structure; path length ≤ baseline.
- **Level 4 (Good):** Reasonable depth; path length slightly above baseline, but few deep chains.
- **Level 3 (Fair):** Notably deep chains; path length 2–3× baseline.
- **Level 2 (Poor):** Excessively deep chains; path length > 4× baseline.
- **Level 1 (Critical):** Spaghetti-like; no clear layering; path length >> baseline.

**Criteria:**
- Level 1: Longest path > 10 or > 6× baseline
- Level 2: Longest path 8–10 or 4–6× baseline
- Level 3: Longest path 5–7 or 2–4× baseline
- Level 4: Longest path 3–5 or ~1.5× baseline
- Level 5: Longest path ≤ 3 or ≤ baseline

---

## Question 4: Cyclomatic Complexity

**Question ID:** `cyclomatic_complexity`

**Instructions:**
Rate the manageability of cyclomatic complexity (CCN) across all functions. High CCN means more branching paths; harder to test and reason about.

Reference `complexity_metrics.avg_cyclomatic_complexity`, `complexity_metrics.max_cyclomatic_complexity`, and `complexity_metrics.functions_above_complexity_threshold` (threshold = CCN > 10).

Use this calibration:
- **Level 5 (Excellent):** avg CCN ≤ 4, no function above 10.
- **Level 4 (Good):** avg CCN 4–7, < 5% of functions above threshold.
- **Level 3 (Fair):** avg CCN 7–12, or 5–15% of functions above threshold.
- **Level 2 (Poor):** avg CCN > 12, or > 15% of functions above threshold.
- **Level 1 (Critical):** avg CCN >> 15 or > 25% of functions above threshold, with some functions CCN > 20.

**Criteria:**
- Level 1: avg CCN > 12 + max CCN > 20
- Level 2: avg CCN > 12 or > 15% above threshold
- Level 3: avg CCN 7–12 or 5–15% above threshold
- Level 4: avg CCN 4–7 and < 5% above threshold
- Level 5: avg CCN ≤ 4 and 0 above threshold

---

## Question 5: Function Size Discipline

**Question ID:** `function_size_discipline`

**Instructions:**
Rate the discipline of function sizing and parameter count. Small, focused functions are good; long functions with many parameters are hard to understand and test.

Reference `complexity_metrics.avg_function_length_nloc` and `complexity_metrics.avg_parameter_count`.

Use this calibration:
- **Level 5 (Excellent):** avg NLOC ≤ 20, avg params ≤ 3.
- **Level 4 (Good):** avg NLOC 20–40, avg params 3–4.
- **Level 3 (Fair):** avg NLOC 40–70, avg params 4–6.
- **Level 2 (Poor):** avg NLOC > 70 or avg params > 6.
- **Level 1 (Critical):** avg NLOC >> 100 or avg params >> 8; functions are unwieldy.

**Criteria:**
- Level 1: avg NLOC > 100 or avg params > 8
- Level 2: avg NLOC > 70 or avg params > 6
- Level 3: avg NLOC 40–70 or avg params 4–6
- Level 4: avg NLOC 20–40 and avg params 3–4
- Level 5: avg NLOC ≤ 20 and avg params ≤ 3

---

## Question 6: Betweenness Centrality — Architectural Bottlenecks

**Question ID:** `betweenness_centrality`

**Instructions:**
Rate whether a small number of nodes sit on most shortest paths between other nodes. This identifies architectural single points of failure.

Reference `complexity_metrics.max_betweenness_centrality`, `complexity_metrics.avg_betweenness_centrality`, and `complexity_metrics.top_betweenness_nodes`.

**Important:** Legitimate entry points (e.g., `server.js`, `main`, a router) naturally have high betweenness by design. Do **not** penalize them for this. Only flag bottlenecks that represent genuine design problems (e.g., a utility module unexpectedly central, a business logic module that shouldn't be central).

Check the node names in `top_betweenness_nodes`. If they are entry points or legitimate shared utilities, rate generously (Level 4–5). If they are unexpected hotspots, rate based on the severity of the ratio.

Use this calibration:
- **Level 5 (Excellent):** No node dominates shortest paths; max/avg ratio < 3.
- **Level 4 (Good):** One or two nodes clearly above average (3–6× avg), but plausibly legitimate entry points or shared utilities.
- **Level 3 (Fair):** A node's betweenness is 6–15× the average; a pronounced single point of architectural failure.
- **Level 2 (Poor):** A node's betweenness is 15–30× average, or multiple nodes show this pattern.
- **Level 1 (Critical):** Betweenness >> 30× average; severe bottleneck risk.

**Criteria:**
- Level 1: max/avg > 30 or multiple nodes > 15×
- Level 2: max/avg 15–30 or > 3 nodes > 10×
- Level 3: max/avg 6–15
- Level 4: max/avg 3–6 (and node names suggest legitimate role)
- Level 5: max/avg < 3

---

## Code Integration Example

```python
from typesafe import jev_client

# Prepare state from metrics.json
state = load_metrics_json("metrics.json")

# Build all six questions
questions = [
    {
        "id": "coupling",
        "instructions": "Rate the severity of coupling...",
        "state": state,
        "criteria": [
            {"level": 1, "description": "Pervasive high coupling (max fan-in/out > 10× avg)"},
            ...
        ]
    },
    # ... (questions 2–6)
]

# Call Jev once (all questions run in parallel)
response = jev_client.ask(
    model="jev",
    questions=questions
)

# Extract scores and map Level 1–5 → 0–10
for q_id, answer in response.items():
    level = answer.top_level  # 1, 2, 3, 4, or 5
    confidence = answer.confidence  # 0–1
    score_0_10 = (level - 1) * 2.5  # 0, 2.5, 5, 7.5, 10
    print(f"{q_id}: Level {level} ({confidence:.2%}) → {score_0_10}")
```

---

## Notes

- All six questions run in **parallel** in a single API call.
- Jev returns a probability distribution over each level; code takes the top level (argmax) and its confidence.
- If a metric is null or missing (e.g., no functions found by Lizard), that question can be set to skip in the Jev state.
- Confidence can guide manual review priority: low confidence on a critical dimension may warrant closer human inspection.
