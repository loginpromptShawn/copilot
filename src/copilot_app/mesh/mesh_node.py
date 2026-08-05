from __future__ import annotations

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class MeshNode:
    def __init__(self, id: str, name: str, address: str, metadata: Dict[str, str] | None = None) -> None:
        self.id = id
        self.name = name
        self.address = address
        self.metadata = metadata or {}
        self.registered = False
        self.last_heartbeat: float | None = None

    def register(self) -> None:
        self.registered = True
        self.last_heartbeat = time.time()
        logger.info("MeshNode registered: %s (%s)", self.name, self.id)

    def deregister(self) -> None:
        self.registered = False
        logger.info("MeshNode deregistered: %s (%s)", self.name, self.id)

    def heartbeat(self) -> None:
        self.last_heartbeat = time.time()
        logger.debug("MeshNode heartbeat: %s (%s)", self.name, self.id)
