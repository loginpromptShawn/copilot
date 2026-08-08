from __future__ import annotations

import configparser
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_config(config_path: str | Path | None = None) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    if config_path is None:
        config_path = Path(__file__).resolve().parents[2] / "config.ini"
    parser.read(config_path)
    if not parser.sections():
        logger.warning("Config file not found or empty at %s, using defaults", config_path)
        parser["app"] = {
            "name": "copilot",
            "version": "0.1.0",
        }
    return parser
