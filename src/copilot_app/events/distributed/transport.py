from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Callable, Dict, List


class Transport(ABC):
    @abstractmethod
    def publish(self, topic: str, message: str) -> None:
        raise NotImplementedError()

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[str], None]) -> None:
        raise NotImplementedError()


class InMemoryTransport(Transport):
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[str], None]]] = {}
        self._lock = threading.Lock()

    def publish(self, topic: str, message: str) -> None:
        with self._lock:
            handlers = list(self._handlers.get(topic, []))
        for h in handlers:
            try:
                h(message)
            except Exception:
                # swallow handler errors
                pass

    def subscribe(self, topic: str, handler: Callable[[str], None]) -> None:
        with self._lock:
            if topic not in self._handlers:
                self._handlers[topic] = []
            if handler not in self._handlers[topic]:
                self._handlers[topic].append(handler)


class RedisTransport(Transport):
    def __init__(self, url: str) -> None:
        # TODO: implement Redis-based pub/sub transport
        self.url = url

    def publish(self, topic: str, message: str) -> None:
        # TODO: publish to Redis channel
        raise NotImplementedError()

    def subscribe(self, topic: str, handler: Callable[[str], None]) -> None:
        # TODO: subscribe to Redis channel and call handler for messages
        raise NotImplementedError()
