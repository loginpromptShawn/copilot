from __future__ import annotations

import configparser
from pathlib import Path


def get_config(config_path: str | Path | None = None) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config.ini"
    parser.read(config_path)
    if not parser.sections():
        parser["app"] = {
            "name": "copilot",
            "version": "0.1.0",
        }
    return parser
