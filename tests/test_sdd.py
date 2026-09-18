from pathlib import Path

from app.metrics import extract_spec_text, extract_spec_text_from_zip

SAMPLE_SDD_ZIP = Path(__file__).parent.parent / "fixtures" / "sample_team_phoenix" / "sdd.zip"


def test_concatenates_markdown_files_with_headers(tmp_path):
    (tmp_path / "a.md").write_text("Spec A content")
    (tmp_path / "b.txt").write_text("Spec B content")
    text = extract_spec_text(tmp_path)
    assert "## a.md" in text
    assert "Spec A content" in text
    assert "## b.txt" in text
    assert "Spec B content" in text


def test_nested_directories_are_included(tmp_path):
    nested = tmp_path / "openspec" / "specs" / "pomodoro-timer"
    nested.mkdir(parents=True)
    (nested / "spec.md").write_text("Pomodoro requirements")
    text = extract_spec_text(tmp_path)
    assert "openspec/specs/pomodoro-timer/spec.md" in text
    assert "Pomodoro requirements" in text


def test_non_spec_files_are_ignored(tmp_path):
    (tmp_path / "config.yaml").write_text("schema: spec-driven")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    text = extract_spec_text(tmp_path)
    assert text == ""


def test_output_is_deterministic(tmp_path):
    (tmp_path / "z.md").write_text("Z")
    (tmp_path / "a.md").write_text("A")
    text = extract_spec_text(tmp_path)
    assert text.index("## a.md") < text.index("## z.md")


def test_smoke_on_real_sample_sdd_zip():
    text = extract_spec_text_from_zip(SAMPLE_SDD_ZIP)
    assert "Pomodoro" in text
    assert "## openspec/specs/pomodoro-timer/spec.md" in text
