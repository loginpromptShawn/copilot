from __future__ import annotations

import logging
from typing import List

from fastapi import FastAPI, Response

from .metrics_registry import global_metrics_registry

logger = logging.getLogger(__name__)


class MetricsExporter:
    def __init__(self, registry=None) -> None:
        self.registry = registry or global_metrics_registry

    def export_metrics(self) -> str:
        lines: List[str] = []
        # counters
        for (name, labels), value in self.registry.counters.items():
            label_text = ""
            if labels:
                label_text = "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}"
            lines.append(f"{name}{label_text} {value}")

        # gauges
        for (name, labels), value in self.registry.gauges.items():
            label_text = ""
            if labels:
                label_text = "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}"
            lines.append(f"{name}{label_text} {value}")

        # histograms: export sum and count
        for (name, labels), samples in self.registry.histograms.items():
            label_text = ""
            if labels:
                label_text = "{" + ",".join(f'{k}="{v}"' for k, v in labels) + "}"
            count = len(samples)
            summ = sum(samples) if samples else 0.0
            lines.append(f"{name}_count{label_text} {count}")
            lines.append(f"{name}_sum{label_text} {summ}")

        return "\n".join(lines)


# FastAPI app providing /metrics endpoint
fastapi_app = FastAPI()


@fastapi_app.get("/metrics")
def metrics_endpoint() -> Response:
    exporter = MetricsExporter()
    data = exporter.export_metrics()
    return Response(content=data, media_type="text/plain; version=0.0.4")
