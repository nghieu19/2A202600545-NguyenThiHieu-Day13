from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear contextvars to avoid leakage between requests
        clear_contextvars()

        # Extract x-request-id from headers or generate a new one
        # Use format: req-<8-char-hex>
        header_id = request.headers.get("x-request-id")
        if header_id:
            correlation_id = header_id
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        # Bind the correlation_id to structlog contextvars
        bind_contextvars(correlation_id=correlation_id)

        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Add the correlation_id and processing time to response headers
        try:
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(elapsed_ms)
        except Exception:
            # Some response types may not allow header mutation; ignore silently
            pass

        return response
