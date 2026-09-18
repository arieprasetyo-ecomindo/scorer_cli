# Implementation Guide: Jev-Based Scorer-CLI

This guide walks through the code changes needed to replace LLM calls with Jev.

## Overview

**Current structure (LLM approach):**
```
score_cli/
  __main__.py           # CLI entry point
  scorer.py             # Main scoring orchestration
  metrics.py            # Compute graph + complexity metrics
  llm_scorer.py         # LLM calls (scoring + prose)
  report_generator.py   # Format output markdown
```

**New structure (Jev + LLM approach):**
```
score_cli/
  __main__.py           # CLI entry point (unchanged)
  scorer.py             # Orchestration (refactored to call Jev + LLM)
  metrics.py            # Compute graph + complexity (unchanged)
  jev_scorer.py         # NEW: Jev questions & API calls (judgment only)
  scoring_engine.py     # NEW: Map Jev answers to 0–10 scores + arithmetic
  report_generator.py   # NEW: Format + LLM-generated prose
  llm_reporter.py       # NEW: LLM calls for report generation (prose only)
```

**Key difference:** Jev handles *judgment* (structured), LLM handles *explanation* (prose).

## Step 1: Setup TypeSafe SDK

### Update `pyproject.toml`

```diff
[project]
name = "score-cli"
version = "0.2.0"
dependencies = [
    "networkx>=3.0",
    "lizard>=1.17",
    "pyyaml>=6.0",
    "requests>=2.28",
-   "anthropic>=0.10",
+   "typesafe>=0.1.0",  # TypeSafe SDK for Jev
]
```

### Environment Setup

```bash
# Install dependencies
uv sync

# Set TypeSafe API key
export TYPESAFE_API_KEY="sk-..."
# OR add to .env
echo "TYPESAFE_API_KEY=sk-..." > .env
```

## Step 2: Create Jev Scoring Module

### New File: `score_cli/jev_scorer.py`

```python
"""
Jev-based scoring for structure and spec quality.
Replaces LLM-based free-form scoring with structured, typed judgments.
"""

import json
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from typesafe import Client

logger = logging.getLogger(__name__)


@dataclass
class ScoreAnswer:
    """A Jev Score answer: level (1–5) + confidence."""
    level: int  # 1 (Critical) to 5 (Excellent)
    confidence: float  # 0–1


@dataclass
class NoulAnswer:
    """A Jev Noul answer: yes/no + confidence."""
    answer: str  # "yes" or "no"
    confidence: float  # 0–1


class JevScorer:
    """Interface to TypeSafe Jev for scoring."""

    def __init__(self, api_key: str, api_endpoint: str, model: str = "jev"):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        self.client = Client(api_key=api_key)

    def score_structure(self, metrics: dict) -> dict[str, ScoreAnswer]:
        """
        Score code structure across 6 dimensions.
        
        Args:
            metrics: Merged metrics.json (graph + complexity)
        
        Returns:
            Dict of dimension_id -> ScoreAnswer
        """
        questions = self._build_structure_questions(metrics)
        
        response = self.client.ask(
            model=self.model,
            questions=questions,
            api_endpoint=self.api_endpoint
        )
        
        # Parse responses into ScoreAnswers
        scores = {}
        for q_id, answer_data in response.items():
            # Jev returns a distribution over levels; extract top level
            level = answer_data.get("level")  # 1–5
            confidence = answer_data.get("confidence")  # 0–1
            scores[q_id] = ScoreAnswer(level=level, confidence=confidence)
        
        return scores

    def score_spec(self, spec_text: str, codebase_modules: list[str]) -> dict:
        """
        Score SDD quality: 1 Choice (weakest dimension) + 5 Noul (thresholds).
        
        Args:
            spec_text: Full concatenated spec
            codebase_modules: List of actual file names in codebase
        
        Returns:
            Dict with:
              - "weakest_dimension": {"answer": str, "confidence": float}
              - "{dimension}_met": {"answer": "yes"/"no", "confidence": float} ×5
        """
        questions = self._build_spec_questions(spec_text, codebase_modules)
        
        response = self.client.ask(
            model=self.model,
            questions=questions,
            api_endpoint=self.api_endpoint
        )
        
        # Parse into flat dict
        spec_scores = {}
        for q_id, answer_data in response.items():
            spec_scores[q_id] = {
                "answer": answer_data.get("answer"),
                "confidence": answer_data.get("confidence")
            }
        
        return spec_scores

    def _build_structure_questions(self, metrics: dict) -> list[dict]:
        """Build the 6 Score primitives for structure scoring."""
        return [
            {
                "id": "coupling",
                "type": "score",
                "instructions": self._get_structure_instruction("coupling"),
                "state": {
                    "avg_fan_in": metrics["graph_metrics"]["avg_fan_in"],
                    "max_fan_in": metrics["graph_metrics"]["max_fan_in"],
                    "avg_fan_out": metrics["graph_metrics"]["avg_fan_out"],
                    "max_fan_out": metrics["graph_metrics"]["max_fan_out"],
                },
                "criteria": [
                    {"level": 1, "description": "Pervasive high coupling (max fan-in/out > 10× avg)"},
                    {"level": 2, "description": "Several god-modules; high fan-in/out hotspots"},
                    {"level": 3, "description": "One or two hotspot nodes; moderate interdependencies"},
                    {"level": 4, "description": "Isolated hotspots; mostly even coupling"},
                    {"level": 5, "description": "Low, even coupling; no architectural hotspots"},
                ]
            },
            # ... (questions 2–6: circular_dependencies, dependency_depth, etc.)
        ]

    def _build_spec_questions(self, spec_text: str, codebase_modules: list[str]) -> list[dict]:
        """Build the Choice + 5 Noul primitives for spec scoring."""
        return [
            {
                "id": "weakest_sdd_dimension",
                "type": "choice",
                "instructions": self._get_spec_instruction("weakest_dimension"),
                "state": {
                    "spec_text": spec_text,
                    "codebase_modules": codebase_modules,
                },
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
                "instructions": self._get_spec_instruction("clarity_testability"),
                "state": {
                    "spec_text": spec_text,
                },
                "criteria": {
                    "yes": "Requirements are specific and testable (>80% of stated requirements)",
                    "no": "Roughly half or more are vague, aspirational, or unfalsifiable"
                }
            },
            # ... (Noul 2–5: scope_boundary, consistency, traceability, substance)
        ]

    def _get_structure_instruction(self, dimension: str) -> str:
        """Return the instruction text for a structure dimension."""
        instructions = {
            "coupling": "Rate the severity of coupling (interdependencies) in this codebase...",
            # ... (more)
        }
        return instructions.get(dimension, "")

    def _get_spec_instruction(self, dimension: str) -> str:
        """Return the instruction text for a spec dimension."""
        instructions = {
            "weakest_dimension": "Identify which SDD dimension is weakest...",
            # ... (more)
        }
        return instructions.get(dimension, "")
```

## Step 3: Create Scoring Engine

### New File: `score_cli/scoring_engine.py`

```python
"""
Map Jev answers to 0–10 scores and compute weighted totals.
Separates semantic judgment (Jev) from policy (weighting in config).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ScoringEngine:
    """Convert Jev answers to 0–10 scores and compute totals."""

    def __init__(self, config: dict):
        self.config = config
        self.structure_weights = config["weights"]["structure_dimensions"]
        self.spec_weights = config["weights"]["spec_dimensions"]
        self.structure_rubric = config["structure_rubric"]
        self.spec_rubric = config["spec_rubric"]

    def score_structure(self, jev_answers: dict[str, dict]) -> dict:
        """
        Convert 6 Score answers (levels 1–5) to 0–10 scores.
        Compute weighted total.
        
        Args:
            jev_answers: Dict of dimension -> {"level": int, "confidence": float}
        
        Returns:
            Dict with scores, weighted_total, and justifications
        """
        scores = {}
        
        # Map each level (1–5) to 0–10
        for dim_id, answer in jev_answers.items():
            level = answer["level"]
            confidence = answer["confidence"]
            
            # Level 1 → 0, Level 5 → 10
            score_0_10 = (level - 1) * 2.5
            
            # Get rubric description for this level
            description = self.structure_rubric[dim_id].get(f"level_{level}", "")
            
            scores[dim_id] = {
                "score": score_0_10,
                "level": level,
                "confidence": confidence,
                "description": description
            }
        
        # Compute weighted total
        weighted_total = 0.0
        for dim_id, score_data in scores.items():
            weight = self.structure_weights.get(dim_id, 0)
            weighted_total += score_data["score"] * weight
        
        return {
            "scores": scores,
            "weighted_total": weighted_total
        }

    def score_spec(self, jev_answers: dict[str, dict]) -> dict:
        """
        Convert Choice + 5 Noul answers to 0–10 scores.
        Compute weighted total.
        
        Args:
            jev_answers: Dict with:
              - "weakest_dimension": {"answer": str, "confidence": float}
              - "{dim}_met": {"answer": "yes"/"no", "confidence": float} ×5
        
        Returns:
            Dict with scores, weighted_total, and weakest_dimension
        """
        scores = {}
        
        for dim_id, answer in jev_answers.items():
            if dim_id == "weakest_sdd_dimension":
                continue  # Diagnostic, not a score
            
            # Noul answer: "yes" or "no"
            is_yes = answer["answer"].lower() == "yes"
            confidence = answer["confidence"]
            
            # Map yes/no to base score, adjust by confidence
            threshold = self.spec_rubric[dim_id]["threshold"]
            yes_range = self.spec_rubric[dim_id]["yes_score_range"]
            no_range = self.spec_rubric[dim_id]["no_score_range"]
            
            if is_yes:
                base_score = yes_range[0]
                score_0_10 = base_score + (yes_range[1] - yes_range[0]) * confidence
            else:
                base_score = no_range[0]
                score_0_10 = base_score + (no_range[1] - no_range[0]) * confidence
            
            scores[dim_id.replace("_met", "")] = {
                "score": score_0_10,
                "answer": answer["answer"],
                "confidence": confidence
            }
        
        # Compute weighted total
        weighted_total = 0.0
        for dim_id, score_data in scores.items():
            weight = self.spec_weights.get(dim_id, 0)
            weighted_total += score_data["score"] * weight
        
        weakest = jev_answers.get("weakest_sdd_dimension", {})
        
        return {
            "scores": scores,
            "weighted_total": weighted_total,
            "weakest_dimension": weakest
        }

    def combined_score(self, structure_total: float, spec_total: float) -> float:
        """Compute final combined score."""
        struct_weight = self.config["weights"]["structure"]
        spec_weight = self.config["weights"]["spec"]
        return (structure_total * struct_weight) + (spec_total * spec_weight)
```

## Step 4: Create LLM Reporter Module

### New File: `score_cli/llm_reporter.py`

```python
"""
Generate markdown reports from structured Jev scores using Claude.
"""

import json
import logging
from typing import Optional

from anthropic import Anthropic

logger = logging.getLogger(__name__)


class LLMReporter:
    """Use Claude to generate readable markdown from scored data."""

    def __init__(self, api_key: str, model: str = "claude-opus-5", temperature: float = 0.3):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def generate_report_markdown(
        self,
        submission_id: str,
        scored_data: dict,
        config: dict,
        metrics: dict
    ) -> str:
        """
        Generate markdown report from Jev scores + metrics.
        
        Args:
            submission_id: Team ID
            scored_data: {
                "structure": {"scores": {...}, "weighted_total": 7.8},
                "spec": {"scores": {...}, "weighted_total": 7.6},
                "combined_score": 7.7,
                "red_flags": [...]
            }
            config: Full config (rubric descriptions, etc.)
            metrics: Original metrics (node_count, CCN stats, etc.)
        
        Returns:
            Markdown string
        """
        
        # Build concise JSON for Claude (don't send huge metrics)
        prompt_data = {
            "submission_id": submission_id,
            "structure_scores": {
                dim_id: {
                    "score": score_data["score"],
                    "level": score_data["level"],
                    "confidence": score_data["confidence"]
                }
                for dim_id, score_data in scored_data["structure"]["scores"].items()
            },
            "structure_total": scored_data["structure"]["weighted_total"],
            "spec_scores": {
                dim_id: {
                    "score": score_data["score"],
                    "answer": score_data["answer"],
                    "confidence": score_data["confidence"]
                }
                for dim_id, score_data in scored_data["spec"]["scores"].items()
            },
            "spec_total": scored_data["spec"]["weighted_total"],
            "combined_score": scored_data["combined_score"],
            "red_flags": scored_data.get("red_flags", []),
            "metrics_snapshot": {
                "nodes": metrics.get("graph_metrics", {}).get("node_count"),
                "avg_fan_in": metrics.get("graph_metrics", {}).get("avg_fan_in"),
                "max_fan_in": metrics.get("graph_metrics", {}).get("max_fan_in"),
                "avg_ccn": metrics.get("complexity_metrics", {}).get("avg_cyclomatic_complexity"),
                "max_ccn": metrics.get("complexity_metrics", {}).get("max_cyclomatic_complexity"),
                "circular_deps": len(metrics.get("graph_metrics", {}).get("circular_dependencies", [])),
            }
        }
        
        # Build the prompt
        prompt = self._build_prompt(prompt_data, config)
        
        # Call Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"LLM report generation failed for {submission_id}: {e}")
            # Fallback: auto-generated markdown without prose
            return self._fallback_markdown(prompt_data)

    def _build_prompt(self, data: dict, config: dict) -> str:
        """Build the Claude prompt for report generation."""
        
        rubric = config.get("structure_rubric", {})
        
        return f"""
You are a hackathon judge report writer. Generate a markdown report with structured scores and human-readable explanations.

SCORING DATA (JSON):
{json.dumps(data, indent=2)}

RUBRIC DESCRIPTIONS (for reference):
Structure dimensions:
{json.dumps({dim: rubric.get(dim, {}) for dim in ["coupling", "circular_dependencies", "dependency_depth", "cyclomatic_complexity", "function_size_discipline", "betweenness_centrality"]}, indent=2)}

TASK:
1. Write 2-3 sentence justifications for each structure dimension (6 total)
   - Reference the Jev confidence level and score
   - Reference specific metrics (coupling ratio, CCN values, etc.)
   - End with actionable feedback for judges
   
2. Write 2-3 sentence justifications for each spec dimension (5 total)
   - State whether threshold was met (yes/no) with confidence
   - Explain what this means for the submission
   
3. Write a 3-4 sentence summary explaining:
   - Overall strengths
   - Key weaknesses
   - Recommendation for judges

FORMAT:
Use markdown with ### headers for each dimension. Include score and confidence in parentheses.
Example:
```
### Coupling — Weight 21%

| | |
|--|--|
| **Score** | 7.5 / 10 |
| **Jev Level** | 4 (Good) |
| **Confidence** | 78% |
| **Justification** | [2-3 sentences with metrics and feedback] |
```

OUTPUT: Markdown only, no preamble. Structure section first, then Spec section, then Summary.
"""

    def _fallback_markdown(self, data: dict) -> str:
        """Fallback auto-generated markdown if LLM fails."""
        md = f"# Report for {data['submission_id']} (Auto-generated)\n\n"
        md += f"**Combined Score:** {data['combined_score']:.1f} / 10\n\n"
        md += f"**Structure Total:** {data['structure_total']:.1f} / 10\n"
        md += f"**Spec Total:** {data['spec_total']:.1f} / 10\n\n"
        
        md += "## Red Flags\n"
        for flag in data.get("red_flags", []):
            md += f"- {flag}\n"
        
        return md
```

## Step 5: Refactor Main Scorer

### Modified: `score_cli/scorer.py`

```python
# In the main scoring function:

def score_submission(submission_id: str, config: dict) -> dict:
    """Score one submission using Jev + LLM."""
    
    # Compute metrics (unchanged)
    metrics = compute_metrics(submission_id)
    
    # Initialize Jev scorer
    from score_cli.jev_scorer import JevScorer
    jev = JevScorer(
        api_key=config["typesafe"]["api_key"],
        api_endpoint=config["typesafe"]["api_endpoint"],
        model=config["typesafe"]["model"]
    )
    
    # Call Jev for structure
    structure_jev_answers = jev.score_structure(metrics)
    
    # Call Jev for spec
    spec_text = extract_spec_text(submission_id)
    codebase_modules = extract_codebase_modules(metrics)
    spec_jev_answers = jev.score_spec(spec_text, codebase_modules)
    
    # Convert Jev answers to 0–10 scores
    from score_cli.scoring_engine import ScoringEngine
    engine = ScoringEngine(config)
    
    structure_result = engine.score_structure(structure_jev_answers)
    spec_result = engine.score_spec(spec_jev_answers)
    
    combined = engine.combined_score(
        structure_result["weighted_total"],
        spec_result["weighted_total"]
    )
    
    # Compute red flags
    red_flags = check_red_flags(metrics, spec_result)
    
    # Compile scored data for LLM report generation
    scored_data = {
        "submission_id": submission_id,
        "structure": structure_result,
        "spec": spec_result,
        "combined_score": combined,
        "red_flags": red_flags
    }
    
    # Generate markdown report using LLM
    from score_cli.llm_reporter import LLMReporter
    reporter = LLMReporter(
        api_key=config["report_generation"]["api_key"],
        model=config["report_generation"]["model"],
        temperature=config["report_generation"]["temperature"]
    )
    
    markdown_report = reporter.generate_report_markdown(
        submission_id=submission_id,
        scored_data=scored_data,
        config=config,
        metrics=metrics
    )
    
    return {
        "submission_id": submission_id,
        "scored_data": scored_data,
        "markdown_report": markdown_report
    }
```

## Step 6: Update Report Generator

### Modified: `score_cli/report_generator.py`

The main report generator now combines scored data with LLM prose:

```python
def write_report(submission_id: str, scored_data: dict, markdown_report: str, output_dir: str) -> str:
    """Write final report to markdown file."""
    
    report_path = f"{output_dir}/reports/{submission_id}.md"
    
    # Combine header with LLM-generated prose
    header = f"""# Hackathon Submission Report: {submission_id}

**Generated:** {datetime.now().isoformat()}Z
**Submission ID:** {submission_id}

"""
    
    with open(report_path, "w") as f:
        f.write(header)
        f.write(markdown_report)
        f.write(f"""

## Scoring Metadata

| Field | Value |
|-------|-------|
| **Jev Model** | jev (TypeSafe System One) |
| **LLM Model** | {config["report_generation"]["model"]} |
| **Combined Score** | {scored_data["combined_score"]:.1f} / 10 |
| **Generated By** | score-cli v0.2.0 (Jev + LLM) |

*This report is an assistive tool for human judges, not a final verdict.*
""")
    
    return report_path
```

## Step 7: Testing

### Test File: `tests/test_jev_scorer.py`

```python
import pytest
from score_cli.jev_scorer import JevScorer, ScoreAnswer
from score_cli.scoring_engine import ScoringEngine


def test_jev_scorer_structure(mock_jev_response):
    """Test structure scoring with mock Jev response."""
    scorer = JevScorer(api_key="test", api_endpoint="http://localhost")
    
    metrics = {
        "graph_metrics": {
            "avg_fan_in": 1.6,
            "max_fan_in": 7,
            "avg_fan_out": 1.6,
            "max_fan_out": 9,
            # ... more
        },
        "complexity_metrics": {
            # ...
        }
    }
    
    # Mock Jev response
    scores = scorer.score_structure(metrics)
    
    assert "coupling" in scores
    assert isinstance(scores["coupling"], ScoreAnswer)
    assert 1 <= scores["coupling"].level <= 5
    assert 0 <= scores["coupling"].confidence <= 1


def test_scoring_engine(config):
    """Test conversion of Jev answers to 0–10 scores."""
    engine = ScoringEngine(config)
    
    jev_answers = {
        "coupling": {"level": 4, "confidence": 0.78},
        "circular_dependencies": {"level": 5, "confidence": 0.95},
        # ... more
    }
    
    result = engine.score_structure(jev_answers)
    
    assert "coupling" in result["scores"]
    assert result["scores"]["coupling"]["score"] == 7.5  # (4-1)*2.5
    assert result["weighted_total"] > 0
```

## Step 8: Configuration

Copy `config.yaml.example` to `config.yaml` and fill in both APIs:

```yaml
typesafe:
  api_key_env: "TYPESAFE_API_KEY"
  api_endpoint: "https://api.typesafe.ai/v1"
  model: "jev"

report_generation:
  api_key_env: "ANTHROPIC_API_KEY"
  model: "claude-opus-5"
  temperature: 0.3
  max_tokens: 2000
```

Then set both API keys:
```bash
export TYPESAFE_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Deployment Checklist

- [ ] All code changes implemented and tested
- [ ] `config.yaml` created with TypeSafe **and** Anthropic credentials
- [ ] `pyproject.toml` updated (add both `typesafe` and `anthropic` SDKs)
- [ ] Both API keys set: `TYPESAFE_API_KEY` and `ANTHROPIC_API_KEY`
- [ ] Sample fixture tested and report generated
  - [ ] Jev calls complete successfully
  - [ ] LLM report generation completes successfully
  - [ ] Fallback markdown generated if LLM fails
- [ ] Batch run on real submissions works
- [ ] Red flags computed correctly
- [ ] Report format matches expected output
- [ ] Both TypeSafe and Anthropic APIs are accessible and responsive
- [ ] Logging configured and errors handled gracefully
- [ ] LLM model choice validated (opus-5 for quality, haiku for cost)

## Troubleshooting

**"Module 'typesafe' not found" or "Module 'anthropic' not found"**
- Run `uv sync` to install dependencies from updated `pyproject.toml`

**"TYPESAFE_API_KEY not set" or "ANTHROPIC_API_KEY not set"**
- Export both keys:
  ```bash
  export TYPESAFE_API_KEY="sk-..."
  export ANTHROPIC_API_KEY="sk-ant-..."
  ```
- Or add to `.env` file

**"Jev returned unexpected output shape"**
- Check that question IDs match expected keys
- Verify state JSON matches question definitions
- Enable debug logging to see full API responses

**"LLM report generation failed, using fallback"**
- Normal if Claude API is rate-limited or times out
- Fallback markdown is generated (scores but no prose)
- Check `ANTHROPIC_API_KEY` is valid
- Try lowering `max_tokens` in config if hitting limits

**"Low confidence on crucial dimensions"**
- Normal if the codebase/spec is genuinely ambiguous
- Flag in red_flags so judges know to review manually
- Consider running multiple Jev calls and averaging (future enhancement)

**"LLM markdown doesn't match expected format"**
- Claude may deviate from the prompt structure
- Parse and validate the returned markdown before writing to file
- Fallback to structured JSON output if validation fails

---

This implementation is a solid foundation. Once working, you can optimize further (averaging calls, caching, async batch processing, etc.).
