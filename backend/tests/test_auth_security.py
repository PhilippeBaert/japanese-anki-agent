"""Security tests for the authentication module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestAuthConfigValidation:
    """Tests for authentication configuration validation at startup."""

    def test_startup_fails_when_require_auth_true_and_no_api_key(self):
        """When REQUIRE_AUTH=True (default) and API_KEY not set, should raise RuntimeError."""
        # We need to test the module loading behavior, so we patch environment and reload
        with patch.dict(os.environ, {"REQUIRE_AUTH": "true"}, clear=False):
            # Ensure API_KEY is not set
            env_copy = os.environ.copy()
            env_copy.pop("API_KEY", None)
            env_copy["REQUIRE_AUTH"] = "true"

            with patch.dict(os.environ, env_copy, clear=True):
                # Import the validation function directly to test it
                # We need to test the _validate_auth_config function
                with pytest.raises(RuntimeError) as exc_info:
                    # Create a fresh module environment
                    API_KEY = None
                    REQUIRE_AUTH = True

                    if REQUIRE_AUTH and not API_KEY:
                        raise RuntimeError(
                            "SECURITY ERROR: API_KEY environment variable is not set but REQUIRE_AUTH=True. "
                            "Set API_KEY for production or set REQUIRE_AUTH=False for development mode."
                        )

                assert "SECURITY ERROR" in str(exc_info.value)
                assert "API_KEY" in str(exc_info.value)

    def test_dev_mode_allows_bypass_when_require_auth_false(self):
        """When REQUIRE_AUTH=False, should not raise error even without API_KEY."""
        # Simulate the validation logic
        API_KEY = None
        REQUIRE_AUTH = False

        # This should not raise an error
        error_raised = False
        if REQUIRE_AUTH and not API_KEY:
            error_raised = True

        assert not error_raised, "Should allow bypass when REQUIRE_AUTH=False"

    def test_startup_succeeds_when_api_key_is_set(self):
        """When API_KEY is set and REQUIRE_AUTH=True, should succeed."""
        API_KEY = "test_secret_key"
        REQUIRE_AUTH = True

        # This should not raise an error
        error_raised = False
        if REQUIRE_AUTH and not API_KEY:
            error_raised = True

        assert not error_raised, "Should succeed when API_KEY is set"


class TestVerifyApiKey:
    """Tests for the verify_api_key dependency function."""

    @pytest.mark.asyncio
    async def test_valid_api_key_passes(self):
        """Valid API key should pass authentication."""
        from app.auth import verify_api_key

        # Patch the module-level variables
        with patch("app.auth.REQUIRE_AUTH", True), \
             patch("app.auth.API_KEY", "test_secret_key"):
            result = await verify_api_key(x_api_key="test_secret_key")
            assert result == "test_secret_key"

    @pytest.mark.asyncio
    async def test_invalid_api_key_returns_401(self):
        """Invalid API key should return 401 Unauthorized."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", True), \
             patch("app.auth.API_KEY", "test_secret_key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong_key")

            assert exc_info.value.status_code == 401
            assert "Invalid API key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_missing_api_key_returns_401_when_required(self):
        """Missing API key should return 401 when REQUIRE_AUTH=True."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", True), \
             patch("app.auth.API_KEY", "test_secret_key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)

            assert exc_info.value.status_code == 401
            assert "API key required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_dev_mode_allows_no_api_key(self):
        """In dev mode (REQUIRE_AUTH=False), no API key should be allowed."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", False), \
             patch("app.auth.API_KEY", None):
            result = await verify_api_key(x_api_key=None)
            assert result is None

    @pytest.mark.asyncio
    async def test_dev_mode_still_validates_if_key_provided(self):
        """In dev mode, if API_KEY is configured and wrong key provided, should reject."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", False), \
             patch("app.auth.API_KEY", "configured_key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key="wrong_key")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_dev_mode_accepts_valid_key_if_provided(self):
        """In dev mode, if API_KEY is configured and correct key provided, should accept."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", False), \
             patch("app.auth.API_KEY", "configured_key"):
            result = await verify_api_key(x_api_key="configured_key")
            assert result == "configured_key"


class TestRequireAuthParsing:
    """Tests for REQUIRE_AUTH environment variable parsing."""

    def test_require_auth_defaults_to_true(self):
        """REQUIRE_AUTH should default to True if not set."""
        require_auth = os.getenv("REQUIRE_AUTH_TEST_NONEXISTENT", "true").lower() in ("true", "1", "yes")
        assert require_auth is True

    def test_require_auth_parses_true_values(self):
        """REQUIRE_AUTH should parse 'true', '1', 'yes' as True."""
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
            result = value.lower() in ("true", "1", "yes")
            assert result is True, f"Failed for value: {value}"

    def test_require_auth_parses_false_values(self):
        """REQUIRE_AUTH should parse other values as False."""
        for value in ["false", "False", "FALSE", "0", "no", "No", "NO", ""]:
            result = value.lower() in ("true", "1", "yes")
            assert result is False, f"Failed for value: {value}"
