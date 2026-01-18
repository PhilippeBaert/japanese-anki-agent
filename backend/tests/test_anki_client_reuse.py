"""Tests for HTTP client reuse in anki_connect.py."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx


class TestHttpClientAttribute:
    """Test that _http_client attribute exists and is properly typed."""

    def test_http_client_attribute_exists(self):
        """Test that AnkiConnectClient has _http_client attribute."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()
        assert hasattr(client, '_http_client')
        assert client._http_client is None  # Should be None initially

    def test_http_client_is_optional_httpx_client(self):
        """Test that _http_client is typed as Optional[httpx.AsyncClient]."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()
        # Can be None or httpx.AsyncClient
        assert client._http_client is None


class TestGetHttpClient:
    """Test the _get_http_client method returns the same client."""

    @pytest.mark.asyncio
    async def test_get_http_client_returns_same_client_on_multiple_calls(self):
        """Test that _get_http_client returns the same client instance."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        try:
            # First call creates the client
            http_client1 = await client._get_http_client()
            assert http_client1 is not None
            assert isinstance(http_client1, httpx.AsyncClient)

            # Second call should return the same client
            http_client2 = await client._get_http_client()
            assert http_client2 is http_client1

            # Third call should also return the same client
            http_client3 = await client._get_http_client()
            assert http_client3 is http_client1

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_http_client_creates_client_with_timeout(self):
        """Test that created client has the correct timeout."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        try:
            http_client = await client._get_http_client()

            # Check that the client was created with a timeout
            assert http_client.timeout is not None
            # The timeout should be set to 30.0 (from self.timeout)
            assert http_client.timeout.read == 30.0

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_get_http_client_recreates_if_closed(self):
        """Test that _get_http_client creates new client if previous was closed."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        try:
            # Get initial client
            http_client1 = await client._get_http_client()
            assert http_client1 is not None

            # Close the client
            await client.close()
            assert client._http_client is None

            # Next call should create a new client
            http_client2 = await client._get_http_client()
            assert http_client2 is not None
            assert http_client2 is not http_client1

        finally:
            await client.close()


class TestCloseMethod:
    """Test the close() method for properly closing the client."""

    @pytest.mark.asyncio
    async def test_close_method_exists(self):
        """Test that close() method exists on AnkiConnectClient."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()
        assert hasattr(client, 'close')
        assert asyncio.iscoroutinefunction(client.close)

    @pytest.mark.asyncio
    async def test_close_properly_closes_client(self):
        """Test that close() properly closes the HTTP client."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        # Create the HTTP client
        http_client = await client._get_http_client()
        assert not http_client.is_closed

        # Close the client
        await client.close()

        # HTTP client should be closed
        assert http_client.is_closed
        # And _http_client should be set to None
        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_close_safe_to_call_multiple_times(self):
        """Test that close() can be called multiple times safely."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        # Create the HTTP client
        await client._get_http_client()

        # Close multiple times - should not raise
        await client.close()
        await client.close()
        await client.close()

        assert client._http_client is None

    @pytest.mark.asyncio
    async def test_close_safe_when_no_client_created(self):
        """Test that close() is safe to call when no client was created."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()
        assert client._http_client is None

        # Close when no client exists - should not raise
        await client.close()
        assert client._http_client is None


class TestSingletonPatternThreadSafety:
    """Test the singleton pattern for get_anki_client is thread-safe."""

    def test_client_lock_function_exists(self):
        """Test that _get_client_lock function exists."""
        from app.services.anki_connect import _get_client_lock

        assert callable(_get_client_lock)

    def test_get_client_lock_returns_lock(self):
        """Test that _get_client_lock returns an asyncio.Lock."""
        from app.services.anki_connect import _get_client_lock

        lock = _get_client_lock()
        assert isinstance(lock, asyncio.Lock)

    def test_get_client_lock_returns_same_lock(self):
        """Test that _get_client_lock returns the same lock on multiple calls."""
        from app.services.anki_connect import _get_client_lock

        lock1 = _get_client_lock()
        lock2 = _get_client_lock()
        assert lock1 is lock2

    @pytest.mark.asyncio
    async def test_get_anki_client_returns_same_instance(self):
        """Test that get_anki_client returns the same singleton instance."""
        from app.services.anki_connect import get_anki_client
        import app.services.anki_connect as module

        # Save original client
        original_client = module._client

        try:
            # Reset the singleton
            module._client = None

            # Get client multiple times
            client1 = await get_anki_client()
            client2 = await get_anki_client()
            client3 = await get_anki_client()

            # All should be the same instance
            assert client1 is client2
            assert client2 is client3

        finally:
            # Restore original state
            module._client = original_client

    @pytest.mark.asyncio
    async def test_concurrent_get_anki_client_returns_same_instance(self):
        """Test that concurrent calls to get_anki_client return the same instance."""
        from app.services.anki_connect import get_anki_client
        import app.services.anki_connect as module

        # Save original state
        original_client = module._client

        try:
            # Reset the singleton
            module._client = None

            # Make concurrent calls
            clients = await asyncio.gather(
                get_anki_client(),
                get_anki_client(),
                get_anki_client(),
                get_anki_client(),
                get_anki_client(),
            )

            # All should be the same instance
            first_client = clients[0]
            for client in clients[1:]:
                assert client is first_client

        finally:
            # Restore original state
            module._client = original_client


class TestInvokeUsesSharedClient:
    """Test that _invoke uses the shared HTTP client."""

    @pytest.mark.asyncio
    async def test_invoke_uses_get_http_client(self):
        """Test that _invoke gets the client via _get_http_client."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        # Mock the _get_http_client to track calls
        original_get = client._get_http_client
        call_count = [0]

        async def tracked_get():
            call_count[0] += 1
            return await original_get()

        client._get_http_client = tracked_get

        try:
            # Mock the HTTP response
            with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"result": "test", "error": None}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                # Make multiple invoke calls
                await client._invoke("test_action")
                await client._invoke("test_action2")

                # _get_http_client should have been called for each invoke
                assert call_count[0] == 2

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_multiple_invokes_reuse_same_client(self):
        """Test that multiple _invoke calls reuse the same HTTP client."""
        from app.services.anki_connect import AnkiConnectClient

        client = AnkiConnectClient()

        try:
            # Mock the HTTP response
            with patch.object(httpx.AsyncClient, 'post', new_callable=AsyncMock) as mock_post:
                mock_response = MagicMock()
                mock_response.json.return_value = {"result": "test", "error": None}
                mock_response.raise_for_status = MagicMock()
                mock_post.return_value = mock_response

                # Get client before invokes
                http_client_before = await client._get_http_client()

                # Make multiple invoke calls
                await client._invoke("test_action1")
                await client._invoke("test_action2")
                await client._invoke("test_action3")

                # Get client after invokes
                http_client_after = await client._get_http_client()

                # Should be the same client instance
                assert http_client_before is http_client_after

        finally:
            await client.close()
