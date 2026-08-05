from __future__ import annotations

import logging
from typing import Any

from ..persistence.repository import UserRepository, SystemInfoRepository
from .event_types import UserCreatedEvent, SystemInfoUpdatedEvent, LogCleanupEvent


logger = logging.getLogger(__name__)


def handle_user_created(event: UserCreatedEvent) -> None:
    logger.info("handle_user_created: %s", event)
    try:
        # optional: store metadata or perform side-effects
        repo = UserRepository()
        # maybe update an audit table or similar; placeholder
        _ = repo.get_user(event.user_id)
    except Exception:
        logger.exception("Error handling user created event")


def handle_system_info_updated(event: SystemInfoUpdatedEvent) -> None:
    logger.info("handle_system_info_updated: %s", event)
    try:
        repo = SystemInfoRepository()
        _ = repo.save_system_info(event.os, event.version)
    except Exception:
        logger.exception("Error handling system info updated event")


def handle_log_cleanup(event: LogCleanupEvent) -> None:
    logger.info("handle_log_cleanup: %s", event)
