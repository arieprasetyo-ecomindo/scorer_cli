# Spec Scoring: 1 Choice + 5 Noul Primitives

This document defines the **1 Choice** and **5 Noul** primitives used to judge Spec-Driven Development quality.

## Overview

- **Choice:** Identify the weakest SDD dimension (diagnostic, helps judges prioritize)
- **Noul (×5):** Judge whether each dimension meets a threshold (yes/no with confidence)

Noul answers map to scores: yes → 8, no → 3, adjusted by confidence.

## Input State

All questions receive the same state:

```json
{
  "submission_id": "string",
  "spec_text": "full concatenated spec documents with filename headers",
  "codebase_modules": [
    "server.js",
    "libs/mailer.js",
    "models/user.js",
    ...
  ]
}
```

---

## Question 1: Weakest Dimension (Choice)

**ID:** `weakest_sdd_dimension`

**Type:** Choice (one answer from options)

**Options:**
1. Clarity & Testability
2. Scope Boundary
3. Internal Consistency
4. Traceability
5. Substance Over Polish

**Instructions:** Identify which SDD dimension is weakest or most concerning in the spec.

**Output:** Single option + confidence (0–1)

**Use case:** Judges see which dimension to review first. Not a score itself.

---

## Question 2: Clarity & Testability (Noul)

**ID:** `clarity_testability_met`

**Type:** Noul (yes/no)

**Yes Criteria:** Requirements are concrete, specific, testable (e.g., "API returns 400 on missing email"). >80% of requirements are testable/falsifiable, not vague aspirations.

**No Criteria:** ~Half or more of requirements are vague ("handle errors well", "user-friendly"), aspirational, or unfalsifiable.

**Examples:**
- **Yes:** "checkout must complete in <2 seconds", "password must be ≥8 chars"
- **No:** "provide great experience", "system should be robust", "handle edge cases"

**Output:** yes/no + confidence (0–1)

**Score mapping:**
- yes (confidence ≥ 0.7) → score ~8.5
- yes (confidence < 0.5) → score ~6.5
- no (confidence ≥ 0.7) → score ~2.5
- no (confidence < 0.5) → score ~4.5

---

## Question 3: Scope Boundary (Noul)

**ID:** `scope_boundary_met`

**Type:** Noul (yes/no)

**Yes Criteria:** Clear in-scope/out-of-scope statement. Either explicit ("MVP: A, B, C. Not in scope: X, Y") or unambiguous from document structure.

**No Criteria:** Scope unclear; reader must guess what's MVP vs. future. Ambiguous boundaries.

**Examples:**
- **Yes:** "MVP Goals: auth, profiles, checkout. Future: admin panel, analytics (out of scope)"
- **No:** "We'll build auth and maybe analytics later" (unclear if analytics is MVP)

**Output:** yes/no + confidence (0–1)

---

## Question 4: Internal Consistency (Noul)

**ID:** `consistency_met`

**Type:** Noul (yes/no)

**Yes Criteria:** No significant contradictions. Same entity described consistently throughout. Requirements and data models align.

**No Criteria:** Multiple inconsistencies or core contradictions. (e.g., "only admins can delete posts" vs. "users can delete their own posts")

**Examples:**
- **Yes:** Data model defined once, referenced consistently. Requirements coherent.
- **No:** "Field named 'email' in one section, 'email_address' in another with different type" + "users can delete posts" vs. "only admins delete"

**Output:** yes/no + confidence (0–1)

---

## Question 5: Traceability (Noul)

**ID:** `traceability_met`

**Type:** Noul (yes/no)

**Yes Criteria:** Most spec-named components have clear mapping to `codebase_modules`. >70% of codebase files are mentioned or clearly accounted for in spec.

**No Criteria:** Weak overlap. Spec describes different system; many files orphaned/unexplained.

**Examples:**
- **Yes:** Spec mentions "mail service" → codebase has `libs/mailer.js`. Spec describes "user profiles" → codebase has `models/user.js`. Most files matched.
- **No:** Codebase has `models/payment.js`, `jobs/billing.js` but spec never mentions billing/payment. `utils/helpers.js` has no clear role in spec.

**Output:** yes/no + confidence (0–1)

**Note:** This is a plausibility check, not proof of correctness. We can't verify behavior, only naming/structure alignment.

---

## Question 6: Substance Over Polish (Noul)

**ID:** `substance_met`

**Type:** Noul (yes/no)

**Yes Criteria:** Content is substantive (concrete detail) regardless of formatting. Even plain, unpolished spec with good detail scores well. >60% of word count is substantive (not filler).

**No Criteria:** Noticeably more polish than content. Well-formatted but vague; buzzwords without specifics; padded or templated sections.

**Examples:**
- **Yes:** "Plain-text spec with API contracts, data models, specific requirements"
- **No:** "Glossy 20-page deck with pretty headers but 'we will build a great product' repeated 5 times"

**Output:** yes/no + confidence (0–1)

---

## Weights

Applied after all 5 Noul questions return:

```yaml
weights:
  clarity_testability: 0.25
  scope_boundary: 0.15
  internal_consistency: 0.15
  traceability: 0.25
  substance_over_polish: 0.20
```

**Weighted Total Formula:**
```
spec_score = Σ(noul_to_score[answer_i] × weight_i)
where noul_to_score[yes] ≈ 8, noul_to_score[no] ≈ 3 (adjusted by confidence)
```

---

## Red Flags (Separate from Noul)

Checked independently after Noul scoring:

- **Spec appears written after-the-fact** (reads like changelog, past tense throughout)
- **Templated boilerplate with placeholders** ("[TODO]", "[description here]" still in spec)
- **Fewer than 2 `codebase_modules` mentioned** anywhere in spec_text
- **Weakest dimension Choice confidence < 0.45** (dimensions equally weak; ambiguous signal)

---

## Implementation Example

```python
from typesafe import jev_client

questions = [
    {
        "id": "weakest_sdd_dimension",
        "type": "choice",
        "instructions": "Identify which SDD dimension is weakest...",
        "state": spec_state,
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
        "instructions": "Are requirements concrete and testable?",
        "state": spec_state,
        "criteria": {
            "yes": "Requirements are specific and testable (>80%)",
            "no": "Roughly half or more are vague, aspirational, unfalsifiable"
        }
    },
    # ... (Noul 2–5, similar structure)
]

response = jev_client.ask(model="jev", questions=questions)

# Extract Choice
weakest = response["weakest_sdd_dimension"]
print(f"Weakest: {weakest.answer} ({weakest.confidence:.0%})")

# Extract Noulis
for dim in ["clarity_testability", "scope_boundary", "consistency", "traceability", "substance"]:
    answer = response[f"{dim}_met"]
    score = 8 if answer.answer == "yes" else 3
    adjusted_score = score + (answer.confidence - 0.5) * 2  # ±2 based on confidence
    print(f"{dim}: {answer.answer} ({answer.confidence:.0%}) → {adjusted_score:.1f}")
```

---

## Debugging Low Confidence

If Jev returns low confidence on a Noul dimension:

- **Clarity:** Spec mixes concrete + vague; mixed signals
- **Scope:** MVP vs. future work unclear in places
- **Consistency:** One or two minor contradictions; mostly coherent
- **Traceability:** Partial mapping; some files explained, others not
- **Substance:** Balanced mix of detail and filler

**Action:** Flag low-confidence dimensions for judge manual review.

---

## Score Mapping: Noul → 0–10

Default mapping (adjustable in `config.yaml`):

```yaml
spec_rubric:
  clarity_testability:
    threshold: 0.65
    yes_score_range: [7.5, 9.0]   # if answer="yes"
    no_score_range: [1.0, 4.0]    # if answer="no"
  # ... (all 5 dimensions)
```

Algorithm:
1. If answer = "yes": base_score = yes_score_range[0]
2. Interpolate: score = base + (max - min) × confidence
3. Example: yes, confidence 0.8 → 7.5 + (9.0 - 7.5) × 0.8 = 8.7
4. Example: no, confidence 0.6 → 1.0 + (4.0 - 1.0) × 0.6 = 2.8
