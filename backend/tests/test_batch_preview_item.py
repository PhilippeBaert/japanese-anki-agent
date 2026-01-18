"""Tests for BatchPreviewItem model naming fixes.

These tests verify that the BatchPreviewItem model correctly handles both
camelCase (from frontend) and snake_case (internal use) field names.
"""

import pytest
from pydantic import ValidationError

from app.routes.migrate import BatchPreviewItem


class TestBatchPreviewItemCamelCase:
    """Test that model accepts camelCase field names from frontend."""

    def test_accepts_camelcase_required_fields(self):
        """Model should accept camelCase for required fields."""
        item = BatchPreviewItem(
            noteId=123,
            rawInput="test"
        )
        assert item.note_id == 123
        assert item.raw_input == "test"

    def test_accepts_camelcase_optional_fields(self):
        """Model should accept camelCase for optional fields."""
        item = BatchPreviewItem(
            noteId=123,
            rawInput="test",
            fixedEnglish="fixed english",
            fixedDutch="fixed dutch",
            extraNotes="extra notes",
            preserveSound="[sound:test.mp3]",
            preserveSoundExample="[sound:example.mp3]"
        )
        assert item.note_id == 123
        assert item.raw_input == "test"
        assert item.fixed_english == "fixed english"
        assert item.fixed_dutch == "fixed dutch"
        assert item.extra_notes == "extra notes"
        assert item.preserve_sound == "[sound:test.mp3]"
        assert item.preserve_sound_example == "[sound:example.mp3]"


class TestBatchPreviewItemSnakeCase:
    """Test that model accepts snake_case field names for internal use."""

    def test_accepts_snake_case_required_fields(self):
        """Model should accept snake_case for required fields."""
        item = BatchPreviewItem(
            note_id=123,
            raw_input="test"
        )
        assert item.note_id == 123
        assert item.raw_input == "test"

    def test_accepts_snake_case_optional_fields(self):
        """Model should accept snake_case for optional fields."""
        item = BatchPreviewItem(
            note_id=456,
            raw_input="hello",
            fixed_english="english",
            fixed_dutch="dutch",
            extra_notes="notes",
            preserve_sound="[sound:main.mp3]",
            preserve_sound_example="[sound:ex.mp3]"
        )
        assert item.note_id == 456
        assert item.raw_input == "hello"
        assert item.fixed_english == "english"
        assert item.fixed_dutch == "dutch"
        assert item.extra_notes == "notes"
        assert item.preserve_sound == "[sound:main.mp3]"
        assert item.preserve_sound_example == "[sound:ex.mp3]"


class TestBatchPreviewItemJsonParsing:
    """Test that model correctly parses JSON with camelCase keys."""

    def test_model_validate_camelcase_json(self):
        """model_validate should parse camelCase JSON correctly."""
        data = {
            "noteId": 456,
            "rawInput": "hello",
            "preserveSoundExample": "[sound:ex.mp3]"
        }
        item = BatchPreviewItem.model_validate(data)
        assert item.note_id == 456
        assert item.raw_input == "hello"
        assert item.preserve_sound_example == "[sound:ex.mp3]"

    def test_model_validate_all_camelcase_fields(self):
        """model_validate should parse all camelCase fields."""
        data = {
            "noteId": 789,
            "rawInput": "konnichiwa",
            "fixedEnglish": "hello",
            "fixedDutch": "hallo",
            "extraNotes": "greeting",
            "preserveSound": "[sound:greeting.mp3]",
            "preserveSoundExample": "[sound:greeting_ex.mp3]"
        }
        item = BatchPreviewItem.model_validate(data)
        assert item.note_id == 789
        assert item.raw_input == "konnichiwa"
        assert item.fixed_english == "hello"
        assert item.fixed_dutch == "hallo"
        assert item.extra_notes == "greeting"
        assert item.preserve_sound == "[sound:greeting.mp3]"
        assert item.preserve_sound_example == "[sound:greeting_ex.mp3]"

    def test_model_validate_snake_case_json(self):
        """model_validate should also accept snake_case JSON."""
        data = {
            "note_id": 999,
            "raw_input": "test",
            "preserve_sound": "[sound:test.mp3]"
        }
        item = BatchPreviewItem.model_validate(data)
        assert item.note_id == 999
        assert item.raw_input == "test"
        assert item.preserve_sound == "[sound:test.mp3]"


class TestBatchPreviewItemValidation:
    """Test that model validates required fields."""

    def test_requires_note_id(self):
        """Model should require note_id/noteId."""
        with pytest.raises(ValidationError):
            BatchPreviewItem(raw_input="test")

    def test_requires_raw_input(self):
        """Model should require raw_input/rawInput."""
        with pytest.raises(ValidationError):
            BatchPreviewItem(note_id=123)

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        item = BatchPreviewItem(note_id=1, raw_input="x")
        assert item.fixed_english is None
        assert item.fixed_dutch is None
        assert item.extra_notes is None
        assert item.preserve_sound is None
        assert item.preserve_sound_example is None
