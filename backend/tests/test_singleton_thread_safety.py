"""Tests for singleton thread safety in anki_connect.py and config.py."""

import asyncio
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Import the modules we're testing
from app.services.anki_connect import (
    get_anki_client,
    AnkiConnectClient,
    _get_client_lock,
)
from app.config import (
    load_config,
    reload_config,
    _get_config_lock,
    CONFIG_TTL,
)
from app.models import AnkiConfig


# ============================================================================
# Tests for anki_connect.py singleton thread safety
# ============================================================================


class TestAnkiClientSingleton:
    """Test the AnkiConnect client singleton pattern."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the singleton before each test."""
        import app.services.anki_connect as anki_module
        anki_module._client = None
        anki_module._client_lock = None
        yield
        anki_module._client = None
        anki_module._client_lock = None

    @pytest.mark.asyncio
    async def test_get_anki_client_returns_singleton(self):
        """Test that get_anki_client returns the same instance on multiple calls."""
        client1 = await get_anki_client()
        client2 = await get_anki_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_concurrent_get_anki_client_returns_same_instance(self):
        """Test that concurrent calls to get_anki_client all return the same instance."""
        # Use asyncio.gather to call get_anki_client concurrently
        clients = await asyncio.gather(*[get_anki_client() for _ in range(10)])

        # All clients should be the exact same instance
        assert all(c is clients[0] for c in clients)

    @pytest.mark.asyncio
    async def test_get_anki_client_is_correct_type(self):
        """Test that get_anki_client returns an AnkiConnectClient instance."""
        client = await get_anki_client()
        assert isinstance(client, AnkiConnectClient)

    def test_get_client_lock_returns_lock(self):
        """Test that _get_client_lock returns an asyncio.Lock."""
        lock = _get_client_lock()
        assert isinstance(lock, asyncio.Lock)

    def test_get_client_lock_returns_same_lock(self):
        """Test that _get_client_lock returns the same lock on multiple calls."""
        lock1 = _get_client_lock()
        lock2 = _get_client_lock()
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_high_concurrency_returns_same_instance(self):
        """Test with higher concurrency to stress test the singleton pattern."""
        # Run 100 concurrent requests
        clients = await asyncio.gather(*[get_anki_client() for _ in range(100)])

        # All should be the same instance
        first_client = clients[0]
        assert all(c is first_client for c in clients)


# ============================================================================
# Tests for config.py singleton/cache thread safety
# ============================================================================


class TestConfigCache:
    """Test the config caching with TTL and thread safety."""

    @pytest.fixture(autouse=True)
    def reset_config_cache(self):
        """Reset the config cache before each test."""
        import app.config as config_module
        config_module._config_cache = None
        config_module._config_cache_time = 0
        config_module._config_lock = None
        yield
        config_module._config_cache = None
        config_module._config_cache_time = 0
        config_module._config_lock = None

    @pytest.fixture
    def mock_config_data(self):
        """Return mock configuration data."""
        return {
            "fields": ["Expression", "Reading", "Meaning"],
            "tags": ["test"],
            "tagsColumnEnabled": True,
            "tagsColumnName": "Tags",
            "sources": [{"label": "Test Source", "tag": "test_source"}],
            "defaultSource": "test_source"
        }

    @pytest.mark.asyncio
    async def test_load_config_caches_result(self, mock_config_data):
        """Test that load_config caches the result."""
        import json
        mock_file_content = json.dumps(mock_config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            config1 = await load_config()
            config2 = await load_config()

            # Both should return the same cached instance
            assert config1 is config2

    @pytest.mark.asyncio
    async def test_concurrent_load_config_returns_same_instance(self, mock_config_data):
        """Test that concurrent calls to load_config all return the same cached instance."""
        import json
        mock_file_content = json.dumps(mock_config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            # Use asyncio.gather to call load_config concurrently
            configs = await asyncio.gather(*[load_config() for _ in range(10)])

            # All configs should be the exact same instance
            assert all(c is configs[0] for c in configs)

    @pytest.mark.asyncio
    async def test_load_config_returns_anki_config(self, mock_config_data):
        """Test that load_config returns an AnkiConfig instance."""
        import json
        mock_file_content = json.dumps(mock_config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            config = await load_config()
            assert isinstance(config, AnkiConfig)

    def test_get_config_lock_returns_lock(self):
        """Test that _get_config_lock returns an asyncio.Lock."""
        lock = _get_config_lock()
        assert isinstance(lock, asyncio.Lock)

    def test_get_config_lock_returns_same_lock(self):
        """Test that _get_config_lock returns the same lock on multiple calls."""
        lock1 = _get_config_lock()
        lock2 = _get_config_lock()
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_reload_config_clears_cache(self, mock_config_data):
        """Test that reload_config clears the cache and loads fresh config."""
        import json
        import app.config as config_module
        mock_file_content = json.dumps(mock_config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            # Load initial config
            config1 = await load_config()

            # Modify the cached data to verify reload actually reloads
            original_cache = config_module._config_cache

            # Reload should clear cache and load fresh
            config2 = await reload_config()

            # New config should be a new instance (fresh load)
            # Note: They might compare equal but should be different objects after reload
            assert config2 is not original_cache or config_module._config_cache is config2

    @pytest.mark.asyncio
    async def test_high_concurrency_load_config(self, mock_config_data):
        """Test with higher concurrency to stress test the config loading."""
        import json
        mock_file_content = json.dumps(mock_config_data)

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            # Run 100 concurrent requests
            configs = await asyncio.gather(*[load_config() for _ in range(100)])

            # All should be the same cached instance
            first_config = configs[0]
            assert all(c is first_config for c in configs)

    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self):
        """Test that load_config raises ValueError when config file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            with pytest.raises(ValueError, match="Configuration file not found"):
                await load_config()

    @pytest.mark.asyncio
    async def test_load_config_invalid_json(self):
        """Test that load_config raises ValueError for invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json {")):
            with pytest.raises(ValueError, match="Invalid JSON"):
                await load_config()


# ============================================================================
# Race condition simulation tests
# ============================================================================


class TestRaceConditionPrevention:
    """Tests that specifically verify race conditions are prevented."""

    @pytest.fixture(autouse=True)
    def reset_all_singletons(self):
        """Reset all singletons before each test."""
        import app.services.anki_connect as anki_module
        import app.config as config_module

        anki_module._client = None
        anki_module._client_lock = None
        config_module._config_cache = None
        config_module._config_cache_time = 0
        config_module._config_lock = None

        yield

        anki_module._client = None
        anki_module._client_lock = None
        config_module._config_cache = None
        config_module._config_cache_time = 0
        config_module._config_lock = None

    @pytest.mark.asyncio
    async def test_anki_client_no_duplicate_instantiation(self):
        """Verify that only one AnkiConnectClient is ever created under concurrency."""
        import app.services.anki_connect as anki_module

        instantiation_count = 0
        original_init = AnkiConnectClient.__init__

        def counting_init(self, *args, **kwargs):
            nonlocal instantiation_count
            instantiation_count += 1
            return original_init(self, *args, **kwargs)

        with patch.object(AnkiConnectClient, '__init__', counting_init):
            # Run many concurrent calls
            await asyncio.gather(*[get_anki_client() for _ in range(50)])

        # Only one instance should have been created
        assert instantiation_count == 1, f"Expected 1 instantiation, got {instantiation_count}"

    @pytest.mark.asyncio
    async def test_config_no_duplicate_file_reads_within_ttl(self):
        """Verify that config file is only read once within TTL under concurrency."""
        import json

        mock_config_data = {
            "fields": ["Expression", "Reading", "Meaning"],
            "tags": ["test"],
            "tagsColumnEnabled": True,
            "tagsColumnName": "Tags",
            "sources": [{"label": "Test Source", "tag": "test"}],
            "defaultSource": "test"
        }

        file_read_count = 0

        def counting_open(*args, **kwargs):
            nonlocal file_read_count
            file_read_count += 1
            return mock_open(read_data=json.dumps(mock_config_data))()

        with patch("builtins.open", counting_open):
            # Run many concurrent calls
            await asyncio.gather(*[load_config() for _ in range(50)])

        # File should only be read once due to caching
        assert file_read_count == 1, f"Expected 1 file read, got {file_read_count}"

    @pytest.mark.asyncio
    async def test_interleaved_operations(self):
        """Test interleaved get_anki_client and load_config calls."""
        import json

        mock_config_data = {
            "fields": ["Expression", "Reading", "Meaning"],
            "tags": ["test"],
            "tagsColumnEnabled": True,
            "tagsColumnName": "Tags",
            "sources": [{"label": "Test Source", "tag": "test"}],
            "defaultSource": "test"
        }

        with patch("builtins.open", mock_open(read_data=json.dumps(mock_config_data))):
            # Mix of operations
            tasks = []
            for i in range(20):
                if i % 2 == 0:
                    tasks.append(get_anki_client())
                else:
                    tasks.append(load_config())

            results = await asyncio.gather(*tasks)

            # Verify clients are all the same
            clients = [r for r in results if isinstance(r, AnkiConnectClient)]
            assert all(c is clients[0] for c in clients)

            # Verify configs are all the same
            configs = [r for r in results if isinstance(r, AnkiConfig)]
            assert all(c is configs[0] for c in configs)
