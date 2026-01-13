"""API Key authentication module."""

import os
from fastapi import Header, HTTPException

# API Key authentication (optional - if not set, auth is disabled for development)
API_KEY = os.getenv("API_KEY")


async def verify_api_key(x_api_key: str = Header(None)):
    """
    Verify API key from X-API-Key header.
    If API_KEY env var is not set or empty, skip authentication (for local dev).
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
