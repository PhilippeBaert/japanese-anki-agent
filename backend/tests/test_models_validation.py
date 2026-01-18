"""Tests for Pydantic model validation fixes.

These tests verify that the GeneratedCard model correctly validates
the fields dict size limit.
"""

import pytest
from pydantic import ValidationError

from app.models import GeneratedCard, CardType


class TestGeneratedCardFieldsValidation:
    """Test validation of the fields dict in GeneratedCard."""

    def test_valid_fields_dict_small(self):
        """A small fields dict should be valid."""
        card = GeneratedCard(
            fields={"Kana": "test", "English": "test"},
            tags=["tag1"],
            auto_classified_type="word"
        )
        assert len(card.fields) == 2
        assert card.fields["Kana"] == "test"
        assert card.fields["English"] == "test"

    def test_valid_fields_dict_typical(self):
        """A typical fields dict with all standard fields should be valid."""
        card = GeneratedCard(
            fields={
                "Hiragana/Katakana": "こんにちは",
                "Romaji": "konnichiwa",
                "Kanji": "今日は",
                "English": "hello",
                "Dutch": "hallo",
                "Example sentence hiragana/katakana": "こんにちは、げんきですか？",
                "Example sentence kanji": "今日は、元気ですか？",
                "Example sentence translation": "Hello, how are you?",
                "Extra notes": "Common greeting",
                "Sound": "[sound:konnichiwa.mp3]",
                "Sound example": "[sound:konnichiwa_ex.mp3]",
            },
            tags=["japanese", "greeting"],
            auto_classified_type="phrase"
        )
        assert len(card.fields) == 11

    def test_invalid_fields_dict_over_50_entries(self):
        """A fields dict with more than 50 entries should be invalid."""
        with pytest.raises(ValidationError) as exc_info:
            GeneratedCard(
                fields={f"field_{i}": "value" for i in range(51)},
                tags=[],
                auto_classified_type="word"
            )
        # Verify the error message mentions the limit
        assert "50" in str(exc_info.value)

    def test_boundary_exactly_50_entries_valid(self):
        """A fields dict with exactly 50 entries should be valid (boundary)."""
        card = GeneratedCard(
            fields={f"field_{i}": "value" for i in range(50)},
            tags=[],
            auto_classified_type="word"
        )
        assert len(card.fields) == 50

    def test_boundary_49_entries_valid(self):
        """A fields dict with 49 entries should be valid."""
        card = GeneratedCard(
            fields={f"field_{i}": "value" for i in range(49)},
            tags=[],
            auto_classified_type="sentence"
        )
        assert len(card.fields) == 49


class TestGeneratedCardAutoClassifiedType:
    """Test auto_classified_type field validation."""

    def test_valid_type_word(self):
        """auto_classified_type 'word' should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=[],
            auto_classified_type="word"
        )
        assert card.auto_classified_type == "word"

    def test_valid_type_phrase(self):
        """auto_classified_type 'phrase' should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=[],
            auto_classified_type="phrase"
        )
        assert card.auto_classified_type == "phrase"

    def test_valid_type_sentence(self):
        """auto_classified_type 'sentence' should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=[],
            auto_classified_type="sentence"
        )
        assert card.auto_classified_type == "sentence"

    def test_invalid_type_raises_error(self):
        """Invalid auto_classified_type should raise ValidationError."""
        with pytest.raises(ValidationError):
            GeneratedCard(
                fields={"test": "value"},
                tags=[],
                auto_classified_type="invalid_type"  # type: ignore
            )


class TestGeneratedCardTags:
    """Test tags field validation."""

    def test_empty_tags_valid(self):
        """Empty tags list should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=[],
            auto_classified_type="word"
        )
        assert card.tags == []

    def test_single_tag_valid(self):
        """Single tag should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=["japanese"],
            auto_classified_type="word"
        )
        assert card.tags == ["japanese"]

    def test_multiple_tags_valid(self):
        """Multiple tags should be valid."""
        card = GeneratedCard(
            fields={"test": "value"},
            tags=["japanese", "vocabulary", "N5"],
            auto_classified_type="word"
        )
        assert len(card.tags) == 3


class TestGeneratedCardEmptyFields:
    """Test edge cases with fields dict."""

    def test_empty_fields_dict_valid(self):
        """Empty fields dict should be valid (no minimum enforced)."""
        card = GeneratedCard(
            fields={},
            tags=[],
            auto_classified_type="word"
        )
        assert len(card.fields) == 0

    def test_fields_with_empty_values_valid(self):
        """Fields with empty string values should be valid."""
        card = GeneratedCard(
            fields={"Kana": "", "English": ""},
            tags=[],
            auto_classified_type="word"
        )
        assert card.fields["Kana"] == ""
        assert card.fields["English"] == ""
