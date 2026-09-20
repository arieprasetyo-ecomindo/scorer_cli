# Structure Scoring: Deterministic, No Jev

This document defines how the 6 structure (code quality) dimensions are scored.

## Why Not Jev?

Every one of these 6 dimensions already has an exact numeric rubric (see `docs/spec/rubrics.md`)
— e.g. "avg CCN <= 4 -> Excellent" is a lookup-table classification, not a judgment call. Running
that through an LLM/Jev added cost, latency, an external dependency, and non-reproducibility for
no real benefit. Jev is reserved for `docs/design/spec-scoring.md`'s Spec Quality dimensions,
where the input is unstructured prose and genuine judgment is actually required.

See `app/structure_scorer.py` for the implementation — this doc mirrors it.

## How It Works

Each dimension has 5 levels, indexed 0 (Critical) through 4 (Excellent). A classifier function
buckets the relevant metric(s) into one of those 5 levels using fixed thresholds, then:

```
score_0_10 = level / 4 * 10   # 0, 2.5, 5, 7.5, or 10 - a discrete bucket, not interpolated
```

Discrete buckets (rather than interpolating within a level) are deliberate: it keeps scoring
fully transparent and auditable — anyone can look at a metric value and the threshold table and
know exactly which bucket it falls into and why.

There's no "confidence" value for structure scores, unlike spec scores — a deterministic rule
has no genuine uncertainty to report. Fabricating one (e.g. always 100%) would be misleading.

## Input

Each classifier reads directly from `graph_metrics` (NetworkX) and/or `complexity_metrics`
(Lizard) — see `app/metrics.py`. No combined "state" object or API call is needed.

---

## 1. Coupling

**Function:** `score_coupling(graph_metrics)`

```
avg_val = max(avg_fan_in, avg_fan_out)
max_val = max(max_fan_in, max_fan_out)
ratio = max_val / avg_val   (0 if avg_val == 0)

if avg_val > 2.5: level = 0        # Critical, regardless of ratio
elif ratio <= 2:  level = 4        # Excellent
elif ratio <= 4:  level = 3        # Good
elif ratio <= 7:  level = 2        # Fair
elif ratio <= 10: level = 1        # Poor
else:             level = 0        # Critical
```

---

## 2. Circular Dependencies

**Function:** `score_circular_dependencies(graph_metrics)`

```
count = len(circular_dependencies)

count == 0:        level = 4  # Excellent
count == 1:        level = 3  # Good
2 <= count <= 3:   level = 2  # Fair
4 <= count <= 6:   level = 1  # Poor
count > 6:         level = 0  # Critical
```

---

## 3. Dependency Depth

**Function:** `score_dependency_depth(graph_metrics)`

```
baseline = ln(node_count) * 2   (1 if node_count <= 1)
ratio = longest_dependency_path / baseline

ratio <= 1: level = 4   # Excellent
ratio <= 2: level = 3   # Good
ratio <= 4: level = 2   # Fair
ratio <= 6: level = 1   # Poor
else:       level = 0   # Critical
```

---

## 4. Cyclomatic Complexity

**Function:** `score_cyclomatic_complexity(complexity_metrics)`

```
pct_above = count(functions_above_complexity_threshold) / total_functions * 100  (0 if no functions)

level_from_avg:  avg_ccn<=4 -> 4, <=7 -> 3, <=12 -> 2, <=15 -> 1, else 0
level_from_pct:  pct==0 -> 4, <5 -> 3, <15 -> 2, <25 -> 1, else 0

level = min(level_from_avg, level_from_pct)   # the worse signal wins
```

---

## 5. Function Size Discipline

**Function:** `score_function_size_discipline(complexity_metrics)`

```
level_from_nloc:   avg_nloc<=20 -> 4, <=40 -> 3, <=70 -> 2, <=100 -> 1, else 0
level_from_params: avg_params<=3 -> 4, <=4 -> 3, <=6 -> 2, <=8 -> 1, else 0

level = min(level_from_nloc, level_from_params)   # the worse signal wins
```

---

## 6. Betweenness Centrality

**Function:** `score_betweenness_centrality(graph_metrics)`

```
ratio = max_betweenness_centrality / avg_betweenness_centrality   (0 if avg == 0)

ratio <= 3:  level = 4   # Excellent
ratio <= 6:  level = 3   # Good
ratio <= 15: level = 2   # Fair
ratio <= 30: level = 1   # Poor
else:        level = 0   # Critical
```

**Known simplification:** the rubric's caveat ("entry points like `server.js`/`main` naturally
have high betweenness — check node names before penalizing") is not implemented. This classifier
scores purely on the ratio; it doesn't special-case filenames. Worth revisiting if this causes
false positives on real submissions.

---

## Weights

```yaml
weights:
  coupling: 0.21
  circular_dependencies: 0.17
  dependency_depth: 0.13
  cyclomatic_complexity: 0.21
  function_size_discipline: 0.13
  betweenness_centrality: 0.15
```

```
structure_score = Σ(score_0_10_i × weight_i)
```

## Red Flags

Checked separately in `app/report_generator.py`, using thresholds from `config.yaml`'s
`red_flags` section (not hardcoded):

- Circular dependency touching more than `circular_deps_involving_more_than` modules
- Function CCN above `max_ccn_threshold`
- Node fan-in/out above `fan_coupling_multiple` × average
- Node betweenness above `betweenness_multiple` × average
