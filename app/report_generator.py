"""Render graph metrics as a Rich terminal report."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def compute_red_flags(metrics: dict) -> list[str]:
    flags = []

    for cycle in metrics["circular_dependencies"]:
        touched = len(cycle) - 1  # cycle list repeats the start node at the end
        if touched > 3:
            flags.append(f"Circular dependency touches {touched} modules: {' -> '.join(cycle)}")

    avg_in, avg_out = metrics["avg_fan_in"], metrics["avg_fan_out"]
    if avg_in > 0 and metrics["max_fan_in"] > 5 * avg_in:
        flags.append(f"Max fan-in {metrics['max_fan_in']} is > 5x the average ({avg_in:.1f})")
    if avg_out > 0 and metrics["max_fan_out"] > 5 * avg_out:
        flags.append(f"Max fan-out {metrics['max_fan_out']} is > 5x the average ({avg_out:.1f})")

    avg_b = metrics["avg_betweenness_centrality"]
    if avg_b > 0 and metrics["max_betweenness_centrality"] > 10 * avg_b:
        top = metrics["top_betweenness_nodes"][0]["node"]
        flags.append(f"Betweenness bottleneck: '{top}' is > 10x the average betweenness")

    return flags


def render_graph_report(console: Console, team_name: str, metrics: dict) -> None:
    console.print(Panel(f"[bold]scorer_cli[/bold] — Graph Metrics Report: [cyan]{team_name}[/cyan]"))

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

    flags = compute_red_flags(metrics)
    if flags:
        body = "\n".join(f"[red]⚠[/red]  {f}" for f in flags)
        console.print(Panel(body, title="Red Flags", border_style="red"))
    else:
        console.print(Panel("No red flags detected.", title="Red Flags", border_style="green"))
