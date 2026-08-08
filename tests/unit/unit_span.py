import time
import uuid

from copilot_app.tracing.span import Span


def unit_span_creation_without_parent():
    span = Span.new("test-span")
    assert span.name == "test-span"
    assert span.parent_id is None
    assert span.trace_id is not None
    assert span.span_id is not None
    assert span.start_time is not None
    assert span.end_time is None


def unit_span_creation_with_parent():
    parent = Span.new("parent-span")
    child = Span.new("child-span", parent=parent)
    assert child.name == "child-span"
    assert child.parent_id == parent.span_id
    assert child.trace_id == parent.trace_id
    assert child.span_id != parent.span_id


def unit_span_finish_sets_end_time():
    span = Span.new("span")
    assert span.end_time is None
    time.sleep(0.01)
    span.finish()
    assert span.end_time is not None
    assert span.end_time >= span.start_time


def unit_span_duration_returns_none_before_finish():
    span = Span.new("span")
    assert span.duration() is None


def unit_span_duration_after_finish():
    span = Span.new("span")
    time.sleep(0.01)
    span.finish()
    duration = span.duration()
    assert duration is not None
    assert duration >= 0.01


def unit_span_finish_idempotent():
    span = Span.new("span")
    first_end = span.finish()
    second_end = span.finish()
    assert first_end == second_end


def unit_span_with_attributes():
    span = Span.new("span")
    span.attributes = {"key": "value"}
    assert span.attributes == {"key": "value"}
