from copilot_app.cli import main


def unit_greet_command(capsys):
    exit_code = main(["greet", "Shawn"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Hello, Shawn from macOS!" in captured.out


def unit_version_flag(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "copilot 0.1.0 (macOS CLI)" in captured.out


def unit_unknown_command_returns_nonzero(capsys):
    exit_code = main(["nonexistent_command"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Unknown command" in captured.out


def unit_no_command_prints_help(capsys):
    exit_code = main([])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "usage:" in captured.out.lower() or "command" in captured.out.lower()
