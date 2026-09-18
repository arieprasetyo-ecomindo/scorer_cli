# Jev Questions: Spec-Driven Development (SDD) Scoring

These five dimensions are scored using **one Choice primitive** (identify the weakest dimension) and **five Noul primitives** (threshold checks). All run **in parallel**.

## Input State

```json
{
  "submission_id": "string",
  "spec_text": "full concatenated spec text with filename headers",
  "codebase_modules": [
    "server.js",
    "libs/mailer.js",
    "models/user.js",
    ...
  ]
}
```

---

## Choice: Weakest Dimension

**Question ID:** `weakest_sdd_dimension`

**Instructions:**
Identify which SDD quality dimension is weakest or most concerning in this spec. This helps judges prioritize what to read manually first.

If all dimensions are equally strong, return the most likely candidate with lower confidence. If spec is uniformly weak, any answer is acceptable.

**Options:**
1. **Clarity & Testability** — requirements are vague or unfalsifiable
2. **Scope Boundary** — in/out of scope is unclear
3. **Internal Consistency** — spec contradicts itself
4. **Traceability** — spec doesn't match codebase structure
5. **Substance Over Polish** — high production value masking low content

**Example:** If the spec reads as a well-formatted marketing document but lacks concrete requirements, choose "Substance Over Polish" with high confidence.

---

## Noul 1: Requirement Clarity & Testability

**Question ID:** `clarity_testability_met`

**Instructions:**
Judge whether requirements are stated concretely enough that someone could verify whether they were met.

**Threshold criteria:**
- **Yes (threshold met):** Requirements are specific and testable (e.g., "the API returns a 400 on missing email field"), not vague ("handle errors well"). Rough target: > 80% of stated requirements are testable/falsifiable.
- **No (threshold not met):** Roughly half or more of requirements are vague, aspirational, or unfalsifiable.

**Guidance:**
- Look for concrete language: "returns 200", "displays within 2 seconds", "rejects invalid email".
- Red flags: "handles", "manages", "supports", "user-friendly", without specific criteria.
- Quote concrete examples from the spec in your reasoning.

---

## Noul 2: Scope Boundary Clarity

**Question ID:** `scope_boundary_met`

**Instructions:**
Judge whether the spec clearly states what is in scope and what is explicitly out.

**Threshold criteria:**
- **Yes (threshold met):** Clear in-scope/out-of-scope statement, or scope is unambiguous from the document structure (e.g., "MVP goals: X, Y, Z. Not in scope: A, B, C.").
- **No (threshold not met):** Scope is unclear in places; reader would have to guess what was intended for MVP vs. later phases.

**Guidance:**
- Explicit is better: "In scope: auth, user profiles. Out of scope: admin dashboard."
- Inferrable but unstated is partial credit (mild yes, not strong yes).
- Complete ambiguity (could be either MVP or future) counts as no.

---

## Noul 3: Internal Consistency

**Question ID:** `consistency_met`

**Instructions:**
Judge whether requirements, data models, and described behavior agree with each other within the document.

**Threshold criteria:**
- **Yes (threshold met):** No significant contradictions found. Minor inconsistencies (e.g., a field named differently in two places, but the meaning is clear) are acceptable.
- **No (threshold not met):** Multiple inconsistencies or a contradiction in core behavior (e.g., "users can delete their own posts" in one section, "only admins can delete posts" in another).

**Guidance:**
- Look for: same entity described differently, same feature described with conflicting requirements, data models that contradict described behavior.
- Quote specific contradictions.
- Minor typos / formatting inconsistencies do not count.

---

## Noul 4: Traceability to Implementation

**Question ID:** `traceability_met`

**Instructions:**
Judge whether the spec's described structure (modules, components, data entities it names) plausibly maps onto the actual files in the codebase.

**Threshold criteria:**
- **Yes (threshold met):** Most named components/modules in the spec have a clearly corresponding file in `codebase_modules`. Little in the codebase looks unaccounted for by the spec. Target: > 70% of codebase files are mentioned or clearly account for in the spec.
- **No (threshold not met):** Weak overlap — spec describes a system that only loosely resembles the actual file list. Many files are orphaned or unexplained.

**Guidance:**
- Build a match matrix: for each major file in `codebase_modules`, find whether it is mentioned in `spec_text` or its purpose is clearly described elsewhere in the spec.
- If `codebase_modules` is large (>20 files), sampling is acceptable—check the top 10 files for mention.
- Example match: spec mentions "mail service" and codebase has `libs/mailer.js` → good.
- Example mismatch: codebase has `models/payment.js`, `models/invoice.js`, `jobs/billing.js` but spec makes no mention of billing/payment → bad.
- Note: this is a **plausibility check on naming/structure**, not proof of correctness — you cannot verify behavior, only whether the described shape is consistent with what was built.

---

## Noul 5: Substance Over Polish

**Question ID:** `substance_met`

**Instructions:**
Judge whether the spec is substantive (concrete detail), not just well-formatted and verbose padding.

**Threshold criteria:**
- **Yes (threshold met):** Content is substantive regardless of formatting — even a plain, unpolished spec with concrete detail scores well. Rough target: > 60% of word count is substantive (not filler, not repetitive, not generic boilerplate).
- **No (threshold not met):** Noticeably more polish/length than actual content — padded or templated-feeling sections, high production value (headers, graphics, buzzwords) masking very little concrete information.

**Guidance:**
- Distinguish "well-written" from "well-specified."
- Filler: "we will provide a great user experience", "the system will be robust", repeated sections without new information.
- Substance: specific requirements, data models, API contracts, decision rationale.
- A short, plain spec with concrete detail is **better** than a long, glossy spec with vague content.
- Word count alone is not substance — look at information density.

---

## Red Flags (Separate from Noul Thresholds)

In addition to the five Noul thresholds, flag any of the following if present:

1. **Spec appears written after-the-fact** (e.g., reads as a changelog/summary rather than a forward-looking plan). Note this as a *possibility*, not a certainty — you cannot verify authorship order.
   - Signs: "implemented the login flow", "added error handling", past tense throughout.

2. **Templated boilerplate with placeholders** (e.g., "[TODO]", "[description here]", "TBD") still present in the spec.

3. **Fewer than 2 of the `codebase_modules` are mentioned** anywhere in `spec_text`.

---

## Code Integration Example

```python
from typesafe import jev_client

# Prepare state from spec extraction
state = {
    "submission_id": submission_id,
    "spec_text": spec_text,
    "codebase_modules": codebase_modules
}

# Build Choice + five Noulis
questions = [
    {
        "id": "weakest_sdd_dimension",
        "type": "choice",
        "instructions": "Identify which SDD quality dimension is weakest...",
        "state": state,
        "options": [
            "Clarity & Testability",
            "Scope Boundary",
            "Internal Consistency",
            "Traceability",
            "Substance Over Polish"
        ]
    },
    {
        "id": "clarity_testability_met",
        "type": "noul",
        "instructions": "Judge whether requirements are concrete and testable...",
        "state": state,
        "criteria": {
            "yes": "Requirements are specific and testable (>80% of stated requirements)",
            "no": "Roughly half or more are vague, aspirational, or unfalsifiable"
        }
    },
    # ... (Noul 2–5)
]

# Call Jev once (all questions run in parallel)
response = jev_client.ask(
    model="jev",
    questions=questions
)

# Extract answers
weakest = response["weakest_sdd_dimension"]
print(f"Weakest dimension: {weakest.answer} ({weakest.confidence:.2%})")

for dim in ["clarity_testability", "scope_boundary", "consistency", "traceability", "substance"]:
    answer = response[f"{dim}_met"]  # "yes" or "no"
    confidence = answer.confidence  # 0–1
    score = 8 if answer.answer == "yes" else 3
    print(f"{dim}: {answer.answer} ({confidence:.2%}) → {score}")
```

---

## Mapping Noul Answers to Scores

| Answer | Base Score | Confidence Adjustment |
|--------|-----------|----------------------|
| Yes | 8.0 | confidence ≥ 0.7 → 8–9, confidence < 0.5 → 6–7 |
| No | 3.0 | confidence ≥ 0.7 → 2–3, confidence < 0.5 → 4–5 |

**Example:**
- Noul says "yes" (clarity met) with 0.8 confidence → score 8.5
- Noul says "no" (clarity not met) with 0.6 confidence → score 3.5

Fine-tuning thresholds in `config.yaml` allows judges to adjust the mapping per dimension if needed.

---

## Notes

- All six questions (Choice + five Noulis) run in **parallel** in a single API call.
- The Choice primitive helps judges prioritize manual review.
- Noul thresholds are deliberately set to catch spec quality issues, not to be overly strict.
- Confidence on each Noul can guide review priority: low confidence may indicate genuinely ambiguous specs worth manual inspection.
- Red flags are checked separately (not via Jev) based on metrics and spec text matching.
