"""
Custom middleware for request tracing and idempotency.
"""

import uuid
import json
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from app.config import settings


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique X-Request-Id header to every request/response."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    For POST/PUT/DELETE/PATCH requests with an Idempotency-Key header,
    cache the response in Redis. If the same key is seen again, return
    the cached response instead of re-processing.
    """

    IDEMPOTENT_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
    TTL_SECONDS = 86400  # 24 hours

    async def dispatch(self, request: Request, call_next):
        if request.method not in self.IDEMPOTENT_METHODS:
            return await call_next(request)

        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        # Build a composite key: method + path + idempotency key
        cache_key = f"prismid:idempotency:{hashlib.sha256(f'{request.method}:{request.url.path}:{idem_key}'.encode()).hexdigest()}"

        try:
            import redis
            r = redis.from_url(settings.REDIS_URL, decode_responses=True)
            cached = r.get(cache_key)
            if cached:
                data = json.loads(cached)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers={"X-Idempotent-Replay": "true"},
                )
        except Exception:
            # Redis unavailable — proceed without idempotency
            return await call_next(request)

        response = await call_next(request)

        # Only cache successful responses (2xx)
        if 200 <= response.status_code < 300:
            try:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk if isinstance(chunk, bytes) else chunk.encode()

                cache_data = json.dumps({
                    "status_code": response.status_code,
                    "body": json.loads(body.decode()),
                })
                r.setex(cache_key, self.TTL_SECONDS, cache_data)

                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception:
                pass

        return response
