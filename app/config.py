"""Load config.yaml: weights, thresholds, and red-flag rules."""

from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy config.yaml.example to config.yaml and fill in your settings."
        )
    with open(path) as f:
        return yaml.safe_load(f)
