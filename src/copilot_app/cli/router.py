from typing import Callable

from ..auth.cli_auth import login, register_user, whoami
from ..cli.commands import _resilience_status, _resilience_test

AUTH_COMMANDS: dict[str, Callable[..., str]] = {
    "register-user": register_user,
    "login": login,
    "whoami": whoami,
    "resilience-status": _resilience_status,
    "resilience-test": _resilience_test,
}


def get_auth_command_handler(command_name: str) -> Callable[..., str] | None:
    return AUTH_COMMANDS.get(command_name)
