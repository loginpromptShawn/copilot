from __future__ import annotations

import functools
import logging
from contextlib import contextmanager
from typing import Callable, Optional

from . import tracer as tracer_module

logger = logging.getLogger(__name__)


def trace_function(name: Optional[str] = None):
    def decorator(func: Callable):
        fname = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = tracer_module.global_tracer
            span = None
            if tracer is not None:
                try:
                    span = tracer.start_span(fname)
                except Exception:
                    logger.exception("Failed to start span for %s", fname)
            try:
                return func(*args, **kwargs)
            finally:
                if tracer is not None and span is not None:
                    try:
                        tracer.finish_span(span)
                    except Exception:
                        logger.exception("Failed to finish span for %s", fname)

        return wrapper

    return decorator


@contextmanager
def trace_block(name: str):
    tracer = tracer_module.global_tracer
    span = None
    if tracer is not None:
        span = tracer.start_span(name)
    try:
        yield
    finally:
        if tracer is not None and span is not None:
            tracer.finish_span(span)
