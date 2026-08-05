import os
import json
from pathlib import Path

import pytest

from copilot_app.tracing.tracer import Tracer, global_tracer
from copilot_app.tracing.span import Span
from copilot_app.tracing.exporters import TraceExporter, TRACE_DIR
from copilot_app.tracing.instrumentation import trace_function, trace_block


def setup_function(fn):
    # reset global tracer
    global_tracer = None


def test_span_creation_and_finish(tmp_path):
    tracer = Tracer()
    # set module-level global_tracer
    import importlib

    tr_mod = importlib.import_module("copilot_app.tracing.tracer")
    tr_mod.global_tracer = tracer

    span = tracer.start_span("test")
    assert span.start_time is not None
    tracer.finish_span(span)
    assert span.end_time is not None
    traces = tracer.get_all_traces()
    assert span.trace_id in traces


def test_nested_spans():
    tracer = Tracer()
    import importlib

    tr_mod = importlib.import_module("copilot_app.tracing.tracer")
    tr_mod.global_tracer = tracer

    parent = tracer.start_span("parent")
    child = tracer.start_span("child")
    tracer.finish_span(child)
    tracer.finish_span(parent)
    assert child.parent_id == parent.span_id
    assert child.trace_id == parent.trace_id


def test_exporter_writes_trace_file(tmp_path):
    tracer = Tracer()
    import importlib

    tr_mod = importlib.import_module("copilot_app.tracing.tracer")
    tr_mod.global_tracer = tracer

    span = tracer.start_span("export-test")
    tracer.finish_span(span)

    exporter = TraceExporter(tracer)
    traces = exporter.export_all()
    assert isinstance(traces, list)
    # ensure files were written
    assert TRACE_DIR.exists()


def test_instrumentation_decorator_records_span():
    tracer = Tracer()
    import importlib

    tr_mod = importlib.import_module("copilot_app.tracing.tracer")
    tr_mod.global_tracer = tracer

    @trace_function("decorated_test")
    def foo(x):
        return x * 2

    assert foo(3) == 6
    traces = tracer.get_all_traces()
    # there should be at least one trace recorded
    assert len(traces) >= 1
