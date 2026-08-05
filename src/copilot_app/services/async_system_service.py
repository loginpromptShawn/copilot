from __future__ import annotations

import asyncio
import platform
from typing import Any

from ..persistence.repository import SystemInfoRepository


async def get_system_info(*args: Any, app_context: dict | None = None) -> str:
    # run platform calls in thread
    os_name = await asyncio.to_thread(platform.system)
    version = await asyncio.to_thread(platform.release)
    info = await asyncio.to_thread(SystemInfoRepository().save_system_info, os_name, version)
    return (
        f"System: {os_name} {version}\n"
        f"Platform: {platform.platform()}\n"
        "Home: /Users/bong\n"
        f"Saved id: {info.id}"
    )


async def store_system_info(*args: Any, app_context: dict | None = None) -> Any:
    os_name = await asyncio.to_thread(platform.system)
    version = await asyncio.to_thread(platform.release)
    repo = SystemInfoRepository()
    info = await asyncio.to_thread(repo.save_system_info, os_name, version)
    return info
