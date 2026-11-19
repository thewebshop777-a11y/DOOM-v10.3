"""
DOOM AI — Rate limiting middleware
Simple in-memory token bucket per IP.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 60, window: int = 60):
        super().__init__(app)
        self.calls = calls
        self.window = window
        self.buckets = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/"):
            ip = request.client.host if request.client else "unknown"
            now = time.time()
            bucket = self.buckets[ip]
            # Drop old timestamps
            self.buckets[ip] = [t for t in bucket if now - t < self.window]
            if len(self.buckets[ip]) >= self.calls:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again shortly."},
                )
            self.buckets[ip].append(now)
        return await call_next(request)
