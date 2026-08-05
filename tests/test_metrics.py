from copilot_app.metrics.metrics_registry import MetricsRegistry
from copilot_app.metrics.collectors import system_metrics_collector, app_metrics_collector
from copilot_app.metrics.exporters import MetricsExporter


def test_metrics_registry_basic():
    reg = MetricsRegistry()
    reg.increment_counter("test_counter")
    reg.increment_counter("test_counter")
    reg.set_gauge("test_gauge", 3.14)
    reg.observe_histogram("test_hist", 1.0)
    reg.observe_histogram("test_hist", 2.0)

    exporter = MetricsExporter(registry=reg)
    out = exporter.export_metrics()
    assert "test_counter" in out
    assert "test_gauge" in out
    assert "test_hist_count" in out


def test_collectors_run(tmp_path):
    # ensure collectors run without error
    reg = MetricsRegistry()
    system_metrics_collector(reg)
    app_metrics_collector(reg)
    exporter = MetricsExporter(registry=reg)
    out = exporter.export_metrics()
    # system gauges should be present
    assert "system_cpu_percent" in out or "app_users_count" in out
