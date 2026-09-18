from pathlib import Path

from app.metrics import (
    compute_complexity_metrics,
    compute_complexity_metrics_from_zip,
    extract_source,
)

SAMPLE_ZIP = Path(__file__).parent.parent / "fixtures" / "sample_team_phoenix" / "source.zip"

SIMPLE_FUNCTION = """
def add(a, b):
    return a + b
"""

BRANCHY_FUNCTION = """
def classify(x):
    result = ""
    if x == 0: result = "0"
    if x == 1: result = "1"
    if x == 2: result = "2"
    if x == 3: result = "3"
    if x == 4: result = "4"
    if x == 5: result = "5"
    if x == 6: result = "6"
    if x == 7: result = "7"
    if x == 8: result = "8"
    if x == 9: result = "9"
    if x == 10: result = "10"
    if x == 11: result = "11"
    return result
"""


def test_extract_source(tmp_path):
    dest = extract_source(SAMPLE_ZIP, tmp_path)
    assert (dest / "app" / "main.py").exists()
    assert (dest / "app" / "timer.py").exists()


def test_simple_function_has_ccn_one(tmp_path):
    (tmp_path / "simple.py").write_text(SIMPLE_FUNCTION)
    m = compute_complexity_metrics(tmp_path)
    assert m["total_functions"] == 1
    assert m["max_cyclomatic_complexity"] == 1
    assert m["functions_above_complexity_threshold"] == []


def test_branchy_function_exceeds_threshold(tmp_path):
    (tmp_path / "branchy.py").write_text(BRANCHY_FUNCTION)
    m = compute_complexity_metrics(tmp_path)
    assert m["total_functions"] == 1
    assert m["max_cyclomatic_complexity"] > 10
    above = m["functions_above_complexity_threshold"]
    assert len(above) == 1
    assert above[0]["name"] == "classify"
    assert above[0]["file"] == "branchy.py"


def test_non_code_files_are_ignored(tmp_path):
    (tmp_path / "notes.md").write_text("# not code, has def foo(): pass in prose")
    (tmp_path / "styles.css").write_text("body { color: red; }")
    m = compute_complexity_metrics(tmp_path)
    assert m["total_functions"] == 0


def test_pycache_dir_is_excluded(tmp_path):
    (tmp_path / "simple.py").write_text(SIMPLE_FUNCTION)
    cache_dir = tmp_path / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "simple.cpython-311.pyc").write_bytes(b"\x00\x01")
    m = compute_complexity_metrics(tmp_path)
    assert m["total_functions"] == 1


def test_avg_parameter_count(tmp_path):
    (tmp_path / "params.py").write_text("def f(a, b, c):\n    return a + b + c\n")
    m = compute_complexity_metrics(tmp_path)
    assert m["avg_parameter_count"] == 3


def test_smoke_on_real_sample_zip():
    m = compute_complexity_metrics_from_zip(SAMPLE_ZIP)
    assert m["total_functions"] > 0
    assert m["avg_function_length_nloc"] > 0
