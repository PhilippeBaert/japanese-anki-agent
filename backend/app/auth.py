"""API Key authentication module."""

import logging
import os

from fastapi import Header, HTTPException

logger = logging.getLogger(__name__)

# API Key authentication configuration
API_KEY = os.getenv("API_KEY")
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "true").lower() in ("true", "1", "yes")


def _validate_auth_config() -> None:
    """Validate authentication configuration at startup."""
    if REQUIRE_AUTH and not API_KEY:
        raise RuntimeError(
            "SECURITY ERROR: API_KEY environment variable is not set but REQUIRE_AUTH=True. "
            "Set API_KEY for production or set REQUIRE_AUTH=False for development mode."
        )
    if not REQUIRE_AUTH:
        logger.warning(
            "WARNING: Authentication is DISABLED (REQUIRE_AUTH=False). "
            "This should only be used in development environments!"
        )


# Validate configuration at module load time
_validate_auth_config()


async def verify_api_key(x_api_key: str = Header(None)):
    """
    Verify API key from X-API-Key header.

    Behavior:
    - If REQUIRE_AUTH=True (default) and API_KEY not set: raises RuntimeError at startup
    - If REQUIRE_AUTH=True and API_KEY set: validates the provided key
    - If REQUIRE_AUTH=False (dev mode): allows bypass but still validates if key provided
    """
    # If auth is required, API key must be provided and valid
    if REQUIRE_AUTH:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key required")
        if x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    else:
        # Dev mode: still validate if a key is provided and API_KEY is configured
        if x_api_key and API_KEY and x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key
