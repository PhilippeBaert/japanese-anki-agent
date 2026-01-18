"""Tests for API design improvements."""

import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
import re


# Set up environment variables BEFORE any imports that might need them
# This ensures the auth module can import without raising RuntimeError
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    with patch.dict(os.environ, {"REQUIRE_AUTH": "false", "API_KEY": ""}):
        yield


class TestExportEndpoints422:
    """Tests for export endpoints returning 422 for 'no cards to export'."""

    @pytest.mark.asyncio
    async def test_export_returns_422_for_empty_cards(self):
        """Export endpoint should return 422 when cards list is empty."""
        from app.routes.export import export_csv
        from app.models import ExportRequest

        # Create request with empty cards
        request = ExportRequest(cards=[], filename="test.csv")

        # The endpoint should raise HTTPException with 422
        with pytest.raises(HTTPException) as exc_info:
            await export_csv(request)

        assert exc_info.value.status_code == 422
        assert "No cards to export" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_export_priority_returns_422_for_empty_cards(self):
        """Export priority endpoint should return 422 when both card lists are empty."""
        from app.routes.export import export_csv_with_priority
        from app.models import ExportWithPriorityRequest

        # Create request with empty card lists
        request = ExportWithPriorityRequest(
            core_cards=[],
            extra_cards=[],
            filename="test.csv"
        )

        # The endpoint should raise HTTPException with 422
        with pytest.raises(HTTPException) as exc_info:
            await export_csv_with_priority(request)

        assert exc_info.value.status_code == 422
        assert "No cards to export" in exc_info.value.detail


class TestErrorMessagesSanitized:
    """Tests for error messages not exposing internal details."""

    @pytest.mark.asyncio
    async def test_export_error_message_is_generic(self):
        """Export endpoint should return generic error message on failure."""
        from app.routes.export import export_csv
        from app.models import ExportRequest, GeneratedCard, AnkiConfig

        # Create a request with valid cards but mock an internal failure
        request = ExportRequest(
            cards=[GeneratedCard(
                fields={"Hiragana/Katakana": "test"},
                tags=["test"],
                auto_classified_type="word"
            )],
            filename="test.csv"
        )

        # Mock load_config to return a valid config
        mock_config = AnkiConfig(fields=["Hiragana/Katakana"], tags=[])

        async def mock_load_config():
            return mock_config

        # Mock generate_csv to raise an internal error (this is inside the try block)
        def mock_generate_csv(*args, **kwargs):
            raise Exception("Internal database connection failed at line 42")

        with patch("app.routes.export.load_config", mock_load_config):
            with patch("app.routes.export.generate_csv", mock_generate_csv):
                with pytest.raises(HTTPException) as exc_info:
                    await export_csv(request)

                # Error message should be generic, not expose internal details
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "Export failed"
                # Should NOT contain internal error details
                assert "line 42" not in exc_info.value.detail
                assert "database" not in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_export_priority_error_message_is_generic(self):
        """Export priority endpoint should return generic error message on failure."""
        from app.routes.export import export_csv_with_priority
        from app.models import ExportWithPriorityRequest, GeneratedCard, AnkiConfig

        # Create a request with valid cards
        request = ExportWithPriorityRequest(
            core_cards=[GeneratedCard(
                fields={"Hiragana/Katakana": "test"},
                tags=["test"],
                auto_classified_type="word"
            )],
            extra_cards=[],
            filename="test.csv"
        )

        # Mock load_config to return a valid config
        mock_config = AnkiConfig(fields=["Hiragana/Katakana"], tags=[])

        async def mock_load_config():
            return mock_config

        # Mock generate_csv_with_priority to raise an internal error (this is inside the try block)
        def mock_generate_csv(*args, **kwargs):
            raise Exception("Stack trace at validator.py:123")

        with patch("app.routes.export.load_config", mock_load_config):
            with patch("app.routes.export.generate_csv_with_priority", mock_generate_csv):
                with pytest.raises(HTTPException) as exc_info:
                    await export_csv_with_priority(request)

                # Error message should be generic
                assert exc_info.value.status_code == 500
                assert exc_info.value.detail == "Export failed"
                # Should NOT contain stack trace info
                assert "validator.py" not in exc_info.value.detail
                assert ":123" not in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_migrate_preview_error_message_is_generic(self):
        """Migrate preview endpoint should return generic error on failure."""
        from app.routes.migrate import generate_migration_preview, PreviewRequest

        request = PreviewRequest(
            note_id=12345,
            raw_input="テスト"
        )

        # Mock dependencies to raise an internal error
        mock_config = MagicMock()
        mock_config.fields = ["test"]
        mock_config.tags = []

        async def mock_load_config():
            return mock_config

        async def mock_generate_cards_with_agent(*args, **kwargs):
            raise Exception("API key leaked: sk-123456")

        with patch("app.routes.migrate.load_config", mock_load_config):
            with patch("app.routes.migrate.generate_cards_with_agent", mock_generate_cards_with_agent):
                with pytest.raises(HTTPException) as exc_info:
                    await generate_migration_preview(request)

                # Error message should be generic
                assert exc_info.value.status_code == 500
                assert "Please try again" in exc_info.value.detail
                # Should NOT contain sensitive info
                assert "sk-" not in exc_info.value.detail
                assert "API key" not in exc_info.value.detail


class TestBatchPreviewStatusCodes:
    """Tests for batch preview returning appropriate status codes."""

    @pytest.mark.asyncio
    async def test_batch_preview_returns_200_on_all_success(self):
        """Batch preview should return 200 when all items succeed."""
        from app.routes.migrate import generate_batch_migration_preview, BatchPreviewRequest, BatchPreviewItem
        from app.models import GeneratedCard

        request = BatchPreviewRequest(
            items=[
                BatchPreviewItem(note_id=1, raw_input="テスト"),
                BatchPreviewItem(note_id=2, raw_input="テスト2"),
            ]
        )

        # Mock successful generation
        mock_cards = [
            GeneratedCard(
                fields={"Hiragana/Katakana": "テスト"},
                tags=[],
                auto_classified_type="word"
            ),
            GeneratedCard(
                fields={"Hiragana/Katakana": "テスト2"},
                tags=[],
                auto_classified_type="word"
            ),
        ]

        mock_config = MagicMock()
        mock_config.fields = ["Hiragana/Katakana"]
        mock_config.tags = []

        async def mock_load_config():
            return mock_config

        async def mock_generate_cards_with_agent(*args, **kwargs):
            return mock_cards

        with patch("app.routes.migrate.load_config", mock_load_config):
            with patch("app.routes.migrate.generate_cards_with_agent", mock_generate_cards_with_agent):
                response = await generate_batch_migration_preview(request)

                # Should return 200 status
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_batch_preview_returns_500_on_all_failure(self):
        """Batch preview should return 500 when all items fail."""
        from app.routes.migrate import generate_batch_migration_preview, BatchPreviewRequest, BatchPreviewItem
        from app.services.agent import CardGenerationError

        request = BatchPreviewRequest(
            items=[
                BatchPreviewItem(note_id=1, raw_input="テスト"),
            ]
        )

        mock_config = MagicMock()
        mock_config.fields = ["Hiragana/Katakana"]
        mock_config.tags = []

        async def mock_load_config():
            return mock_config

        async def mock_generate_cards_with_agent(*args, **kwargs):
            raise CardGenerationError("Generation failed")

        with patch("app.routes.migrate.load_config", mock_load_config):
            with patch("app.routes.migrate.generate_cards_with_agent", mock_generate_cards_with_agent):
                response = await generate_batch_migration_preview(request)

                # Should return 500 status
                assert response.status_code == 500


class TestDeckParameterValidation:
    """Tests for deck parameter validation in migrate endpoints."""

    def test_deck_name_pattern_regex(self):
        """Test that DECK_NAME_PATTERN rejects dangerous characters."""
        from app.routes.migrate import DECK_NAME_PATTERN

        pattern = re.compile(DECK_NAME_PATTERN)

        # Valid deck names should match
        assert pattern.match("My Deck")
        assert pattern.match("Japanese_Vocabulary")
        assert pattern.match("Deck-123")
        assert pattern.match("Parent::Child")  # Anki uses :: for subdecks
        assert pattern.match("Deck/Subdeck")  # Forward slash allowed
        assert pattern.match("Deck (2024)")
        assert pattern.match("It's my deck")
        assert pattern.match("Deck, v2")

        # Dangerous characters should NOT match
        assert not pattern.match("deck; DROP TABLE")
        assert not pattern.match("deck\" or 1=1")
        assert not pattern.match("deck<script>")
        assert not pattern.match("")  # Empty string should fail
        assert not pattern.match("deck`backtick")
        # Note: \s in regex includes newlines by default, so we don't test newline here
        # The min_length and max_length constraints handle other validation

    def test_deck_min_length_validation(self):
        """Deck name should have min_length=1."""
        from app.routes.migrate import get_notes_for_migration
        from annotated_types import MinLen
        import inspect

        # Get the function signature
        sig = inspect.signature(get_notes_for_migration)
        deck_param = sig.parameters["deck"]

        # The validation constraints are in the metadata list
        metadata = deck_param.default.metadata
        min_len_constraints = [m for m in metadata if isinstance(m, MinLen)]
        assert len(min_len_constraints) > 0, "Should have MinLen constraint"
        assert min_len_constraints[0].min_length == 1

    def test_deck_max_length_validation(self):
        """Deck name should have max_length=255."""
        from app.routes.migrate import get_notes_for_migration
        from annotated_types import MaxLen
        import inspect

        sig = inspect.signature(get_notes_for_migration)
        deck_param = sig.parameters["deck"]

        # The validation constraints are in the metadata list
        metadata = deck_param.default.metadata
        max_len_constraints = [m for m in metadata if isinstance(m, MaxLen)]
        assert len(max_len_constraints) > 0, "Should have MaxLen constraint"
        assert max_len_constraints[0].max_length == 255


class TestCheckConnectionRequiresAuth:
    """Tests for /check-connection endpoint requiring authentication."""

    def test_check_connection_has_auth_dependency(self):
        """check_anki_connection should have verify_api_key dependency."""
        from app.routes.migrate import router
        from app.auth import verify_api_key

        # Find the route for check-connection
        # Note: router has prefix="/migrate", so full path is /migrate/check-connection
        route = None
        for r in router.routes:
            if hasattr(r, 'path') and r.path == "/migrate/check-connection":
                route = r
                break

        assert route is not None, "/migrate/check-connection route not found"

        # Check that the route has dependencies
        assert route.dependencies is not None
        assert len(route.dependencies) > 0

        # Check that verify_api_key is one of the dependencies
        dep_callables = [d.dependency for d in route.dependencies]
        assert verify_api_key in dep_callables, "verify_api_key should be a dependency"

    @pytest.mark.asyncio
    async def test_check_connection_rejects_without_auth(self):
        """check_connection should reject requests without valid auth when auth is required."""
        from app.auth import verify_api_key

        # Test that verify_api_key raises 401 without a key
        with patch("app.auth.REQUIRE_AUTH", True), \
             patch("app.auth.API_KEY", "secret_key"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key(x_api_key=None)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_check_connection_accepts_valid_auth(self):
        """check_connection should accept requests with valid auth."""
        from app.auth import verify_api_key

        with patch("app.auth.REQUIRE_AUTH", True), \
             patch("app.auth.API_KEY", "secret_key"):
            result = await verify_api_key(x_api_key="secret_key")
            assert result == "secret_key"


class TestErrorCodesInRoutes:
    """Tests verifying correct HTTP status codes are used."""

    def test_export_uses_422_not_400_for_validation(self):
        """Ensure export.py uses 422 for validation errors, not 400."""
        import ast

        with open("app/routes/export.py", "r") as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content)

        # Find all HTTPException calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if hasattr(node, 'func'):
                    func = node.func
                    if hasattr(func, 'id') and func.id == 'HTTPException':
                        # Check status_code argument
                        for kw in node.keywords:
                            if kw.arg == 'detail':
                                if isinstance(kw.value, ast.Constant):
                                    if "No cards" in str(kw.value.value):
                                        # Find the corresponding status_code
                                        for kw2 in node.keywords:
                                            if kw2.arg == 'status_code':
                                                if isinstance(kw2.value, ast.Constant):
                                                    assert kw2.value.value == 422, \
                                                        f"'No cards to export' should use 422, not {kw2.value.value}"
