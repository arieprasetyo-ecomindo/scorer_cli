import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
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
    load_dotenv()

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

    jev_scores = None
    jev_skip_reason = "No TYPESAFE_API_KEY found."
    if complexity_metrics is None:
        jev_skip_reason = "No source.zip found — complexity metrics needed for Jev scoring."
    elif os.environ.get("TYPESAFE_API_KEY"):
        from typesafe_sdk import TypeSafeAPIError, TypeSafeClient

        from app.jev_scorer import build_jev_log, score_structure_with_response, write_jev_log

        try:
            jev_scores, response = score_structure_with_response(
                graph_metrics, complexity_metrics, TypeSafeClient()
            )
            log_path = write_jev_log(team_dir, build_jev_log(team_name, response))
            print(f"Jev response logged to {log_path}")
        except TypeSafeAPIError as e:
            jev_skip_reason = f"Jev scoring failed: {e}"

    render_report(
        Console(), team_name, graph_metrics, complexity_metrics, jev_scores, jev_skip_reason
    )


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
