from fastapi import FastAPI, Request
from ..metrics.exporters import fastapi_app as metrics_app
from ..tracing.exporters import router as traces_router
from ..tracing.tracer import global_tracer
from ..rate_limit.middleware import RateLimitMiddleware
from ..mesh.mesh_router import MeshRouter
from ..mesh.mesh_control_plane import global_mesh_control_plane
from ..circuit_breaker.integration import wrap_service_call
from ..core.errors import CircuitOpenError

app = FastAPI()

# mount metrics endpoint app
app.mount("/metrics", metrics_app)

# include tracing routes if available
if traces_router is not None:
    app.include_router(traces_router)

# add rate limit middleware
app.add_middleware(RateLimitMiddleware)

@app.get("/mesh/greet/{name}")
async def mesh_greet(name: str):
    if global_mesh_control_plane is None:
        return {"error": "Mesh control plane unavailable"}
    router = MeshRouter()
    try:
        result = router.load_balanced_call("user-service", "greet_user", name)
        return {"result": result}
    except CircuitOpenError as exc:
        return {"error": str(exc), "state": "OPEN"}
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/mesh/sysinfo")
async def mesh_sysinfo():
    if global_mesh_control_plane is None:
        return {"error": "Mesh control plane unavailable"}
    router = MeshRouter()
    try:
        result = router.load_balanced_call("system-service", "get_system_info")
        return {"result": result}
    except CircuitOpenError as exc:
        return {"error": str(exc), "state": "OPEN"}
    except Exception as exc:
        return {"error": str(exc)}


@app.middleware("http")
async def trace_requests(request: Request, call_next):
    tracer = global_tracer
    span = None
    if tracer is not None:
        try:
            span = tracer.start_span(f"request:{request.method}:{request.url.path}")
        except Exception:
            pass
    try:
        response = await call_next(request)
        return response
    finally:
        if tracer is not None and span is not None:
            try:
                tracer.finish_span(span)
            except Exception:
                pass
