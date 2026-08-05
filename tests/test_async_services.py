import asyncio

import pytest

from copilot_app.services.async_user_service import greet_user, store_user
from copilot_app.services.async_system_service import get_system_info, store_system_info


@pytest.mark.asyncio
async def test_greet_user():
    res = await greet_user("TestUser")
    assert "Hello, TestUser" in res


@pytest.mark.asyncio
async def test_store_user():
    user = await store_user("AsyncUser")
    assert user is not None
    assert user.name == "AsyncUser"


@pytest.mark.asyncio
async def test_get_system_info():
    info = await get_system_info()
    assert "System:" in info


@pytest.mark.asyncio
async def test_store_system_info():
    info = await store_system_info()
    assert info is not None
