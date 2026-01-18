"""Tests for type and validation improvements."""

import pytest
import json
from pydantic import ValidationError


class TestKanaOnlyFieldsConstant:
    """Tests for KANA_ONLY_FIELDS constant in validator.py."""

    def test_kana_only_fields_constant_exists(self):
        """KANA_ONLY_FIELDS constant should exist in validator module."""
        from app.services.validator import KANA_ONLY_FIELDS

        assert KANA_ONLY_FIELDS is not None
        assert isinstance(KANA_ONLY_FIELDS, list)

    def test_kana_only_fields_contains_expected_fields(self):
        """KANA_ONLY_FIELDS should contain the expected field names."""
        from app.services.validator import KANA_ONLY_FIELDS

        assert 'Hiragana/Katakana' in KANA_ONLY_FIELDS
        assert 'Example sentence hiragana/katakana' in KANA_ONLY_FIELDS

    def test_kana_only_fields_is_used_in_validation(self):
        """KANA_ONLY_FIELDS should be used by validate_card function."""
        from app.services.validator import validate_card, KANA_ONLY_FIELDS

        # Create a card with kanji in a kana-only field
        card = {
            "fields": {
                "Hiragana/Katakana": "日本語",  # Contains kanji - should fail
                "Romaji": "nihongo",
                "Kanji": "日本語",
                "English": "Japanese language",
                "Dutch": "Japans",
                "Example sentence hiragana/katakana": "",
                "Example sentence kanji": "",
                "Example sentence translation": "",
            },
            "tags": ["test"],
        }

        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)

        # Should have an error about kanji in kana-only field
        assert any("kanji" in e.lower() for e in errors)
        assert any("Hiragana/Katakana" in e for e in errors)


class TestRequiredNonEmptyFieldsConstant:
    """Tests for REQUIRED_NON_EMPTY_FIELDS validation."""

    def test_required_non_empty_fields_constant_exists(self):
        """REQUIRED_NON_EMPTY_FIELDS constant should exist in validator module."""
        from app.services.validator import REQUIRED_NON_EMPTY_FIELDS

        assert REQUIRED_NON_EMPTY_FIELDS is not None
        assert isinstance(REQUIRED_NON_EMPTY_FIELDS, list)

    def test_required_non_empty_fields_contains_expected_fields(self):
        """REQUIRED_NON_EMPTY_FIELDS should contain core identification fields."""
        from app.services.validator import REQUIRED_NON_EMPTY_FIELDS

        assert 'Hiragana/Katakana' in REQUIRED_NON_EMPTY_FIELDS
        assert 'English' in REQUIRED_NON_EMPTY_FIELDS
        assert 'Dutch' in REQUIRED_NON_EMPTY_FIELDS

    def test_empty_required_field_fails_validation(self):
        """Empty required fields should fail validation."""
        from app.services.validator import validate_card

        # Create a card with empty English field
        card = {
            "fields": {
                "Hiragana/Katakana": "にほんご",
                "Romaji": "nihongo",
                "Kanji": "日本語",
                "English": "",  # Empty - should fail
                "Dutch": "Japans",
                "Example sentence hiragana/katakana": "",
                "Example sentence kanji": "",
                "Example sentence translation": "",
            },
            "tags": ["test"],
        }

        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)

        # Should have an error about empty required field
        assert any("empty" in e.lower() or "whitespace" in e.lower() for e in errors)
        assert any("English" in e for e in errors)

    def test_whitespace_only_required_field_fails_validation(self):
        """Whitespace-only required fields should fail validation."""
        from app.services.validator import validate_card

        # Create a card with whitespace-only Dutch field
        card = {
            "fields": {
                "Hiragana/Katakana": "にほんご",
                "Romaji": "nihongo",
                "Kanji": "日本語",
                "English": "Japanese language",
                "Dutch": "   ",  # Whitespace only - should fail
                "Example sentence hiragana/katakana": "",
                "Example sentence kanji": "",
                "Example sentence translation": "",
            },
            "tags": ["test"],
        }

        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)

        # Should have an error about whitespace-only required field
        assert any("empty" in e.lower() or "whitespace" in e.lower() for e in errors)
        assert any("Dutch" in e for e in errors)

    def test_valid_required_fields_pass_validation(self):
        """Valid non-empty required fields should pass validation."""
        from app.services.validator import validate_card

        card = {
            "fields": {
                "Hiragana/Katakana": "にほんご",
                "Romaji": "nihongo",
                "Kanji": "日本語",
                "English": "Japanese language",
                "Dutch": "Japans",
                "Example sentence hiragana/katakana": "",
                "Example sentence kanji": "",
                "Example sentence translation": "",
            },
            "tags": ["test"],
        }

        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)

        # Should not have errors about empty required fields
        assert not any("empty" in e.lower() and "Required" in e for e in errors)


class TestAnkiConfigSnakeCase:
    """Tests for AnkiConfig using snake_case internally with camelCase aliases."""

    def test_anki_config_uses_snake_case_attributes(self):
        """AnkiConfig should use snake_case for Python attribute names."""
        from app.models import AnkiConfig

        # Create an instance with snake_case
        config = AnkiConfig(
            fields=["test"],
            tags=["tag1"],
            tags_column_enabled=True,
            tags_column_name="Tags",
            sources=[],
            default_source=None
        )

        # Should be able to access via snake_case
        assert hasattr(config, 'tags_column_enabled')
        assert hasattr(config, 'tags_column_name')
        assert hasattr(config, 'default_source')

        # Verify values
        assert config.tags_column_enabled == True
        assert config.tags_column_name == "Tags"

    def test_anki_config_accepts_camel_case_json(self):
        """AnkiConfig should accept camelCase when parsing JSON."""
        from app.models import AnkiConfig

        # JSON payload with camelCase keys (as would come from frontend)
        json_data = {
            "fields": ["field1", "field2"],
            "tags": ["tag1"],
            "tagsColumnEnabled": False,
            "tagsColumnName": "CustomTags",
            "sources": [],
            "defaultSource": "web"
        }

        # Should parse without error
        config = AnkiConfig(**json_data)

        # Values should be accessible via snake_case
        assert config.tags_column_enabled == False
        assert config.tags_column_name == "CustomTags"
        assert config.default_source == "web"

    def test_anki_config_serializes_to_camel_case(self):
        """AnkiConfig should serialize to camelCase for API responses."""
        from app.models import AnkiConfig

        config = AnkiConfig(
            fields=["test"],
            tags=["tag1"],
            tags_column_enabled=True,
            tags_column_name="Tags",
            sources=[],
            default_source="podcast"
        )

        # Serialize to dict (for JSON response)
        serialized = config.model_dump(by_alias=True)

        # Should use camelCase keys
        assert "tagsColumnEnabled" in serialized
        assert "tagsColumnName" in serialized
        assert "defaultSource" in serialized

        # Should NOT have snake_case keys in serialized output
        assert "tags_column_enabled" not in serialized
        assert "tags_column_name" not in serialized
        assert "default_source" not in serialized

        # Values should be correct
        assert serialized["tagsColumnEnabled"] == True
        assert serialized["tagsColumnName"] == "Tags"
        assert serialized["defaultSource"] == "podcast"

    def test_anki_config_model_config_settings(self):
        """AnkiConfig should have correct model_config settings."""
        from app.models import AnkiConfig

        # Check model_config
        assert hasattr(AnkiConfig, 'model_config')
        model_config = AnkiConfig.model_config

        # Should have populate_by_name=True for accepting both alias and field name
        assert model_config.get('populate_by_name') == True

        # Should have serialize_by_alias=True for outputting aliases
        assert model_config.get('serialize_by_alias') == True

    def test_anki_config_field_aliases(self):
        """AnkiConfig fields should have correct aliases defined."""
        from app.models import AnkiConfig

        # Get field info
        fields_info = AnkiConfig.model_fields

        # Check aliases
        assert fields_info['tags_column_enabled'].alias == 'tagsColumnEnabled'
        assert fields_info['tags_column_name'].alias == 'tagsColumnName'
        assert fields_info['default_source'].alias == 'defaultSource'


class TestExportWithPriorityRequestType:
    """Tests for ExportWithPriorityRequest type."""

    def test_export_with_priority_request_exists(self):
        """ExportWithPriorityRequest should exist in models."""
        from app.models import ExportWithPriorityRequest

        assert ExportWithPriorityRequest is not None

    def test_export_with_priority_request_has_required_fields(self):
        """ExportWithPriorityRequest should have core_cards, extra_cards, filename, source."""
        from app.models import ExportWithPriorityRequest

        fields = ExportWithPriorityRequest.model_fields

        assert 'core_cards' in fields
        assert 'extra_cards' in fields
        assert 'filename' in fields
        assert 'source' in fields

    def test_export_with_priority_request_accepts_valid_data(self):
        """ExportWithPriorityRequest should accept valid data."""
        from app.models import ExportWithPriorityRequest, GeneratedCard

        card = GeneratedCard(
            fields={"Hiragana/Katakana": "test"},
            tags=["test"],
            auto_classified_type="word"
        )

        request = ExportWithPriorityRequest(
            core_cards=[card],
            extra_cards=[],
            filename="test.csv",
            source="web"
        )

        assert len(request.core_cards) == 1
        assert len(request.extra_cards) == 0
        assert request.filename == "test.csv"
        assert request.source == "web"

    def test_export_with_priority_request_allows_both_lists_empty(self):
        """ExportWithPriorityRequest should allow both card lists to be empty (validation happens in endpoint)."""
        from app.models import ExportWithPriorityRequest

        request = ExportWithPriorityRequest(
            core_cards=[],
            extra_cards=[],
            filename="test.csv"
        )

        assert len(request.core_cards) == 0
        assert len(request.extra_cards) == 0

    def test_export_with_priority_request_validates_max_length(self):
        """ExportWithPriorityRequest should validate max_length constraints."""
        from app.models import ExportWithPriorityRequest, GeneratedCard

        card = GeneratedCard(
            fields={"Hiragana/Katakana": "test"},
            tags=["test"],
            auto_classified_type="word"
        )

        # Create more than 1000 cards (max_length)
        too_many_cards = [card] * 1001

        with pytest.raises(ValidationError):
            ExportWithPriorityRequest(
                core_cards=too_many_cards,
                extra_cards=[],
                filename="test.csv"
            )


class TestDraftCardIdJsDoc:
    """Tests for DraftCard id field documentation (frontend TypeScript)."""

    def test_draft_card_id_documentation_in_types(self):
        """DraftCard in types/index.ts should have JSDoc for id field."""
        # Read the types file
        with open("../frontend/src/types/index.ts", "r") as f:
            content = f.read()

        # Check for JSDoc comment about id being client-side generated
        assert "client-side" in content.lower() or "Client-side" in content
        assert "DraftCard" in content

        # Verify the comment is near the id field
        # Look for pattern like /** ... client-side ... */ followed by id: string
        import re
        pattern = r'/\*\*[^*]*client-side[^*]*\*/\s*\n\s*id:\s*string'
        match = re.search(pattern, content, re.IGNORECASE)
        assert match is not None, "JSDoc comment for client-side id should be present"


class TestValidatorFieldNamesConstant:
    """Tests verifying field names are defined in constants, not hardcoded."""

    def test_kana_only_fields_is_module_level_constant(self):
        """KANA_ONLY_FIELDS should be a module-level constant, not defined inside functions."""
        import ast

        with open("app/services/validator.py", "r") as f:
            content = f.read()

        tree = ast.parse(content)

        # Check that KANA_ONLY_FIELDS is assigned at module level
        found_at_module_level = False
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'KANA_ONLY_FIELDS':
                        found_at_module_level = True
                        break

        assert found_at_module_level, "KANA_ONLY_FIELDS should be defined at module level"

    def test_required_non_empty_fields_is_module_level_constant(self):
        """REQUIRED_NON_EMPTY_FIELDS should be a module-level constant."""
        import ast

        with open("app/services/validator.py", "r") as f:
            content = f.read()

        tree = ast.parse(content)

        # Check that REQUIRED_NON_EMPTY_FIELDS is assigned at module level
        found_at_module_level = False
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'REQUIRED_NON_EMPTY_FIELDS':
                        found_at_module_level = True
                        break

        assert found_at_module_level, "REQUIRED_NON_EMPTY_FIELDS should be defined at module level"

    def test_validate_card_uses_kana_only_fields_constant(self):
        """validate_card should use KANA_ONLY_FIELDS constant, not hardcoded values."""
        import ast

        with open("app/services/validator.py", "r") as f:
            content = f.read()

        tree = ast.parse(content)

        # Find the validate_card function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'validate_card':
                # Look for usage of KANA_ONLY_FIELDS in a for loop
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        if hasattr(child, 'iter'):
                            iter_node = child.iter
                            if isinstance(iter_node, ast.Name) and iter_node.id == 'KANA_ONLY_FIELDS':
                                # Found usage of the constant
                                return

        pytest.fail("validate_card should use KANA_ONLY_FIELDS constant in a loop")

    def test_validate_card_uses_required_non_empty_fields_constant(self):
        """validate_card should use REQUIRED_NON_EMPTY_FIELDS constant."""
        import ast

        with open("app/services/validator.py", "r") as f:
            content = f.read()

        tree = ast.parse(content)

        # Find the validate_card function
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'validate_card':
                # Look for usage of REQUIRED_NON_EMPTY_FIELDS in a for loop
                for child in ast.walk(node):
                    if isinstance(child, ast.For):
                        if hasattr(child, 'iter'):
                            iter_node = child.iter
                            if isinstance(iter_node, ast.Name) and iter_node.id == 'REQUIRED_NON_EMPTY_FIELDS':
                                # Found usage of the constant
                                return

        pytest.fail("validate_card should use REQUIRED_NON_EMPTY_FIELDS constant in a loop")
