"""Security tests for the migration module - query injection prevention."""

import re
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Import the functions and constants we're testing
from app.routes.migrate import escape_anki_query_value, DECK_NAME_PATTERN


class TestEscapeAnkiQueryValue:
    """Tests for the escape_anki_query_value() function."""

    def test_escapes_double_quotes(self):
        """Input with quotes should have them escaped."""
        assert escape_anki_query_value('My "Test" Deck') == 'My \\"Test\\" Deck'

    def test_escapes_backslashes(self):
        """Input with backslashes should have them escaped."""
        assert escape_anki_query_value('Deck\\Name') == 'Deck\\\\Name'

    def test_escapes_both_quotes_and_backslashes(self):
        """Input with both quotes and backslashes should escape both."""
        # Backslashes are escaped first, then quotes
        # Input: Deck\"Name
        # After escaping backslashes: Deck\\"Name
        # After escaping quotes: Deck\\\\"Name
        assert escape_anki_query_value('Deck\\"Name') == 'Deck\\\\\\"Name'

    def test_preserves_normal_characters(self):
        """Normal characters should pass through unchanged."""
        assert escape_anki_query_value("Japanese Vocabulary") == "Japanese Vocabulary"
        assert escape_anki_query_value("Deck-2024") == "Deck-2024"
        assert escape_anki_query_value("Parent::Child") == "Parent::Child"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert escape_anki_query_value("") == ""

    def test_special_anki_operators_are_preserved(self):
        """Colons and other Anki operators in values should be preserved (they're only special at top level)."""
        assert escape_anki_query_value("deck:test") == "deck:test"
        assert escape_anki_query_value("note:Japanese") == "note:Japanese"

    def test_unicode_characters(self):
        """Unicode/Japanese characters should pass through unchanged."""
        assert escape_anki_query_value("日本語") == "日本語"
        assert escape_anki_query_value("漢字デッキ") == "漢字デッキ"

    def test_multiple_quotes(self):
        """Multiple quotes should all be escaped."""
        assert escape_anki_query_value('"A" and "B"') == '\\"A\\" and \\"B\\"'

    def test_multiple_backslashes(self):
        """Multiple backslashes should all be escaped."""
        assert escape_anki_query_value('a\\b\\c') == 'a\\\\b\\\\c'


class TestDeckNamePattern:
    """Tests for the DECK_NAME_PATTERN regex validation."""

    def test_valid_simple_names(self):
        """Simple alphanumeric names should be valid."""
        valid_names = [
            "Japanese",
            "Vocabulary",
            "Japanese Vocabulary",
            "Deck123",
        ]
        for name in valid_names:
            assert re.match(DECK_NAME_PATTERN, name), f"Should accept: {name}"

    def test_valid_with_punctuation(self):
        """Names with allowed punctuation should be valid."""
        valid_names = [
            "Deck-2024",
            "Deck_v2.0",
            "Japanese, Easy",
            "My Deck's Cards",
            "Deck (Main)",
        ]
        for name in valid_names:
            assert re.match(DECK_NAME_PATTERN, name), f"Should accept: {name}"

    def test_valid_hierarchical_names(self):
        """Anki hierarchical deck names with :: should be valid."""
        valid_names = [
            "Parent::Child",
            "Languages::Japanese::Vocabulary",
            "Main::Sub::SubSub",
        ]
        for name in valid_names:
            assert re.match(DECK_NAME_PATTERN, name), f"Should accept: {name}"

    def test_invalid_with_quotes(self):
        """Names with double quotes should be rejected (injection risk)."""
        assert not re.match(DECK_NAME_PATTERN, 'Deck"injection')
        assert not re.match(DECK_NAME_PATTERN, '"malicious"')
        assert not re.match(DECK_NAME_PATTERN, 'Test"Name')

    def test_invalid_with_backslash(self):
        """Names with backslashes should be rejected (injection risk)."""
        assert not re.match(DECK_NAME_PATTERN, 'Deck\\hack')
        assert not re.match(DECK_NAME_PATTERN, '\\escape')
        assert not re.match(DECK_NAME_PATTERN, 'path\\to\\deck')

    def test_invalid_with_wildcards(self):
        """Names with wildcards should be rejected."""
        assert not re.match(DECK_NAME_PATTERN, 'Deck*wildcard')
        assert not re.match(DECK_NAME_PATTERN, '*all')
        assert not re.match(DECK_NAME_PATTERN, 'test*')

    def test_invalid_with_other_special_chars(self):
        """Names with other dangerous special characters should be rejected."""
        invalid_chars = ['<', '>', '|', '`', '$', ';', '&', '!', '@', '#', '%', '^', '=', '+', '[', ']', '{', '}']
        for char in invalid_chars:
            name = f"Deck{char}Name"
            # Note: Some chars may be valid depending on the pattern, this tests the concept
            # The pattern allows: \w (alphanumeric + underscore), \s (whitespace), \-_.,'():/
            if char not in "-_.,'/():":
                assert not re.match(DECK_NAME_PATTERN, name), f"Should reject: {name}"

    def test_japanese_characters_valid(self):
        r"""Japanese deck names should be valid (unicode \\w includes them)."""
        valid_names = [
            "日本語",
            "漢字デッキ",
            "Japanese 日本語 Deck",
        ]
        for name in valid_names:
            assert re.match(DECK_NAME_PATTERN, name), f"Should accept: {name}"


class TestEndpointDeckNameValidation:
    """Tests for endpoint-level deck name validation."""

    def test_valid_deck_name_accepted(self):
        """Valid deck names should be accepted by the endpoint."""
        from app.main import app
        client = TestClient(app)

        # Mock the auth to allow requests through
        with patch("app.auth.verify_api_key", return_value="test_key"):
            # Mock the Anki client to avoid actual Anki connection
            with patch("app.routes.migrate.get_anki_client") as mock_client:
                mock_anki = AsyncMock()
                mock_anki.find_notes.return_value = []
                mock_client.return_value = mock_anki

                response = client.get(
                    "/api/migrate/notes",
                    params={"deck": "Japanese Vocabulary"},
                    headers={"X-API-Key": "test_key"}
                )
                # Should not be a 422 validation error
                assert response.status_code != 422

    def test_invalid_deck_name_with_quotes_rejected(self):
        """Deck names with quotes should be rejected with 422."""
        from app.main import app
        client = TestClient(app)

        response = client.get(
            "/api/migrate/notes",
            params={"deck": 'Deck"injection'},
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 422

    def test_invalid_deck_name_with_backslash_rejected(self):
        """Deck names with backslashes should be rejected with 422."""
        from app.main import app
        client = TestClient(app)

        response = client.get(
            "/api/migrate/notes",
            params={"deck": "Deck\\hack"},
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 422

    def test_invalid_deck_name_with_wildcard_rejected(self):
        """Deck names with wildcards should be rejected with 422."""
        from app.main import app
        client = TestClient(app)

        response = client.get(
            "/api/migrate/notes",
            params={"deck": "Deck*wildcard"},
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 422

    def test_empty_deck_name_rejected(self):
        """Empty deck names should be rejected."""
        from app.main import app
        client = TestClient(app)

        response = client.get(
            "/api/migrate/notes",
            params={"deck": ""},
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 422

    def test_deck_name_max_length_enforced(self):
        """Deck names exceeding max length should be rejected."""
        from app.main import app
        client = TestClient(app)

        # Create a deck name longer than 255 characters
        long_name = "A" * 256

        response = client.get(
            "/api/migrate/notes",
            params={"deck": long_name},
            headers={"X-API-Key": "test_key"}
        )
        assert response.status_code == 422


class TestQueryConstruction:
    """Tests to verify query construction is safe."""

    def test_query_uses_escaped_values(self):
        """Verify that the query construction properly uses escaped values."""
        deck_name = 'Test"Deck'
        escaped = escape_anki_query_value(deck_name)

        # The escaped value should be safe to use in a quoted query
        query = f'"deck:{escaped}"'

        # The query should contain escaped quotes, not raw quotes that would break the query
        assert '\\"' in query
        assert query == '"deck:Test\\"Deck"'

    def test_complex_injection_attempt_escaped(self):
        """Test that complex injection attempts are properly escaped."""
        # Attempt to break out of the quoted value and inject a new search term
        malicious_input = 'MyDeck" OR deck:*'
        escaped = escape_anki_query_value(malicious_input)

        # After escaping, the quotes should be escaped, preventing injection
        assert escaped == 'MyDeck\\" OR deck:*'

        query = f'"deck:{escaped}"'
        # The resulting query treats the entire thing as a literal deck name
        assert query == '"deck:MyDeck\\" OR deck:*"'
