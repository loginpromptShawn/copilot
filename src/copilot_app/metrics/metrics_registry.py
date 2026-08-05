from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Dict, Tuple, List, Optional

logger = logging.getLogger(__name__)


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.counters: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], int] = defaultdict(int)
        self.gauges: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], float] = {}
        self.histograms: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], List[float]] = defaultdict(list)

    def _labels_key(self, labels: Optional[Dict[str, str]]) -> Tuple[Tuple[str, str], ...]:
        if not labels:
            return ()
        return tuple(sorted((str(k), str(v)) for k, v in labels.items()))

    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        key = (name, self._labels_key(labels))
        with self._lock:
            self.counters[key] += 1
            logger.debug("counter %s %s -> %d", name, labels, self.counters[key])

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        key = (name, self._labels_key(labels))
        with self._lock:
            self.gauges[key] = float(value)
            logger.debug("gauge %s %s -> %s", name, labels, value)

    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        key = (name, self._labels_key(labels))
        with self._lock:
            self.histograms[key].append(float(value))
            logger.debug("histogram %s %s observed %s", name, labels, value)


# module-level global registry (can be overridden by App on startup)
global_metrics_registry: MetricsRegistry = MetricsRegistry()
