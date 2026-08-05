from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict
import uuid
import time


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_id: Optional[str]
    name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    attributes: Dict[str, str] = field(default_factory=dict)

    def finish(self) -> None:
        if self.end_time is None:
            self.end_time = time.time()

    def duration(self) -> Optional[float]:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @staticmethod
    def new(name: str, parent: Optional["Span"] = None) -> "Span":
        trace_id = parent.trace_id if parent is not None else str(uuid.uuid4())
        span_id = str(uuid.uuid4())
        parent_id = parent.span_id if parent is not None else None
        return Span(trace_id=trace_id, span_id=span_id, parent_id=parent_id, name=name)
