from __future__ import annotations

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import rate_limiter as rl_module

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rl = rl_module.global_rate_limiter
        identifier = request.client.host if request.client else "anon"
        try:
            if rl is not None and not rl.allow_request(identifier):
                logger.info("Rate limit exceeded for %s", identifier)
                return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        except Exception:
            logger.exception("Error checking rate limit")
        return await call_next(request)
