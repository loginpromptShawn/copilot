from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from ..metrics.exporters import fastapi_app as metrics_app
from ..tracing.exporters import router as traces_router
from ..tracing.tracer import global_tracer
from ..rate_limit.middleware import RateLimitMiddleware
from ..mesh.mesh_router import MeshRouter
from ..mesh.mesh_control_plane import global_mesh_control_plane
from ..auth.service import AuthService
from ..auth.middleware import AuthMiddleware, get_current_user
from ..persistence.repository import UserRepository, SystemInfoRepository
from ..circuit_breaker.integration import wrap_service_call
from ..core.errors import CircuitOpenError

app = FastAPI()

app.add_middleware(AuthMiddleware)

auth_service = AuthService()


class AuthRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str


class CurrentUserResponse(BaseModel):
    id: int
    username: str
    is_active: bool


class CreateUserRequest(BaseModel):
    name: str


class CreateSystemInfoRequest(BaseModel):
    os: str
    version: str


@app.post("/auth/register", response_model=CurrentUserResponse)
async def auth_register(payload: AuthRequest):
    try:
        user = auth_service.register_user(payload.username, payload.password)
        return CurrentUserResponse(id=user.id, username=user.username, is_active=user.is_active)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login", response_model=TokenResponse)
async def auth_login(payload: AuthRequest):
    try:
        session = auth_service.authenticate(payload.username, payload.password)
        return TokenResponse(token=session.token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/auth/me", response_model=CurrentUserResponse)
async def auth_me(user=Depends(get_current_user)):
    return CurrentUserResponse(id=user.id, username=user.username, is_active=user.is_active)


@app.get("/users", response_model=list[CurrentUserResponse])
async def list_users(user=Depends(get_current_user)):
    repo = UserRepository()
    users = repo.list_users()
    return [CurrentUserResponse(id=u.id, username=u.name, is_active=True) for u in users]


@app.post("/users", response_model=CurrentUserResponse)
async def create_user(payload: CreateUserRequest, user=Depends(get_current_user)):
    repo = UserRepository()
    created = repo.create_user(payload.name)
    return CurrentUserResponse(id=created.id, username=created.name, is_active=True)


@app.get("/system-info")
async def get_system_info_route(user=Depends(get_current_user)):
    repo = SystemInfoRepository()
    info = repo.get_latest_system_info()
    return {
        "os": info.os if info else None,
        "version": info.version if info else None,
        "id": info.id if info else None,
    }


@app.post("/system-info")
async def save_system_info(payload: CreateSystemInfoRequest, user=Depends(get_current_user)):
    repo = SystemInfoRepository()
    info = repo.save_system_info(payload.os, payload.version)
    return {"id": info.id, "os": info.os, "version": info.version}


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
