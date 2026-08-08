import configparser
from pathlib import Path

from copilot_app.utils.config import get_config


def unit_get_config_defaults_when_file_missing(tmp_path, monkeypatch):
    missing = tmp_path / "nonexistent.ini"
    monkeypatch.setattr("copilot_app.utils.config.Path", lambda *a, **k: tmp_path)
    parser = get_config(missing)
    assert "app" in parser
    assert parser["app"]["name"] == "copilot"
    assert parser["app"]["version"] == "0.1.0"


def unit_get_config_reads_existing_file(tmp_path):
    cfg = tmp_path / "app.ini"
    cfg.write_text("[app]\nname = testapp\nversion = 1.0\n")
    parser = get_config(cfg)
    assert parser["app"]["name"] == "testapp"
    assert parser["app"]["version"] == "1.0"


def unit_get_config_default_path_uses_project_config():
    parser = get_config()
    assert "app" in parser