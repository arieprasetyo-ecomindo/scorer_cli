import pytest

from app.config import load_config

REAL_CONFIG = "config.yaml"


def test_load_real_config_has_expected_sections():
    config = load_config(REAL_CONFIG)
    assert config["weights"]["structure"] == 0.5
    assert config["weights"]["spec"] == 0.5
    assert "red_flags" in config
    assert "spec_rubric" in config


def test_load_missing_config_raises_clear_error(tmp_path):
    missing = tmp_path / "does-not-exist.yaml"
    with pytest.raises(FileNotFoundError, match="config.yaml.example"):
        load_config(missing)
