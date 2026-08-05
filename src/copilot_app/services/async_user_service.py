from __future__ import annotations

import asyncio
from typing import Any

from ..persistence.repository import UserRepository


async def greet_user(name: str) -> str:
    # simulate async work
    await asyncio.sleep(0.1)
    # create user asynchronously
    user = await store_user(name)
    return f"Hello, {user.name} from macOS! Your home directory is /Users/bong."


async def store_user(name: str) -> Any:
    repo = UserRepository()
    # call blocking DB operation in a thread
    user = await asyncio.to_thread(repo.create_user, name)
    return user
