from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Set, Type

from ..event_bus import EventBus
from .transport import Transport, InMemoryTransport
from .serializers import serialize_event, deserialize_event
from ..event_types import UserCreatedEvent, SystemInfoUpdatedEvent, LogCleanupEvent
from ...tracing import tracer as tracer_module

logger = logging.getLogger(__name__)


_TOPICS: Dict[Type[Any], str] = {
    UserCreatedEvent: "events.user.created",
    SystemInfoUpdatedEvent: "events.system.updated",
    LogCleanupEvent: "events.log.cleanup",
}


class DistributedEventBus:
    def __init__(self, local_bus: EventBus | None = None, transport: Transport | None = None) -> None:
        self.local_bus = local_bus or EventBus()
        self.transport = transport or InMemoryTransport()
        self._subscribed_topics: Set[str] = set()

    def _topic_for(self, event_type: Type[Any]) -> str:
        return _TOPICS.get(event_type, f"events.custom.{event_type.__name__}")

    def publish(self, event: Any) -> None:
        # publish locally first
        tracer = tracer_module.global_tracer
        pub_span = None
        if tracer is not None:
            try:
                pub_span = tracer.start_span(f"distributed_publish:{type(event).__name__}")
            except Exception:
                logger.exception("Failed to start distributed publish span")

        self.local_bus.publish(event)
        # then serialize and send via transport
        topic = self._topic_for(type(event))
        try:
            msg = serialize_event(event)
            self.transport.publish(topic, msg)
        except Exception:
            logger.exception("Failed to publish distributed event %s", event)
        finally:
            if tracer is not None and pub_span is not None:
                try:
                    tracer.finish_span(pub_span)
                except Exception:
                    logger.exception("Failed to finish distributed publish span")

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        # subscribe locally
        self.local_bus.subscribe(event_type, handler)
        # ensure we subscribe to transport for this topic to receive remote events
        topic = self._topic_for(event_type)
        if topic in self._subscribed_topics:
            return

        def _on_message(msg: str) -> None:
            try:
                tracer = tracer_module.global_tracer
                msg_span = None
                if tracer is not None:
                    try:
                        msg_span = tracer.start_span("distributed_receive")
                    except Exception:
                        logger.exception("Failed to start distributed receive span")
                evt = deserialize_event(msg)
                # re-emit into local bus
                self.local_bus.publish(evt)
                if tracer is not None and msg_span is not None:
                    try:
                        tracer.finish_span(msg_span)
                    except Exception:
                        logger.exception("Failed to finish distributed receive span")
            except Exception:
                logger.exception("Failed to deserialize/emit distributed message")

        self.transport.subscribe(topic, _on_message)
        self._subscribed_topics.add(topic)


# module-level default
global_distributed_bus: DistributedEventBus | None = None
