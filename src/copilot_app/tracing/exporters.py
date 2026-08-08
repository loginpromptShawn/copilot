from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

try:
    from fastapi import APIRouter, HTTPException
except ImportError:  # pragma: no cover
    APIRouter = None  # type: ignore
    HTTPException = Exception  # type: ignore

from .tracer import Tracer
from . import tracer as tracer_module

logger = logging.getLogger(__name__)

def _default_trace_dir() -> Path:
    try:
        from ..utils.config import get_config
        config = get_config()
        if config.has_section("paths") and config.has_option("paths", "data_dir"):
            return Path(config.get("paths", "data_dir")).parent / "traces"
    except Exception:
        pass
    return Path.home() / "copilot" / "traces"

TRACE_DIR = _default_trace_dir()
TRACE_DIR.mkdir(parents=True, exist_ok=True)


class TraceExporter:
    def __init__(self, tracer: Tracer | None = None) -> None:
        self.tracer = tracer or tracer_module.global_tracer

    def export_all(self) -> List[Dict[str, Any]]:
        if self.tracer is None:
            return []
        traces = []
        for trace_id, spans in self.tracer.get_all_traces().items():
            traces.append({"trace_id": trace_id, "spans": [self._span_to_dict(s) for s in spans]})
            self._write_trace_file(trace_id, spans)
        return traces

    def export_trace(self, trace_id: str) -> Dict[str, Any]:
        if self.tracer is None:
            raise KeyError("No tracer configured")
        spans = self.tracer.get_trace(trace_id)
        if not spans:
            raise KeyError(trace_id)
        self._write_trace_file(trace_id, spans)
        return {"trace_id": trace_id, "spans": [self._span_to_dict(s) for s in spans]}

    def _span_to_dict(self, s: "Span") -> Dict[str, Any]:
        return {
            "trace_id": s.trace_id,
            "span_id": s.span_id,
            "parent_id": s.parent_id,
            "name": s.name,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "duration": s.duration(),
            "attributes": s.attributes,
        }

    def _write_trace_file(self, trace_id: str, spans: List["Span"]) -> None:
        try:
            data = {"trace_id": trace_id, "spans": [self._span_to_dict(s) for s in spans]}
            path = TRACE_DIR / f"trace_{trace_id}.json"
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception:
            logger.exception("Failed writing trace file for %s", trace_id)


if APIRouter is not None:
    router = APIRouter()

    @router.get("/traces")
    def get_traces() -> List[Dict[str, Any]]:
        exporter = TraceExporter()
        return exporter.export_all()

    @router.get("/traces/{trace_id}")
    def get_trace(trace_id: str) -> Dict[str, Any]:
        exporter = TraceExporter()
        try:
            return exporter.export_trace(trace_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Trace not found")
else:
    router = None
