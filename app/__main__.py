import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from app.config import load_config
from app.metrics import (
    build_file_graph,
    compute_complexity_metrics_from_zip,
    compute_graph_metrics,
    extract_codebase_modules,
    extract_spec_text_from_zip,
    load_graph,
)
from app.report_generator import compute_all_red_flags, render_report
from app.structure_scorer import score_structure

FIXTURES_DIR = Path("fixtures")
REPORTS_DIR = Path("reports")


def report(team_name: str) -> None:
    load_dotenv()
    config = load_config()

    team_dir = FIXTURES_DIR / team_name
    graph_path = team_dir / "graph.json"
    if not graph_path.exists():
        raise SystemExit(f"No graph.json found for '{team_name}' at {graph_path}")

    raw = load_graph(graph_path)
    file_graph = build_file_graph(raw)
    graph_metrics = compute_graph_metrics(file_graph)
    codebase_modules = extract_codebase_modules(raw)

    source_zip = team_dir / "source.zip"
    complexity_metrics = (
        compute_complexity_metrics_from_zip(source_zip) if source_zip.exists() else None
    )

    sdd_zip = team_dir / "sdd.zip"
    spec_text = extract_spec_text_from_zip(sdd_zip) if sdd_zip.exists() else None

    # Structure scoring is pure code - deterministic, no API call, no cost.
    structure_scores = None
    structure_skip_reason = "No source.zip found — complexity metrics needed for structure scoring."
    if complexity_metrics is not None:
        structure_scores = score_structure(graph_metrics, complexity_metrics)

    # Spec scoring is the one place Jev is actually used (judging prose).
    spec_scores = None
    spec_response = None
    spec_skip_reason = "No TYPESAFE_API_KEY found."
    if spec_text is None:
        spec_skip_reason = "No sdd.zip found — spec text needed for Jev scoring."
    elif os.environ.get("TYPESAFE_API_KEY"):
        from typesafe_sdk import TypeSafeAPIError, TypeSafeClient

        from app.jev_scorer import build_jev_log, score_spec_with_response, write_jev_log

        try:
            spec_scores, spec_response = score_spec_with_response(
                spec_text, codebase_modules, TypeSafeClient(), config.get("spec_rubric")
            )
            log_path = write_jev_log(team_dir, build_jev_log(team_name, spec_response))
            print(f"Jev response logged to {log_path}")
        except TypeSafeAPIError as e:
            spec_skip_reason = f"Jev scoring failed: {e}"

    render_report(
        Console(),
        team_name,
        graph_metrics,
        config,
        complexity_metrics,
        structure_scores,
        structure_skip_reason,
        spec_scores,
        spec_text,
        codebase_modules,
        spec_skip_reason,
    )

    if structure_scores is not None or spec_scores is not None:
        red_flags_cfg = config.get("red_flags", {})
        flags = compute_all_red_flags(
            graph_metrics, complexity_metrics, spec_scores, spec_text, codebase_modules, red_flags_cfg
        )

        report_cfg = config.get("report_generation", {})
        narrative = None
        if os.environ.get("ANTHROPIC_API_KEY"):
            from anthropic import Anthropic, APIError

            from app.llm_reporter import generate_fallback_narrative, generate_narrative

            try:
                narrative = generate_narrative(
                    structure_scores,
                    spec_scores,
                    flags,
                    Anthropic(),
                    model=report_cfg.get("model", "claude-opus-5"),
                    max_tokens=report_cfg.get("max_tokens", 600),
                )
            except APIError as e:
                print(f"Claude narrative generation failed ({e}); using fallback summary.")
                narrative = generate_fallback_narrative(structure_scores, spec_scores)
        else:
            from app.llm_reporter import generate_fallback_narrative

            narrative = generate_fallback_narrative(structure_scores, spec_scores)

        from app.report_writer import write_markdown_report

        report_path = write_markdown_report(
            team_name,
            REPORTS_DIR,
            structure_scores,
            spec_scores,
            narrative,
            flags,
            config.get("weights", {"structure": 0.5, "spec": 0.5}),
        )
        print(f"Markdown report written to {report_path}")


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
