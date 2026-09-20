"""Render a bar chart of Jev structure + spec scores for the markdown report.

Also runnable standalone for a quick visual check of the chart style:
    uv run python -m app.chart_generator
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: no display needed to write a PNG
import matplotlib.pyplot as plt

from app.jev_scorer import SPEC_WEIGHTS, STRUCTURE_WEIGHTS

LOW_COLOR = "#d64545"  # < 4: needs work
MID_COLOR = "#e0a72e"  # 4-7: fair
HIGH_COLOR = "#3fa34d"  # >= 7: solid


def _score_color(score: float) -> str:
    if score < 4:
        return LOW_COLOR
    if score < 7:
        return MID_COLOR
    return HIGH_COLOR


def _plot_dimensions(ax, dims: dict[str, float], title: str) -> None:
    labels = [d.replace("_", " ").title() for d in dims]
    values = list(dims.values())
    colors = [_score_color(v) for v in values]

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=colors, height=0.6)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 10)
    ax.set_xlabel("Score (0-10)")
    ax.set_title(title, fontsize=12, fontweight="bold", loc="left")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    ax.spines[["top", "right"]].set_visible(False)

    for i, v in enumerate(values):
        ax.text(v + 0.15, i, f"{v:.1f}", va="center", fontsize=9)


def generate_score_chart(
    team_name: str,
    jev_scores: dict | None,
    spec_scores: dict | None,
    output_path: str | Path,
) -> Path:
    """Render all scored dimensions as horizontal bar charts and save as a PNG."""
    output_path = Path(output_path)

    sections = []
    if jev_scores:
        sections.append(
            ("Structure Quality", {d: jev_scores[d]["score_0_10"] for d in STRUCTURE_WEIGHTS})
        )
    if spec_scores:
        sections.append(
            ("Spec Quality", {d: spec_scores[d]["score_0_10"] for d in SPEC_WEIGHTS})
        )
    if not sections:
        raise ValueError("No scores to chart")

    total_bars = sum(len(dims) for _, dims in sections)
    fig, axes = plt.subplots(len(sections), 1, figsize=(7, 1.2 + 0.55 * total_bars))
    axes = [axes] if len(sections) == 1 else axes

    for ax, (title, dims) in zip(axes, sections):
        _plot_dimensions(ax, dims, title)

    fig.suptitle(f"scorer_cli — Score Breakdown: {team_name}", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    demo_jev_scores = {
        "coupling": {"score_0_10": 7.7},
        "circular_dependencies": {"score_0_10": 10.0},
        "dependency_depth": {"score_0_10": 9.8},
        "cyclomatic_complexity": {"score_0_10": 6.5},
        "function_size_discipline": {"score_0_10": 10.0},
        "betweenness_centrality": {"score_0_10": 9.5},
    }
    demo_spec_scores = {
        "clarity_testability": {"score_0_10": 8.4},
        "scope_boundary": {"score_0_10": 8.9},
        "internal_consistency": {"score_0_10": 8.3},
        "traceability": {"score_0_10": 2.4},
        "substance_over_polish": {"score_0_10": 8.8},
    }
    path = generate_score_chart("demo_team", demo_jev_scores, demo_spec_scores, "demo_chart.png")
    print(f"Wrote {path}")
