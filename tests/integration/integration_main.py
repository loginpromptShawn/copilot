from copilot_app.main import main


def integration_main_no_args_returns_nonzero():
    # main() with no command should print help and return nonzero
    rc = main([])
    assert rc == 1


def integration_main_version_flag():
    rc = main(["--version"])
    assert rc == 0


def integration_main_unknown_command():
    rc = main(["totally-unknown-command"])
    assert rc == 1
