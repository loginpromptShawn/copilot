from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from .span import Span

logger = logging.getLogger(__name__)


class Tracer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spans_by_trace: Dict[str, List[Span]] = {}
        self._local = threading.local()

    def _stack(self) -> List[Span]:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    def start_span(self, name: str, parent: Optional[Span] = None) -> Span:
        stack = self._stack()
        if parent is None and stack:
            parent = stack[-1]
        span = Span.new(name, parent)
        stack.append(span)
        with self._lock:
            self._spans_by_trace.setdefault(span.trace_id, []).append(span)
        logger.debug("Started span %s (%s)", span.name, span.span_id)
        return span

    def finish_span(self, span: Span) -> None:
        try:
            span.finish()
            stack = self._stack()
            if stack and stack[-1] is span:
                stack.pop()
            logger.debug("Finished span %s (%s) duration=%s", span.name, span.span_id, span.duration())
        except Exception:
            logger.exception("Error finishing span")

    def get_trace(self, trace_id: str) -> List[Span]:
        with self._lock:
            return list(self._spans_by_trace.get(trace_id, []))

    def get_all_traces(self) -> Dict[str, List[Span]]:
        with self._lock:
            return {k: list(v) for k, v in self._spans_by_trace.items()}


# module-level default tracer
global_tracer: Tracer | None = None
