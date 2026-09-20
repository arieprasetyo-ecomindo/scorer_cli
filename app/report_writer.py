"""Assemble the final markdown report: chart image + score tables + LLM narrative."""

from datetime import datetime, timezone
from pathlib import Path

from app.chart_generator import generate_score_chart
from app.jev_scorer import (
    SPEC_WEIGHTS,
    STRUCTURE_WEIGHTS,
    weighted_spec_total,
    weighted_structure_total,
)


def _structure_table_md(jev_scores: dict) -> str:
    lines = ["| Dimension | Weight | Score | Jev Level | Confidence |", "|---|---|---|---|---|"]
    for dim, weight in STRUCTURE_WEIGHTS.items():
        a = jev_scores[dim]
        lines.append(
            f"| {dim.replace('_', ' ').title()} | {weight:.0%} | {a['score_0_10']:.1f} / 10 "
            f"| {a['level']} ({a['level_label']}) | {a['confidence']:.0%} |"
        )
    return "\n".join(lines)


def _spec_table_md(spec_scores: dict) -> str:
    lines = ["| Dimension | Weight | Score | Jev Answer | Confidence |", "|---|---|---|---|---|"]
    for dim, weight in SPEC_WEIGHTS.items():
        a = spec_scores[dim]
        lines.append(
            f"| {dim.replace('_', ' ').title()} | {weight:.0%} | {a['score_0_10']:.1f} / 10 "
            f"| {a['answer']} | {a['confidence']:.0%} |"
        )
    return "\n".join(lines)


def write_markdown_report(
    team_name: str,
    output_dir: str | Path,
    jev_scores: dict | None,
    spec_scores: dict | None,
    narrative_md: str,
    red_flags: list[str],
    weights: dict,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sections = [f"# Hackathon Submission Report: {team_name}", ""]
    sections.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    sections.append("")

    structure_total = spec_total = None
    if jev_scores or spec_scores:
        chart_filename = f"{team_name}_chart.png"
        generate_score_chart(team_name, jev_scores, spec_scores, output_dir / chart_filename)
        sections += [f"![Score Breakdown]({chart_filename})", ""]

    if jev_scores:
        structure_total = weighted_structure_total(jev_scores)
        sections += [
            "## Structure Quality (Code Metrics)",
            "",
            _structure_table_md(jev_scores),
            "",
            f"**Structure Weighted Total: {structure_total:.1f} / 10**",
            "",
        ]

    if spec_scores:
        spec_total = weighted_spec_total(spec_scores)
        weakest = spec_scores["weakest_dimension"]
        sections += [
            "## Spec Quality (SDD Scoring)",
            "",
            f"**Weakest Dimension (diagnostic):** {weakest['choice']} ({weakest['confidence']:.0%} confidence)",
            "",
            _spec_table_md(spec_scores),
            "",
            f"**Spec Weighted Total: {spec_total:.1f} / 10**",
            "",
        ]

    if structure_total is not None and spec_total is not None:
        combined = structure_total * weights["structure"] + spec_total * weights["spec"]
        sections += [
            f"## Combined Score: {combined:.1f} / 10",
            f"_(structure {weights['structure']:.0%} + spec {weights['spec']:.0%})_",
            "",
        ]

    sections += [narrative_md, ""]

    sections += ["## Red Flags", ""]
    sections += [f"- {f}" for f in red_flags] if red_flags else ["None detected."]
    sections += ["", "---", "", "_This report is an assistive tool for human judges, not a final verdict._"]

    report_path = output_dir / f"{team_name}.md"
    report_path.write_text("\n".join(sections))
    return report_path
