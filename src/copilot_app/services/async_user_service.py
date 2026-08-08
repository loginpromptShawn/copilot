from __future__ import annotations

import asyncio
from typing import Any

from pathlib import Path

from ..persistence.repository import UserRepository


async def greet_user(*args: Any, app_context: dict | None = None) -> str:
    # simulate async work
    await asyncio.sleep(0.1)
    if not args:
        raise TypeError("greet_user() missing required positional argument: 'name'")
    name = args[0]
    # create user asynchronously
    user = await store_user(name, app_context=app_context)
    return f"Hello, {user.name} from macOS! Your home directory is {Path.home()}."


async def store_user(*args: Any, app_context: dict | None = None) -> Any:
    if not args:
        raise TypeError("store_user() missing required positional argument: 'name'")
    name = args[0]
    repo = UserRepository()
    # call blocking DB operation in a thread
    user = await asyncio.to_thread(repo.create_user, name)
    return user
