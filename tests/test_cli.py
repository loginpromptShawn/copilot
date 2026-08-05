from copilot_app.cli import main


def test_greet_command(capsys):
    exit_code = main(["greet", "Shawn"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Hello, Shawn from macOS!" in captured.out


def test_version_flag(capsys):
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "copilot 0.1.0 (macOS CLI)" in captured.out
