"""Global rate limiting: 100 requests per minute per IP (configurable)."""

from collections import deque
from time import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

# In-memory: IP -> deque of request timestamps (last 60 seconds)
_rate: dict[str, deque[float]] = {}
_WINDOW_SECONDS = 60


def _get_client_ip(request: Request) -> str:
    """Prefer X-Forwarded-For when behind proxy (e.g. Nginx), else client.host."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests when IP exceeds rate_limit_per_minute_per_ip in a 60s window."""

    async def dispatch(self, request: Request, call_next):
        ip = _get_client_ip(request)
        now = time()
        if ip not in _rate:
            _rate[ip] = deque(maxlen=settings.rate_limit_per_minute_per_ip + 1)
        q = _rate[ip]
        # Drop timestamps outside window
        while q and q[0] < now - _WINDOW_SECONDS:
            q.popleft()
        if len(q) >= settings.rate_limit_per_minute_per_ip:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Try again later."},
                headers={"Retry-After": "60"},
            )
        q.append(now)
        return await call_next(request)
