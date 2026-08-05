# Copilot Project

A fresh Python project scaffold created for development with Microsoft Copilot.

## macOS CLI Usage

Run the Copilot CLI directly from `src/copilot_app`:

```bash
python3 src/copilot_app/cli.py greet Shawn
```

To print version information:

```bash
python3 src/copilot_app/cli.py --version
```

## Logging and Configuration

This project loads configuration from `config.ini` at the repository root and initializes logging at startup.

- `config.ini` contains application settings and macOS-friendly paths.
- `logs/copilot.log` stores rotating log files created automatically by the CLI.
- If `config.ini` is missing, default values are used, including `/Users/bong/VSCode/copilot/data` for `data_dir`.

Edit `config.ini` to change the app name, environment, or data directory.

Example config section:

```ini
[app]
name = CopilotApp
environment = macos

[paths]
data_dir = /Users/bong/VSCode/copilot/data
```

## Modular Architecture

The project is organized into a clean modular architecture under `src/copilot_app`:

- `core/` — application orchestrator, router, and custom errors
- `services/` — domain-specific actions such as user greetings and system utilities
- `cli/` — command definitions and CLI entry point
- `utils/` — shared helpers for configuration and logging

This structure makes it easy to extend the CLI with new commands and services while keeping application concerns separated.

## Plugin System

This project includes a simple plugin system under `src/copilot_app/plugins`.

- `plugins/installed/` — drop-in plugin modules discovered at startup.
- Each plugin must implement the `BasePlugin` abstract class in `plugins/base_plugin.py`.

To add a plugin, create a Python file under `src/copilot_app/plugins/installed/` with a class inheriting `BasePlugin` and defining `name`, `version`, `description`, and `activate(app_context)` / `deactivate()` methods. Example plugin: `plugins/installed/example_plugin.py`.

Plugins are loaded automatically at application startup and activated with an `app_context` dictionary containing `app`, `config`, and `plugin_manager`.

## Async Support

This project includes optional async/await support.

- Async app entrypoint: `src/copilot_app/core/async_app.py` provides `AsyncApp` with `init()` and `run()` methods.
- Async router: `src/copilot_app/core/async_router.py` dispatches async commands.
- To run async commands from CLI, use the `async-greet` and `async-sysinfo` commands. Example:

```bash
python3 src/copilot_app/cli/cli.py async-greet Shawn
```

Async services live in `src/copilot_app/services/` as `async_user_service.py` and `async_system_service.py`.

## Background Job Scheduler

This project includes a lightweight background job scheduler under `src/copilot_app/scheduler`.

- `cleanup_logs()` — runs every hour to rotate/prune large log files under `/Users/bong/VSCode/copilot/logs`.
- `snapshot_system_info()` — runs every 5 minutes to record macOS system info to the database.

The scheduler uses a background thread and runs as soon as the application starts. It can be queried via the CLI command `scheduler-status` which reports `running` or `stopped`.

Notes for macOS:
- Long-running background threads keep the process alive; when running from Terminal, the app will continue until the process exits or `scheduler.stop()` is called.
- If you need system-level scheduling across reboots, consider using `launchd` instead of an in-process scheduler.

## Event Bus / Pub-Sub System

This project includes an in-process EventBus under `src/copilot_app/events`.

- Event types are defined in `event_types.py` (e.g., `UserCreatedEvent`, `SystemInfoUpdatedEvent`, `LogCleanupEvent`).
- `EventBus` supports `subscribe(event_type, handler)`, `unsubscribe(event_type, handler)`, and `publish(event)`.
- Core services and scheduler publish events (user creation, system snapshots, log cleanup). Subscribers live in `events/subscribers.py` and are registered at application startup.

To add a new event:
1. Define a dataclass in `event_types.py`.
2. Add subscriber handler in `events/subscribers.py` and register it in `core/app.py` during startup (or subscribe at runtime via `event_bus.subscribe`).

### Distributed Event Bus

The project provides a distributed extension under `src/copilot_app/events/distributed`:

- `Transport` abstraction (publish/subscribe). Includes `InMemoryTransport` for local testing and a `RedisTransport` stub to implement later.
- `serializers` handles JSON serialization/deserialization of events and embeds event type metadata.
- `DistributedEventBus` wraps the local `EventBus`, publishes serialized events via the transport, and re-emits incoming transport messages into the local `EventBus`.

To run distributed tests locally use `InMemoryTransport`. To integrate a real transport like Redis, implement `RedisTransport` and instantiate `DistributedEventBus` with it.


## Metrics & Monitoring

This project includes a lightweight metrics system under `src/copilot_app/metrics`.

- `MetricsRegistry` stores counters, gauges, and histograms in a thread-safe way.
- Collectors in `metrics/collectors.py` gather system and app metrics and update the registry.
- `metrics/exporters.py` exposes metrics in Prometheus text format and includes a FastAPI `/metrics` endpoint.

Collectors are scheduled to run periodically by the background scheduler. To access metrics via HTTP, run the FastAPI app (or mount `metrics/exporters.fastapi_app` into your ASGI server) and visit `/metrics`.

On macOS, install `psutil` for better system metrics: `pip install psutil`.


## Persistence (SQLite)

This project includes a simple SQLite persistence layer under `src/copilot_app/persistence`.

- Database file: `/Users/bong/VSCode/copilot/copilot.db`
- `database.py` provides `get_connection()` and `init_db()` to initialize tables.
- `models.py` defines `User` and `SystemInfo` dataclasses.
- `repository.py` provides `UserRepository` and `SystemInfoRepository` for CRUD operations.

Repositories are used by services to persist application data. The database is initialized automatically when the app starts.

To inspect the database on macOS, you can run:

```bash
sqlite3 /Users/bong/VSCode/copilot/copilot.db 
```

## Distributed Tracing

This project includes a lightweight distributed tracing system under `src/copilot_app/tracing`.

- `Span` (`span.py`): dataclass representing a trace span with `trace_id`, `span_id`, `parent_id`, `name`, timestamps, and attributes.
- `Tracer` (`tracer.py`): in-memory tracer that records spans and supports nested spans and thread-local span stacks.
- `TraceExporter` (`exporters.py`): exports traces to JSON files at `/Users/bong/VSCode/copilot/traces/` and exposes a FastAPI endpoint to view traces.
- `instrumentation` (`instrumentation.py`): provides `@trace_function(name=None)` decorator and `trace_block(name)` context manager for easy instrumentation.

How spans work:

- Spans are created with `Tracer.start_span(name)` and finished with `Tracer.finish_span(span)`.
- Nested spans inherit the `trace_id` of their parent and set `parent_id` appropriately.
- Durations are measured using `time.time()`.

Viewing traces:

- CLI: run `traces` via the CLI to print collected traces (JSON).
- API: the FastAPI app mounts tracing endpoints; `GET /traces` returns all traces and `GET /traces/{trace_id}` returns a single trace.
- Filesystem: JSON trace files are written to `/Users/bong/VSCode/copilot/traces/` (macOS path).

## Rate Limiting

This project includes a configurable rate limiting system under `src/copilot_app/rate_limit`.

- `TokenBucketStrategy` — token-bucket with `capacity` and `refill_rate` (tokens/sec).
- `FixedWindowStrategy` — fixed-window counting with `window_size` and `max_requests`.
- `SlidingWindowStrategy` — sliding-window with timestamp deque and eviction.
- `RateLimiter` — manages per-identifier strategy instances and evaluates `allow_request(identifier)`.
- `RateLimitMiddleware` — FastAPI middleware that blocks requests with HTTP 429 when limits are exceeded.

Configuration (config.ini):

```ini
[rate_limit]
strategy = token_bucket
capacity = 100
refill_rate = 10
```

How it applies:

- CLI: the `rate-limit-test` command runs a burst of requests against the configured limiter and prints allowed/blocked results.
- Services: `user_service` and `system_service` check the rate limiter before performing work and raise `RateLimitExceededError` if blocked.
- API: `RateLimitMiddleware` applies limits per-client IP by default.

macOS notes:

- The implementation uses thread-safe locks and `time.time()` for timestamps, suitable for the single-process CLI and FastAPI server on macOS.
- For distributed or multi-process rate limiting across machines, replace the per-instance strategies with a shared backend (Redis, etc.).


## Circuit Breaker System

This project includes a circuit breaker implementation under `src/copilot_app/circuit_breaker`.

- `CircuitState` — CLOSED, OPEN, HALF_OPEN.
- `CircuitPolicy` — configured with `failure_threshold`, `recovery_timeout`, and `half_open_max_calls`.
- `CircuitBreaker` — tracks `state`, `failure_count`, `last_failure_time`, and `half_open_attempts`.
- `wrap_service_call()` — attaches breakers to backend operations and mesh calls.

### States and transitions

- CLOSED: requests pass normally. Failures increment `failure_count`.
- OPEN: requests are blocked until `recovery_timeout` elapses.
- HALF_OPEN: a limited number of requests are allowed to verify recovery. If they succeed, the breaker closes; if any fail, it reopens.

### Integration points

- `MeshRouter` uses circuit breakers for `user-service` and `system-service` operations.
- `user_service` and `system_service` expose circuit-protected mesh variants.
- API endpoints under `/mesh/greet/{name}` and `/mesh/sysinfo` return clear error payloads when a circuit is open.
- CLI commands `circuit-status` and `circuit-test <service>` allow inspection and failure-mode testing.

### macOS considerations

- Timing uses `time.time()` and is appropriate for local CLI and FastAPI usage on macOS.
- Long-running processes should keep the event loop or thread alive while waiting for circuit recovery timeouts.
- For production-grade deployments on macOS, use a shared state backend when multiple processes need to coordinate breaker state.

