"""ASGI middleware — request rate limiting.

Throttles per API key (when presented) or per client IP, using the injected
:class:`RateLimiterPort`. Denied requests get ``429`` with ``Retry-After``;
allowed requests carry ``X-RateLimit-*`` headers. Keeps identity resolution
cheap (header/IP only) so it never touches the database on the hot path.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from bise.application.ports.rate_limiter import RateLimiterPort


def _identity(request: Request) -> str:
    """A stable throttle key: the API key if presented, else the client IP."""
    header = request.headers.get("authorization")
    if header and header.lower().startswith("bearer "):
        return f"key:{header[7:].strip()}"
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key:{api_key}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applies a token-bucket limit to every request except exempt paths."""

    def __init__(
        self,
        app: Callable[..., Awaitable[None]],
        limiter: RateLimiterPort,
        exempt_paths: frozenset[str] = frozenset(),
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._exempt = exempt_paths

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path in self._exempt:
            return await call_next(request)

        decision = self._limiter.hit(_identity(request))
        if not decision.allowed:
            retry_after = max(1, round(decision.retry_after))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(decision.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        return response
