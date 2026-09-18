import argparse
from pathlib import Path

from rich.console import Console

from app.metrics import build_file_graph, compute_graph_metrics, load_graph
from app.report_generator import render_graph_report

FIXTURES_DIR = Path("fixtures")


def report(team_name: str) -> None:
    graph_path = FIXTURES_DIR / team_name / "graph.json"
    if not graph_path.exists():
        raise SystemExit(f"No graph.json found for '{team_name}' at {graph_path}")

    raw = load_graph(graph_path)
    file_graph = build_file_graph(raw)
    metrics = compute_graph_metrics(file_graph)

    render_graph_report(Console(), team_name, metrics)


def main() -> None:
    parser = argparse.ArgumentParser(prog="score-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser(
        "report", help="Show a graph metrics report for a team fixture"
    )
    report_parser.add_argument(
        "team_name", help="Folder name under fixtures/, e.g. sample_team_phoenix"
    )

    args = parser.parse_args()

    if args.command == "report":
        report(args.team_name)


if __name__ == "__main__":
    main()
