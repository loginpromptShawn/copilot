from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from ..metrics.exporters import metrics_endpoint
from ..tracing.exporters import router as traces_router
from ..tracing import tracer as tracer_module
from ..rate_limit.middleware import RateLimitMiddleware
from ..mesh.mesh_router import MeshRouter
from ..mesh.mesh_control_plane import global_mesh_control_plane
from ..auth.middleware import AuthMiddleware, get_current_user
from ..auth.service import AuthService

auth_service = AuthService()
from ..persistence.repository import UserRepository, SystemInfoRepository
from ..core.errors import AuthError, CircuitOpenError

app = FastAPI()

app.add_middleware(AuthMiddleware)


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
    name: str = Field(min_length=1, max_length=100)


class CreateSystemInfoRequest(BaseModel):
    os: str = Field(min_length=1, max_length=50)
    version: str = Field(min_length=1, max_length=50)


@app.post("/auth/register", response_model=CurrentUserResponse)
async def auth_register(payload: AuthRequest):
    try:
        user = auth_service.register_user(payload.username, payload.password)
        return CurrentUserResponse(id=user.id, username=user.username, is_active=user.is_active)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login", response_model=TokenResponse)
async def auth_login(payload: AuthRequest):
    try:
        session = auth_service.authenticate(payload.username, payload.password)
        return TokenResponse(token=session.token)
    except AuthError:
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


# metrics endpoint
app.get("/metrics")(metrics_endpoint)

# include tracing routes if available
if traces_router is not None:
    app.include_router(traces_router)

# add rate limit middleware
app.add_middleware(RateLimitMiddleware)

class MeshResponse(BaseModel):
    result: str | None = None
    error: str | None = None
    state: str | None = None


@app.get("/mesh/greet/{name}", response_model=MeshResponse)
async def mesh_greet(name: str):
    if global_mesh_control_plane is None:
        return MeshResponse(error="Mesh control plane unavailable")
    router = MeshRouter()
    try:
        result = router.load_balanced_call("user-service", "greet_user", name)
        return MeshResponse(result=result)
    except CircuitOpenError as exc:
        return MeshResponse(error=str(exc), state="OPEN")
    except Exception as exc:
        return MeshResponse(error=str(exc))


@app.get("/mesh/sysinfo", response_model=MeshResponse)
async def mesh_sysinfo():
    if global_mesh_control_plane is None:
        return MeshResponse(error="Mesh control plane unavailable")
    router = MeshRouter()
    try:
        result = router.load_balanced_call("system-service", "get_system_info")
        return MeshResponse(result=result)
    except CircuitOpenError as exc:
        return MeshResponse(error=str(exc), state="OPEN")
    except Exception as exc:
        return MeshResponse(error=str(exc))


@app.middleware("http")
async def trace_requests(request: Request, call_next):
    tracer = tracer_module.global_tracer
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
