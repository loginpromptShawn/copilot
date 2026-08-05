from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Type, Any
from ..tracing.tracer import global_tracer

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[Type[Any], List[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        tracer = global_tracer
        span = None
        if tracer is not None:
            try:
                span = tracer.start_span(f"subscribe:{event_type.__name__}")
            except Exception:
                logger.exception("Failed to start subscribe span")
        with self._lock:
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.debug("Handler %s subscribed to %s", handler, event_type)
        if tracer is not None and span is not None:
            try:
                tracer.finish_span(span)
            except Exception:
                logger.exception("Failed to finish subscribe span")

    def unsubscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        tracer = global_tracer
        span = None
        if tracer is not None:
            try:
                span = tracer.start_span(f"unsubscribe:{event_type.__name__}")
            except Exception:
                logger.exception("Failed to start unsubscribe span")
        with self._lock:
            if handler in self._handlers.get(event_type, []):
                self._handlers[event_type].remove(handler)
                logger.debug("Handler %s unsubscribed from %s", handler, event_type)
        if tracer is not None and span is not None:
            try:
                tracer.finish_span(span)
            except Exception:
                logger.exception("Failed to finish unsubscribe span")

    def publish(self, event: Any) -> None:
        etype = type(event)
        logger.info("Publishing event %s: %s", etype.__name__, event)
        tracer = global_tracer
        pub_span = None
        if tracer is not None:
            try:
                pub_span = tracer.start_span(f"publish:{etype.__name__}")
            except Exception:
                logger.exception("Failed to start publish span")
        handlers: List[Callable[[Any], None]]
        with self._lock:
            handlers = list(self._handlers.get(etype, []))

        for h in handlers:
            handler_span = None
            if tracer is not None:
                try:
                    handler_span = tracer.start_span(f"handler:{getattr(h, '__name__', repr(h))}")
                except Exception:
                    logger.exception("Failed to start handler span")
            try:
                h(event)
            except Exception:
                logger.exception("Error in event handler %s for event %s", h, etype)
            finally:
                if tracer is not None and handler_span is not None:
                    try:
                        tracer.finish_span(handler_span)
                    except Exception:
                        logger.exception("Failed to finish handler span")

        if tracer is not None and pub_span is not None:
            try:
                tracer.finish_span(pub_span)
            except Exception:
                logger.exception("Failed to finish publish span")


# global default bus (applications can override by assigning a new instance)
global_event_bus = EventBus()
