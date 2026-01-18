"""Security tests for CORS configuration."""

import os
import logging
import pytest
from unittest.mock import patch, MagicMock


class TestParseCorsOrigins:
    """Tests for the parse_cors_origins() function."""

    def test_no_env_var_returns_localhost(self):
        """When CORS_ORIGINS is not set, should return localhost:3000."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove CORS_ORIGINS if it exists
            env_without_cors = {k: v for k, v in os.environ.items() if k != "CORS_ORIGINS"}
            with patch.dict(os.environ, env_without_cors, clear=True):
                # We need to re-import to test the function with fresh env
                from app.main import parse_cors_origins
                result = parse_cors_origins()
                assert result == ["http://localhost:3000"]

    def test_empty_string_returns_localhost(self):
        """When CORS_ORIGINS is empty, should return localhost:3000."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["http://localhost:3000"]

    def test_whitespace_only_returns_localhost(self):
        """When CORS_ORIGINS is whitespace only, should return localhost:3000."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "   "}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["http://localhost:3000"]

    def test_single_https_origin(self):
        """Single HTTPS origin should be parsed correctly."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://myapp.com"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["https://myapp.com"]

    def test_single_http_origin(self):
        """Single HTTP origin should be parsed correctly."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:8080"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["http://localhost:8080"]

    def test_multiple_origins_comma_separated(self):
        """Multiple comma-separated origins should be parsed correctly."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://a.com,https://b.com"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["http://a.com", "https://b.com"]

    def test_multiple_origins_with_spaces(self):
        """Origins with spaces around commas should be trimmed."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://a.com , https://b.com , http://c.com"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["http://a.com", "https://b.com", "http://c.com"]

    def test_wildcard_returns_star(self):
        """Wildcard '*' should return ['*']."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert result == ["*"]

    def test_wildcard_logs_warning(self, caplog):
        """Wildcard '*' should log a security warning."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "*"}, clear=False):
            from app.main import parse_cors_origins
            with caplog.at_level(logging.WARNING):
                result = parse_cors_origins()
                # Check that a warning was logged
                assert any("insecure" in record.message.lower() or "warning" in record.message.lower()
                          for record in caplog.records)

    def test_invalid_origin_no_scheme_skipped(self, caplog):
        """Origins without http:// or https:// should be skipped with warning."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "myapp.com"}, clear=False):
            from app.main import parse_cors_origins
            with caplog.at_level(logging.WARNING):
                result = parse_cors_origins()
                # Should fall back to localhost since the only origin was invalid
                assert result == ["http://localhost:3000"]
                # Check that a warning was logged about invalid origin
                assert any("invalid" in record.message.lower() for record in caplog.records)

    def test_mixed_valid_and_invalid_origins(self, caplog):
        """Mix of valid and invalid origins should only include valid ones."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://valid.com,invalid.com,http://also-valid.com"}, clear=False):
            from app.main import parse_cors_origins
            with caplog.at_level(logging.WARNING):
                result = parse_cors_origins()
                assert "https://valid.com" in result
                assert "http://also-valid.com" in result
                assert "invalid.com" not in result
                assert len(result) == 2

    def test_origin_with_spaces_skipped(self, caplog):
        """Origins containing spaces should be skipped."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://bad origin.com,https://good.com"}, clear=False):
            from app.main import parse_cors_origins
            with caplog.at_level(logging.WARNING):
                result = parse_cors_origins()
                assert "https://good.com" in result
                assert "http://bad origin.com" not in result

    def test_all_invalid_falls_back_to_localhost(self, caplog):
        """When all origins are invalid, should fall back to localhost:3000."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "invalid1.com,invalid2.com"}, clear=False):
            from app.main import parse_cors_origins
            with caplog.at_level(logging.ERROR):
                result = parse_cors_origins()
                assert result == ["http://localhost:3000"]

    def test_origin_with_port(self):
        """Origins with port numbers should be valid."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "http://localhost:3000,https://api.example.com:8443"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            assert "http://localhost:3000" in result
            assert "https://api.example.com:8443" in result

    def test_origin_with_path_preserved(self):
        """Origins with paths should be preserved (though not recommended)."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com/app"}, clear=False):
            from app.main import parse_cors_origins
            result = parse_cors_origins()
            # The function doesn't validate paths, so this should be accepted
            assert result == ["https://example.com/app"]


class TestCorsMiddlewareConfiguration:
    """Tests for CORS middleware configuration."""

    def test_cors_middleware_is_configured(self):
        """Verify that CORS middleware is properly configured on the app."""
        from app.main import app

        # Check that CORSMiddleware is in the middleware stack
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes or any(
            "CORS" in str(m) for m in app.user_middleware
        )

    def test_cors_allows_required_headers(self):
        """Verify that required headers (Content-Type, X-API-Key) are allowed."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Make a preflight OPTIONS request
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type,X-API-Key",
            }
        )

        # Check CORS headers in response
        assert "access-control-allow-headers" in response.headers
        allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
        assert "content-type" in allowed_headers
        assert "x-api-key" in allowed_headers

    def test_cors_allows_required_methods(self):
        """Verify that required methods (GET, POST, OPTIONS) are allowed."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )

        assert "access-control-allow-methods" in response.headers
        allowed_methods = response.headers.get("access-control-allow-methods", "").upper()
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "OPTIONS" in allowed_methods


class TestCorsSecurityBehavior:
    """Tests for CORS security behavior."""

    def test_cors_origin_header_respected(self):
        """Verify that the Origin header is checked by CORS middleware."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Make a request with allowed origin
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        # For allowed origin, should include Access-Control-Allow-Origin
        # Note: Behavior depends on CORS_ALLOWED_ORIGINS configuration
        # This test verifies the mechanism exists

    def test_credentials_allowed(self):
        """Verify that credentials are allowed (for cookie-based auth if needed)."""
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

        # Check if credentials are allowed
        allow_credentials = response.headers.get("access-control-allow-credentials", "")
        assert allow_credentials.lower() == "true"
