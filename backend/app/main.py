import logging
import os
import sys
import time
from collections import defaultdict
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging - use DEBUG level if DEBUG env var is set
debug_mode = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
log_level = logging.DEBUG if debug_mode else logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True  # Override any existing config
)

# Enable debug logging for Claude SDK when DEBUG is set
if debug_mode:
    logging.getLogger("claude_agent_sdk").setLevel(logging.DEBUG)
    print("DEBUG MODE ENABLED - verbose logging active", file=sys.stderr)

logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limiting Implementation
# =============================================================================

# Rate limit configuration (requests per minute)
RATE_LIMITS = {
    # Strict limits for Claude API endpoints to prevent abuse
    "/api/generate": 10,
    "/api/regenerate-card": 10,
    # More permissive limits for config and health endpoints
    "/api/config": 60,
    "/health": 60,
}
DEFAULT_RATE_LIMIT = 30  # Default for unlisted endpoints
RATE_WINDOW = 60  # Window in seconds (1 minute)

# In-memory storage for request timestamps per IP per endpoint
# Structure: {(client_ip, endpoint): [timestamp1, timestamp2, ...]}
request_timestamps: dict[tuple[str, str], list[float]] = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; first is the client
        return forwarded.split(",")[0].strip()
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


def get_rate_limit_for_path(path: str) -> int:
    """Get the rate limit for a given path."""
    # Check for exact match first
    if path in RATE_LIMITS:
        return RATE_LIMITS[path]
    # Check for prefix matches (e.g., /api/generate matches /api/generate/*)
    for endpoint, limit in RATE_LIMITS.items():
        if path.startswith(endpoint):
            return limit
    return DEFAULT_RATE_LIMIT


def check_rate_limit(client_ip: str, endpoint: str) -> tuple[bool, int, int]:
    """
    Check if a request is within rate limits.

    Returns:
        tuple: (allowed, remaining_requests, retry_after_seconds)
    """
    now = time.time()
    key = (client_ip, endpoint)
    limit = get_rate_limit_for_path(endpoint)

    # Get and clean up old timestamps
    timestamps = request_timestamps[key]
    timestamps[:] = [t for t in timestamps if now - t < RATE_WINDOW]

    remaining = max(0, limit - len(timestamps))

    if len(timestamps) >= limit:
        # Calculate retry-after (time until oldest timestamp expires)
        oldest = min(timestamps) if timestamps else now
        retry_after = int(RATE_WINDOW - (now - oldest)) + 1
        return False, 0, retry_after

    # Record this request
    timestamps.append(now)
    return True, remaining - 1, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on all requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = get_client_ip(request)
        path = request.url.path

        # Check rate limit
        allowed, remaining, retry_after = check_rate_limit(client_ip, path)

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {path}. "
                f"Retry after {retry_after}s"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(get_rate_limit_for_path(path)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Process the request
        response = await call_next(request)

        # Add rate limit headers to successful responses
        limit = get_rate_limit_for_path(path)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + RATE_WINDOW)

        return response


# =============================================================================
# Application Setup
# =============================================================================

app = FastAPI(
    title="Anki Agent API",
    description="API for generating Japanese Anki flashcards using Claude",
    version="0.1.0"
)

# CORS configuration for frontend at localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# Rate limiting middleware - applied after CORS to ensure proper handling
app.add_middleware(RateLimitMiddleware)

# Import and include routers
from .routes import config as config_router
from .routes import generate as generate_router
from .routes import export as export_router

app.include_router(config_router.router, prefix="/api", tags=["config"])
app.include_router(generate_router.router, prefix="/api", tags=["generate"])
app.include_router(export_router.router, prefix="/api", tags=["export"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
