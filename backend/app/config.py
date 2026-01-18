import asyncio
import json
import os
import time
from pathlib import Path
from .models import AnkiConfig

CONFIG_PATH = Path(os.getenv("CONFIG_PATH", Path(__file__).parent.parent.parent / "config" / "anki_config.json"))

# TTL-based cache configuration with thread-safe access
_config_cache = None
_config_cache_time = 0
_config_lock: asyncio.Lock | None = None
CONFIG_TTL = 300  # 5 minutes


def _get_config_lock() -> asyncio.Lock:
    """Get or create the config lock (lazy initialization for the lock itself)."""
    global _config_lock
    if _config_lock is None:
        _config_lock = asyncio.Lock()
    return _config_lock


async def load_config() -> AnkiConfig:
    """Load and cache the Anki configuration (thread-safe).

    Uses TTL-based caching (5 minutes by default). Config changes will be
    picked up automatically after the TTL expires, or call reload_config()
    to force an immediate reload.
    """
    global _config_cache, _config_cache_time
    now = time.time()

    # Fast path: cache is valid
    if _config_cache is not None and (now - _config_cache_time) <= CONFIG_TTL:
        return _config_cache

    async with _get_config_lock():
        # Double-check after acquiring lock
        now = time.time()
        if _config_cache is not None and (now - _config_cache_time) <= CONFIG_TTL:
            return _config_cache

        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise ValueError(f"Configuration file not found: {CONFIG_PATH}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        _config_cache = AnkiConfig(**data)
        _config_cache_time = now
        return _config_cache


async def reload_config() -> AnkiConfig:
    """Force reload the config (clears cache, thread-safe).

    Use this to immediately reload configuration without waiting for TTL expiry.
    """
    global _config_cache, _config_cache_time

    async with _get_config_lock():
        _config_cache = None
        _config_cache_time = 0

    return await load_config()
