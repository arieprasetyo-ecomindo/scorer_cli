import argparse
from pathlib import Path

from rich.console import Console

from app.metrics import (
    build_file_graph,
    compute_complexity_metrics_from_zip,
    compute_graph_metrics,
    load_graph,
)
from app.report_generator import render_report

FIXTURES_DIR = Path("fixtures")


def report(team_name: str) -> None:
    team_dir = FIXTURES_DIR / team_name
    graph_path = team_dir / "graph.json"
    if not graph_path.exists():
        raise SystemExit(f"No graph.json found for '{team_name}' at {graph_path}")

    raw = load_graph(graph_path)
    file_graph = build_file_graph(raw)
    graph_metrics = compute_graph_metrics(file_graph)

    source_zip = team_dir / "source.zip"
    complexity_metrics = (
        compute_complexity_metrics_from_zip(source_zip) if source_zip.exists() else None
    )

    render_report(Console(), team_name, graph_metrics, complexity_metrics)


def main() -> None:
    parser = argparse.ArgumentParser(prog="score-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report", help="Show a structure metrics report for a team fixture"
    )
    report_parser.add_argument(
        "team_name", help="Folder name under fixtures/, e.g. sample_team_phoenix"
    )

    args = parser.parse_args()

    if args.command == "report":
        report(args.team_name)


if __name__ == "__main__":
    main()
