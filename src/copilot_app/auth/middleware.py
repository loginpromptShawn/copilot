import logging
from typing import Optional

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .service import AuthService
from .models import AuthUser

logger = logging.getLogger(__name__)


def _extract_token(token: Optional[str], authorization: Optional[str]) -> Optional[str]:
    if authorization:
        if authorization.lower().startswith("bearer "):
            return authorization.split(" ", 1)[1].strip()
        return authorization.strip()
    return token


def get_current_user(
    request: Request,
    token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> AuthUser:
    # If AuthMiddleware already validated the token, reuse the cached user
    cached = getattr(request.state, "user", None)
    if cached is not None:
        return cached
    candidate = _extract_token(token, authorization)
    if not candidate:
        logger.debug("Missing auth token")
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = AuthService().validate_token(candidate)
    if user is None:
        logger.debug("Invalid auth token")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service: Optional[AuthService] = None):
        super().__init__(app)
        self.auth_service = auth_service or AuthService()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path.startswith("/auth") or request.url.path.startswith("/metrics") or request.method == "OPTIONS":
            return await call_next(request)

        token = _extract_token(request.headers.get("token"), request.headers.get("authorization"))
        if not token:
            logger.debug("AuthMiddleware blocked request without token: %s", request.url.path)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        user = self.auth_service.validate_token(token)
        if user is None:
            logger.debug("AuthMiddleware blocked invalid token: %s", token)
            return JSONResponse({"detail": "Unauthorized"}, status_code=401)

        request.state.user = user
        return await call_next(request)
