"""Render graph/complexity metrics, deterministic structure scores, and Jev spec
scores as a Rich terminal report.
"""

import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.chart_generator import HIGH_COLOR, LOW_COLOR, MID_COLOR
from app.jev_scorer import SPEC_WEIGHTS, weighted_spec_total
from app.structure_scorer import STRUCTURE_WEIGHTS, weighted_structure_total

TEMPLATED_PLACEHOLDER_RE = re.compile(r"\[(TODO|TBD|description here|FIXME)\]", re.IGNORECASE)


def _score_color(score: float) -> str:
    if score < 4:
        return LOW_COLOR
    if score < 7:
        return MID_COLOR
    return HIGH_COLOR


def score_bar(score: float, width: int = 10, max_score: float = 10.0) -> str:
    """A little inline meter bar, e.g. '[green]████████░░░░[/green]', for a 0-10 score."""
    filled = round(width * max(0.0, min(score, max_score)) / max_score)
    bar = "█" * filled + "░" * (width - filled)
    color = _score_color(score)
    return f"[{color}]{bar}[/{color}]"


def compute_graph_red_flags(metrics: dict, red_flags_cfg: dict) -> list[str]:
    flags = []
    cycle_threshold = red_flags_cfg.get("circular_deps_involving_more_than", 3)
    fan_multiple = red_flags_cfg.get("fan_coupling_multiple", 5.0)
    betweenness_multiple = red_flags_cfg.get("betweenness_multiple", 10.0)

    for cycle in metrics["circular_dependencies"]:
        touched = len(cycle) - 1  # cycle list repeats the start node at the end
        if touched > cycle_threshold:
            flags.append(f"Circular dependency touches {touched} modules: {' -> '.join(cycle)}")

    avg_in, avg_out = metrics["avg_fan_in"], metrics["avg_fan_out"]
    if avg_in > 0 and metrics["max_fan_in"] > fan_multiple * avg_in:
        flags.append(
            f"Max fan-in {metrics['max_fan_in']} is > {fan_multiple:g}x the average ({avg_in:.1f})"
        )
    if avg_out > 0 and metrics["max_fan_out"] > fan_multiple * avg_out:
        flags.append(
            f"Max fan-out {metrics['max_fan_out']} is > {fan_multiple:g}x the average ({avg_out:.1f})"
        )

    avg_b = metrics["avg_betweenness_centrality"]
    if avg_b > 0 and metrics["max_betweenness_centrality"] > betweenness_multiple * avg_b:
        top = metrics["top_betweenness_nodes"][0]["node"]
        flags.append(f"Betweenness bottleneck: '{top}' is > {betweenness_multiple:g}x the average betweenness")

    return flags


def compute_complexity_red_flags(metrics: dict, red_flags_cfg: dict) -> list[str]:
    ccn_threshold = red_flags_cfg.get("max_ccn_threshold", 20)
    flags = []
    for func in metrics["functions_above_complexity_threshold"]:
        if func["ccn"] > ccn_threshold:
            flags.append(
                f"Function `{func['name']}` in {func['file']} has CCN {func['ccn']} (> {ccn_threshold})"
            )
    return flags


def compute_spec_red_flags(
    spec_scores: dict, spec_text: str, codebase_modules: list[str], red_flags_cfg: dict
) -> list[str]:
    flags = []

    choice_confidence_low = red_flags_cfg.get("choice_confidence_low", 0.45)
    weakest = spec_scores["weakest_dimension"]
    if weakest["confidence"] < choice_confidence_low:
        flags.append(
            f"Weakest-dimension signal is ambiguous: '{weakest['choice']}' at only "
            f"{weakest['confidence']:.0%} confidence (all dimensions may be equally weak)"
        )

    min_modules = red_flags_cfg.get("min_modules_mentioned", 2)
    spec_lower = spec_text.lower()
    mentioned = sum(1 for m in codebase_modules if m.rsplit("/", 1)[-1].lower() in spec_lower)
    if mentioned < min_modules:
        flags.append(
            f"Only {mentioned} codebase file(s) appear to be mentioned in the spec (< {min_modules})"
        )

    if red_flags_cfg.get("templated_boilerplate") and TEMPLATED_PLACEHOLDER_RE.search(spec_text):
        flags.append("Spec still contains template placeholders (e.g. [TODO], [TBD])")

    return flags


def compute_all_red_flags(
    graph_metrics: dict,
    complexity_metrics: dict | None,
    spec_scores: dict | None,
    spec_text: str | None,
    codebase_modules: list[str] | None,
    red_flags_cfg: dict,
) -> list[str]:
    """All red flags for a submission, for reuse outside the terminal report (e.g. markdown)."""
    flags = compute_graph_red_flags(graph_metrics, red_flags_cfg)
    if complexity_metrics is not None:
        flags += compute_complexity_red_flags(complexity_metrics, red_flags_cfg)
    if spec_scores is not None:
        flags += compute_spec_red_flags(spec_scores, spec_text or "", codebase_modules or [], red_flags_cfg)
    return flags


def render_graph_section(console: Console, metrics: dict) -> None:
    summary = Table(title="Graph Metrics", header_style="bold magenta")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")
    summary.add_row("Files", str(metrics["node_count"]))
    summary.add_row("Avg Fan-In", f"{metrics['avg_fan_in']:.2f}")
    summary.add_row("Max Fan-In", str(metrics["max_fan_in"]))
    summary.add_row("Avg Fan-Out", f"{metrics['avg_fan_out']:.2f}")
    summary.add_row("Max Fan-Out", str(metrics["max_fan_out"]))
    summary.add_row("Longest Dependency Path", str(metrics["longest_dependency_path"]))
    summary.add_row("Circular Dependencies", str(len(metrics["circular_dependencies"])))
    summary.add_row("Modularity Score", f"{metrics['modularity_score']:.3f}")
    summary.add_row("Avg Betweenness", f"{metrics['avg_betweenness_centrality']:.4f}")
    summary.add_row("Max Betweenness", f"{metrics['max_betweenness_centrality']:.4f}")
    console.print(summary)

    top = Table(title="Top Betweenness Nodes (potential bottlenecks)", header_style="bold magenta")
    top.add_column("File")
    top.add_column("Betweenness", justify="right")
    for entry in metrics["top_betweenness_nodes"]:
        top.add_row(entry["node"], f"{entry['betweenness']:.4f}")
    console.print(top)


def render_complexity_section(console: Console, metrics: dict) -> None:
    summary = Table(title="Complexity Metrics", header_style="bold magenta")
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")
    summary.add_row("Total Functions", str(metrics["total_functions"]))
    summary.add_row("Avg Cyclomatic Complexity", f"{metrics['avg_cyclomatic_complexity']:.2f}")
    summary.add_row("Max Cyclomatic Complexity", str(metrics["max_cyclomatic_complexity"]))
    summary.add_row("Avg Function Length (NLOC)", f"{metrics['avg_function_length_nloc']:.1f}")
    summary.add_row("Avg Parameter Count", f"{metrics['avg_parameter_count']:.1f}")
    summary.add_row(
        "Functions Above CCN Threshold (10)",
        str(len(metrics["functions_above_complexity_threshold"])),
    )
    console.print(summary)

    above = metrics["functions_above_complexity_threshold"]
    if above:
        worst = Table(title="Most Complex Functions", header_style="bold magenta")
        worst.add_column("Function")
        worst.add_column("File")
        worst.add_column("CCN", justify="right")
        worst.add_column("NLOC", justify="right")
        for func in sorted(above, key=lambda f: -f["ccn"])[:5]:
            worst.add_row(func["name"], func["file"], str(func["ccn"]), str(func["nloc"]))
        console.print(worst)


def render_structure_section(console: Console, structure_scores: dict) -> float:
    table = Table(title="Structure Quality (Code Metrics)", header_style="bold magenta")
    table.add_column("Dimension", no_wrap=True)
    table.add_column("Weight", justify="right", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("", no_wrap=True)
    table.add_column("Level", justify="right", no_wrap=True)
    for dim, weight in STRUCTURE_WEIGHTS.items():
        answer = structure_scores[dim]
        table.add_row(
            dim.replace("_", " ").title(),
            f"{weight:.0%}",
            f"{answer['score_0_10']:.1f} / 10",
            score_bar(answer["score_0_10"]),
            f"{answer['level']} ({answer['level_label']})",
        )
    console.print(table)
    total = weighted_structure_total(structure_scores)
    console.print(f"[bold]Structure Weighted Total: {total:.1f} / 10[/bold]")
    return total


def render_spec_section(console: Console, spec_scores: dict) -> float:
    weakest = spec_scores["weakest_dimension"]
    console.print(
        f"Weakest Dimension (diagnostic): [yellow]{weakest['choice']}[/yellow] "
        f"({weakest['confidence']:.0%} confidence)"
    )

    table = Table(title="Spec Quality (Jev)", header_style="bold magenta")
    table.add_column("Dimension", no_wrap=True)
    table.add_column("Weight", justify="right", no_wrap=True)
    table.add_column("Score", justify="right", no_wrap=True)
    table.add_column("", no_wrap=True)
    table.add_column("Jev Answer", justify="right", no_wrap=True)
    table.add_column("Confidence", justify="right", no_wrap=True)
    for dim, weight in SPEC_WEIGHTS.items():
        answer = spec_scores[dim]
        table.add_row(
            dim.replace("_", " ").title(),
            f"{weight:.0%}",
            f"{answer['score_0_10']:.1f} / 10",
            score_bar(answer["score_0_10"]),
            answer["answer"],
            f"{answer['confidence']:.0%}",
        )
    console.print(table)
    total = weighted_spec_total(spec_scores)
    console.print(f"[bold]Spec Weighted Total: {total:.1f} / 10[/bold]")
    return total


def render_report(
    console: Console,
    team_name: str,
    graph_metrics: dict,
    config: dict,
    complexity_metrics: dict | None = None,
    structure_scores: dict | None = None,
    structure_skip_reason: str = "No source.zip found — complexity metrics needed for structure scoring.",
    spec_scores: dict | None = None,
    spec_text: str | None = None,
    codebase_modules: list[str] | None = None,
    spec_skip_reason: str = "Jev spec scoring skipped.",
) -> None:
    console.print(Panel(f"[bold]scorer_cli[/bold] — Structure Report: [cyan]{team_name}[/cyan]"))
    red_flags_cfg = config.get("red_flags", {})

    render_graph_section(console, graph_metrics)
    flags = compute_graph_red_flags(graph_metrics, red_flags_cfg)

    if complexity_metrics is not None:
        render_complexity_section(console, complexity_metrics)
        flags += compute_complexity_red_flags(complexity_metrics, red_flags_cfg)
    else:
        console.print(
            Panel(
                "No source.zip found — complexity metrics skipped.",
                title="Complexity Metrics",
                border_style="yellow",
            )
        )

    structure_total = None
    if structure_scores is not None:
        structure_total = render_structure_section(console, structure_scores)
    else:
        console.print(
            Panel(structure_skip_reason, title="Structure Quality (Code Metrics)", border_style="yellow")
        )

    spec_total = None
    if spec_scores is not None:
        spec_total = render_spec_section(console, spec_scores)
        flags += compute_spec_red_flags(
            spec_scores, spec_text or "", codebase_modules or [], red_flags_cfg
        )
    else:
        console.print(Panel(spec_skip_reason, title="Spec Quality (Jev)", border_style="yellow"))

    if structure_total is not None and spec_total is not None:
        weights = config.get("weights", {"structure": 0.5, "spec": 0.5})
        combined = structure_total * weights["structure"] + spec_total * weights["spec"]
        meter = score_bar(combined, width=40)
        console.print(
            Panel(
                f"[bold]{combined:.1f} / 10[/bold]  "
                f"(structure {weights['structure']:.0%} + spec {weights['spec']:.0%})\n\n"
                f"{meter} {combined / 10:.0%}",
                title="Combined Score",
                border_style="cyan",
            )
        )

    if flags:
        body = "\n".join(f"[red]⚠[/red]  {f}" for f in flags)
        console.print(Panel(body, title="Red Flags", border_style="red"))
    else:
        console.print(Panel("No red flags detected.", title="Red Flags", border_style="green"))
