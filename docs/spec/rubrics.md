# Scoring Rubrics — Reference

This is the unified rubric reference for all 11 scoring dimensions (6 structure + 5 spec).

## Structure Dimensions (Code Quality)

### 1. Coupling (Weight 21%)

**Definition:** Interdependencies between modules (how much they depend on each other).

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Low, even coupling; max fan-in/out within ~2× average. No architectural hotspots. |
| **4** | **7.5** | Moderate coupling; one or two hotspot nodes (3–4× avg) but not dominant. |
| **3** | **5** | Several high fan-in/fan-out nodes (5–7× avg) suggesting god-modules or tangled responsibility. |
| **2** | **2.5** | Pervasive high coupling; most nodes densely interconnected (max > 7× avg). |
| **1** | **0** | Extreme coupling; tangled mess (max > 10× avg or avg fan-in/out > 2.5). |

**Key metrics:** avg_fan_in, max_fan_in, avg_fan_out, max_fan_out

**Red flag:** Any node with fan-in/out > 5× graph average.

---

### 2. Circular Dependencies (Weight 17%)

**Definition:** Modules depending on each other in loops (bad for modularity).

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Zero cycles. Perfect architectural discipline. |
| **4** | **7.5** | One isolated cycle in non-core area. Acceptable. |
| **3** | **5** | 2–3 cycles or one cycle involving a core module. Worth fixing but not critical. |
| **2** | **2.5** | 4–6 cycles or cycles spanning large portions of graph. Needs refactoring. |
| **1** | **0** | >6 cycles or cycles involving multiple core modules. Architectural problem. |

**Key metric:** count of cycles in circular_dependencies list

**Red flag:** Any cycle touching > 3 modules.

---

### 3. Dependency Depth / Layering (Weight 13%)

**Definition:** Longest chain of dependencies (A→B→C→D→...).

Suitable depth ≈ log(node_count) × 2. For 87 nodes, ≈ 8.5.

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Longest path ≤ baseline. Shallow, flat structure. |
| **4** | **7.5** | Path 1.5–2× baseline. Reasonable depth. |
| **3** | **5** | Path 2–4× baseline. Notably deep chains; poor layering visible. |
| **2** | **2.5** | Path 4–6× baseline. Excessively deep; hard to trace data flow. |
| **1** | **0** | Path >> baseline; spaghetti-like with no clear layers. |

**Key metrics:** longest_dependency_path, node_count

---

### 4. Cyclomatic Complexity (Weight 21%)

**Definition:** Function complexity (branching paths). Higher = harder to test.

Threshold: CCN > 10 is "too complex."

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | avg CCN ≤ 4, no function above 10. Excellent discipline. |
| **4** | **7.5** | avg CCN 4–7, < 5% of functions above threshold. Good. |
| **3** | **5** | avg CCN 7–12 or 5–15% above threshold. Fair, some complex functions. |
| **2** | **2.5** | avg CCN > 12 or > 15% above threshold. Too many complex functions. |
| **1** | **0** | avg CCN >> 15 or > 25% above threshold, with some functions CCN > 20. Critical. |

**Key metrics:** avg_cyclomatic_complexity, max_cyclomatic_complexity, count of functions above threshold

**Red flag:** Any function with CCN > 20.

---

### 5. Function Size Discipline (Weight 13%)

**Definition:** Function length (NLOC) and parameter count. Smaller, fewer params = better.

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | avg NLOC ≤ 20, avg params ≤ 3. Excellent small functions. |
| **4** | **7.5** | avg NLOC 20–40, avg params 3–4. Good discipline. |
| **3** | **5** | avg NLOC 40–70, avg params 4–6. Fair, some large functions. |
| **2** | **2.5** | avg NLOC > 70 or avg params > 6. Unwieldy functions. |
| **1** | **0** | avg NLOC >> 100 or avg params >> 8. Functions are hard to understand. |

**Key metrics:** avg_function_length_nloc, avg_parameter_count

---

### 6. Betweenness Centrality (Weight 15%)

**Definition:** Whether a small number of nodes sit on most shortest paths (architectural bottlenecks).

**Important:** Entry points (server.js, main) naturally have high betweenness. Check node names before penalizing.

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | max/avg ratio < 3. No single point of failure; evenly distributed. |
| **4** | **7.5** | Ratio 3–6; one or two nodes clearly above avg but plausibly legitimate (entry points, shared utils). |
| **3** | **5** | Ratio 6–15; pronounced single point of architectural failure. |
| **2** | **2.5** | Ratio 15–30 or multiple nodes > 10×. Severe bottleneck risk. |
| **1** | **0** | Ratio > 30× or severe multi-node bottlenecks spanning whole system. Critical risk. |

**Key metrics:** max_betweenness_centrality, avg_betweenness_centrality, top_betweenness_nodes names

**Red flag:** Any node with betweenness > 10× average (unless it's server.js or similar entry point).

---

## Spec Dimensions (SDD Quality)

### 1. Clarity & Testability (Weight 25%)

**Definition:** Are requirements stated concretely enough that someone could verify whether they were met?

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Requirements are specific and testable (e.g., "API returns 400 on missing email field"). >80% of requirements are falsifiable. |
| **4** | **7.5** | Mostly concrete; a few vague or unverifiable statements. 70–80% testable. |
| **3** | **5** | Roughly half testable, half aspirational. Mixed signals. |
| **2** | **2.5** | Mostly vague ("handle errors well", "be user-friendly"). Few concrete requirements. |
| **1** | **0** | Requirements are almost entirely vague, marketing-style, or missing. |

**Red flags:** "Handle", "manage", "support", "robust", "intuitive" without specifics.

---

### 2. Scope Boundary (Weight 15%)

**Definition:** Does the spec say what's in scope and what's explicitly out?

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Clear in-scope/out-of-scope statement. No ambiguity. |
| **4** | **7.5** | Scope is inferable from document structure, not explicitly stated. Clear enough. |
| **3** | **5** | Scope unclear in places; reader would have to guess MVP vs. future. |
| **2** | **2.5** | Scope mostly undefined; features could be either. |
| **1** | **0** | No discernible scope boundary at all. |

**Example of Level 5:** "MVP Goals: auth, user profiles, checkout flow. Future (out of scope): admin panel, analytics."

---

### 3. Internal Consistency (Weight 15%)

**Definition:** Do requirements, data models, and described behavior agree with each other within the document?

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | No contradictions found. Completely coherent. |
| **4** | **7.5** | One minor inconsistency (e.g., field named differently in two places, but meaning is clear). |
| **3** | **5** | Multiple minor inconsistencies or one contradiction in non-core behavior. |
| **2** | **2.5** | Several contradictions or one in core behavior. Spec contradicts itself noticeably. |
| **1** | **0** | Spec substantially contradicts itself. Major incoherence. |

**Example of red flag:** "Users can delete their own posts" (Section 2) vs. "Only admins can delete posts" (Section 5).

---

### 4. Traceability (Weight 25%)

**Definition:** Compare spec against codebase. Does the spec's described structure plausibly map to actual files?

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Most named components in spec have clear mapping to codebase_modules. Little in codebase is unaccounted for. >80% overlap. |
| **4** | **7.5** | Reasonable overlap; a few spec components lack obvious file match, or vice versa. 70–80% mapped. |
| **3** | **5** | Weak overlap; spec describes system that only loosely resembles actual files. 50–70% mapped. |
| **2** | **2.5** | Very weak overlap. Spec and codebase appear largely disconnected. <50% mapped. |
| **1** | **0** | Spec and codebase are completely disconnected or spec is generic boilerplate. No mapping. |

**Note:** This is a **plausibility check**, not correctness proof. We can't verify behavior, only structure.

**Example of Level 5:** Spec mentions "mail service", "user database", "checkout processor" → codebase has libs/mailer.js, models/user.js, checkout/processor.js.

---

### 5. Substance Over Polish (Weight 20%)

**Definition:** Distinguish "well-written" from "well-specified." Does the spec have real content?

| Level | Score | Criteria |
|-------|-------|----------|
| **5** | **10** | Substantive content regardless of formatting. Even plain, unpolished spec with concrete detail scores well. >70% substantive. |
| **4** | **7.5** | Solid substance with reasonable presentation. 60–70% substantive. |
| **3** | **5** | Noticeably balanced between detail and filler. 50–60% substantive. |
| **2** | **2.5** | More polish than content; padded or templated sections. <50% substantive. |
| **1** | **0** | High production value (glossy, lots of headers, graphics) masking very little concrete information. |

**Red flags:** Repeated phrases ("we will build a great product"), no specific requirements, buzzwords without detail.

**Example of Level 5:** Plain-text spec with API contracts, data models, specific requirements (no formatting).

**Example of Level 1:** 30-page glossy document with "we will provide excellent service" in 5 different ways, no actual requirements.

---

## Combined Score Formula

```
structure_weighted_total = Σ(score_i × weight_i) for i in [1, 6]
spec_weighted_total = Σ(score_i × weight_i) for i in [7, 11]

combined_score = (structure_weighted_total × 0.5) + (spec_weighted_total × 0.5)
# Both equally weighted; adjust in config.yaml if needed
```

---

## Confidence Interpretation

Each Jev answer comes with confidence (0–1). For the 6 structure dimensions (Score
primitives), this confidence is returned directly by Jev alongside a continuous
score. For the 5 spec dimensions (Noul primitives), Jev returns only a single
yes-probability; code derives both the yes/no answer and this confidence from it
(`confidence = abs(probability - 0.5) * 2`) — see `docs/design/spec-scoring.md`.

| Confidence Range | Meaning |
|------------------|---------|
| **0.85–1.0** | Very clear signal. Metrics/spec strongly support the rating. |
| **0.70–0.85** | Clear signal with some ambiguity. Most evidence points one way. |
| **0.50–0.70** | Weak signal. Mixed evidence; worth manual inspection. |
| **< 0.50** | Very ambiguous. Jev found conflicting signals. Must review manually. |

**Action for judges:** If average confidence on a submission is < 0.60, that submission needs manual review regardless of score.

---

## Red Flags (Automatic Checks)

Checked after scoring, independent of dimension scores:

**Structure:**
- Any cycle touching > 3 modules
- Any function CCN > 20
- Any node fan-in/out > 5× average
- Any node betweenness centrality > 10× average

**Spec:**
- Spec appears written after-the-fact (reads like changelog)
- Templated boilerplate with placeholders ("[TODO]", etc.)
- Fewer than 2 codebase_modules mentioned in entire spec
- Weakest dimension choice has confidence < 0.45 (all dimensions equally weak)

---

## Using This Rubric

1. **For judges:** These are your scoring anchors. Use them to understand what the numbers mean.
2. **For developers:** Implement Jev questions following these criteria (see design/*.md for details).
3. **For configuration:** Thresholds and ranges are in config.yaml; adjust if your hackathon has different standards.
