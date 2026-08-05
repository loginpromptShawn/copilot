from __future__ import annotations

from typing import Dict, Optional

from .commands import Command


class CommandRegistry:
    _commands: Dict[str, Command] = {}
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        cls._commands = {}
        cls._initialized = True

    @classmethod
    def populate_default_commands(cls) -> None:
        from .commands import COMMANDS

        if not cls._initialized:
            cls.initialize()
        for command in COMMANDS:
            cls._commands[command.name] = command

    @classmethod
    def get(cls, command_name: str) -> Optional[Command]:
        if not cls._initialized:
            cls.initialize()
        return cls._commands.get(command_name)

    @classmethod
    def all_commands(cls) -> list[Command]:
        if not cls._initialized:
            cls.initialize()
        return list(cls._commands.values())
