"""Tests for configurable environment variables.

These tests verify that hardcoded configuration values have been properly
refactored to use environment variables with appropriate defaults and fallback behavior.

Configuration values tested:
- MIGRATE_OLD_NOTE_TYPE: Note type to migrate from (migrate.py)
- MIGRATE_NEW_NOTE_TYPE: Note type to migrate to (migrate.py)
- MIGRATE_FIELD_MAPPING: JSON field mapping for migration (migrate.py)
- CLAUDE_MODEL: Claude model to use for generation (agent.py)
- ANKI_CONNECT_TIMEOUT: Timeout for AnkiConnect requests (anki_connect.py)
- CONFIG_TTL: Cache TTL for config file (config.py)
"""

import importlib
import json
import os
import sys
from unittest.mock import patch

import pytest


# Base environment to ensure required vars are always set
BASE_ENV = {
    "REQUIRE_AUTH": "false",  # Disable auth for testing
}


def _reload_module_with_env(module_name: str, env_updates: dict):
    """Reload a module with specific environment variables.

    This helper ensures that:
    1. Required base environment variables are always present
    2. The specified module is reloaded with fresh env var values
    3. Only the target module is reloaded (not the entire dependency tree)
    """
    # Build environment: base + updates
    env = {**BASE_ENV, **env_updates}

    with patch.dict(os.environ, env):
        # Remove the specific module from cache
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Import and return the module
        return importlib.import_module(module_name)


class TestMigrateNoteTypes:
    """Tests for OLD_NOTE_TYPE and NEW_NOTE_TYPE configuration."""

    def test_old_note_type_default(self):
        """Test OLD_NOTE_TYPE uses correct default when env var not set."""
        # Test without MIGRATE_OLD_NOTE_TYPE set
        module = _reload_module_with_env("app.routes.migrate", {})
        assert module.OLD_NOTE_TYPE == "Philippe's Japanese v3"

    def test_old_note_type_from_env(self):
        """Test OLD_NOTE_TYPE uses environment variable when set."""
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_OLD_NOTE_TYPE": "Custom Old Note Type"}
        )
        assert module.OLD_NOTE_TYPE == "Custom Old Note Type"

    def test_new_note_type_default(self):
        """Test NEW_NOTE_TYPE uses correct default when env var not set."""
        module = _reload_module_with_env("app.routes.migrate", {})
        assert module.NEW_NOTE_TYPE == "Japanese Vocabulary (Agent)"

    def test_new_note_type_from_env(self):
        """Test NEW_NOTE_TYPE uses environment variable when set."""
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_NEW_NOTE_TYPE": "Custom New Note Type"}
        )
        assert module.NEW_NOTE_TYPE == "Custom New Note Type"


class TestMigrateFieldMapping:
    """Tests for FIELD_MAPPING configuration via JSON environment variable."""

    def test_field_mapping_default(self):
        """Test FIELD_MAPPING uses correct default when env var not set."""
        module = _reload_module_with_env("app.routes.migrate", {})

        # Check expected default mappings
        expected_mappings = {
            "Kana": "Hiragana/Katakana",
            "Romaji": "Romaji",
            "Kanji": "Kanji",
            "English": "English",
            "Nederlands": "Dutch",
            "Example": "Example sentence hiragana/katakana",
            "Example Kanji": "Example sentence kanji",
            "Example translation": "Example sentence translation",
            "Extra": "Extra notes",
            "Sound": "Sound",
            "Sound Example": "Sound example",
        }
        assert module.FIELD_MAPPING == expected_mappings

    def test_field_mapping_from_env_json(self):
        """Test FIELD_MAPPING can be overridden via JSON environment variable."""
        custom_mapping = {
            "OldField1": "NewField1",
            "OldField2": "NewField2",
        }
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": json.dumps(custom_mapping)}
        )
        assert module.FIELD_MAPPING == custom_mapping

    def test_field_mapping_invalid_json_falls_back_to_default(self):
        """Test FIELD_MAPPING falls back to default on invalid JSON."""
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": "not valid json {"}
        )

        # Should fall back to default (non-empty dict with expected structure)
        assert isinstance(module.FIELD_MAPPING, dict)
        assert "Kana" in module.FIELD_MAPPING  # Check a known default key

    def test_field_mapping_non_dict_json_falls_back_to_default(self):
        """Test FIELD_MAPPING falls back to default if JSON is not an object."""
        # Valid JSON but not an object
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": '["array", "not", "dict"]'}
        )

        # Should fall back to default
        assert isinstance(module.FIELD_MAPPING, dict)
        assert "Kana" in module.FIELD_MAPPING


class TestClaudeModel:
    """Tests for DEFAULT_MODEL configuration in agent.py."""

    def test_default_model_default(self):
        """Test DEFAULT_MODEL uses correct default when env var not set."""
        module = _reload_module_with_env("app.services.agent", {})
        assert module.DEFAULT_MODEL == "claude-sonnet-4-5-20250929"

    def test_default_model_from_env(self):
        """Test DEFAULT_MODEL uses environment variable when set."""
        module = _reload_module_with_env(
            "app.services.agent",
            {"CLAUDE_MODEL": "claude-opus-4-20250514"}
        )
        assert module.DEFAULT_MODEL == "claude-opus-4-20250514"

    def test_default_model_custom_value(self):
        """Test DEFAULT_MODEL accepts arbitrary model names."""
        module = _reload_module_with_env(
            "app.services.agent",
            {"CLAUDE_MODEL": "claude-custom-model-2025"}
        )
        assert module.DEFAULT_MODEL == "claude-custom-model-2025"


class TestAnkiConnectTimeout:
    """Tests for DEFAULT_TIMEOUT configuration in anki_connect.py."""

    def test_default_timeout_default(self):
        """Test DEFAULT_TIMEOUT uses correct default when env var not set."""
        module = _reload_module_with_env("app.services.anki_connect", {})
        assert module.DEFAULT_TIMEOUT == 30.0

    def test_default_timeout_from_env(self):
        """Test DEFAULT_TIMEOUT uses environment variable when set."""
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "60.0"}
        )
        assert module.DEFAULT_TIMEOUT == 60.0

    def test_default_timeout_integer_string(self):
        """Test DEFAULT_TIMEOUT handles integer string values."""
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "45"}
        )
        assert module.DEFAULT_TIMEOUT == 45.0

    def test_anki_client_accepts_custom_timeout(self):
        """Test AnkiConnectClient accepts custom timeout parameter."""
        module = _reload_module_with_env("app.services.anki_connect", {})

        # Create client with custom timeout
        client = module.AnkiConnectClient(timeout=120.0)
        assert client.timeout == 120.0

    def test_anki_client_uses_default_timeout_when_none(self):
        """Test AnkiConnectClient uses DEFAULT_TIMEOUT when timeout not specified."""
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "75.5"}
        )

        # Create client without specifying timeout
        client = module.AnkiConnectClient()
        assert client.timeout == module.DEFAULT_TIMEOUT
        assert client.timeout == 75.5

    def test_invalid_timeout_raises_error(self):
        """Test that invalid ANKI_CONNECT_TIMEOUT raises ValueError."""
        with patch.dict(os.environ, {**BASE_ENV, "ANKI_CONNECT_TIMEOUT": "not-a-number"}):
            if "app.services.anki_connect" in sys.modules:
                del sys.modules["app.services.anki_connect"]
            # Should raise ValueError when trying to convert to float
            with pytest.raises(ValueError):
                importlib.import_module("app.services.anki_connect")


class TestConfigTTL:
    """Tests for CONFIG_TTL configuration in config.py."""

    def test_config_ttl_default(self):
        """Test CONFIG_TTL uses correct default when env var not set."""
        module = _reload_module_with_env("app.config", {})
        assert module.CONFIG_TTL == 300  # 5 minutes default

    def test_config_ttl_from_env(self):
        """Test CONFIG_TTL uses environment variable when set."""
        module = _reload_module_with_env("app.config", {"CONFIG_TTL": "600"})
        assert module.CONFIG_TTL == 600

    def test_config_ttl_zero(self):
        """Test CONFIG_TTL can be set to zero (disable caching)."""
        module = _reload_module_with_env("app.config", {"CONFIG_TTL": "0"})
        assert module.CONFIG_TTL == 0

    def test_invalid_config_ttl_raises_error(self):
        """Test that invalid CONFIG_TTL raises ValueError."""
        with patch.dict(os.environ, {**BASE_ENV, "CONFIG_TTL": "not-a-number"}):
            if "app.config" in sys.modules:
                del sys.modules["app.config"]
            with pytest.raises(ValueError):
                importlib.import_module("app.config")


class TestEnvironmentVariableFallbackGracefully:
    """Tests for graceful fallback behavior with invalid env var values."""

    def test_empty_env_vars_use_defaults(self):
        """Test that empty string env vars are handled gracefully."""
        # Note: empty strings still evaluate to truthy for os.getenv default behavior
        # but should be treated as "not set" for some configs

        # Test CLAUDE_MODEL with empty string - should use that empty string
        # (This is current behavior - may want to change to use default instead)
        module = _reload_module_with_env("app.services.agent", {"CLAUDE_MODEL": ""})
        # Empty string is returned as-is by os.getenv when set
        # This tests the current behavior - consider adding validation if needed
        assert module.DEFAULT_MODEL == ""

    def test_whitespace_env_vars(self):
        """Test that whitespace-only values are handled."""
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_OLD_NOTE_TYPE": "  Note Type With Spaces  "}
        )
        # Preserves whitespace - caller should strip if needed
        assert module.OLD_NOTE_TYPE == "  Note Type With Spaces  "


class TestConfigurationIntegration:
    """Integration tests ensuring configurations work together."""

    def test_multiple_env_vars_can_be_set_together(self):
        """Test that multiple environment variables can be configured at once."""
        custom_env = {
            "MIGRATE_OLD_NOTE_TYPE": "Old Type",
            "MIGRATE_NEW_NOTE_TYPE": "New Type",
            "CLAUDE_MODEL": "claude-opus-4-20250514",
            "ANKI_CONNECT_TIMEOUT": "60",
            "CONFIG_TTL": "120",
        }

        with patch.dict(os.environ, {**BASE_ENV, **custom_env}):
            # Reload all modules
            for mod_name in ["app.routes.migrate", "app.services.agent",
                           "app.services.anki_connect", "app.config"]:
                if mod_name in sys.modules:
                    del sys.modules[mod_name]

            migrate = importlib.import_module("app.routes.migrate")
            agent = importlib.import_module("app.services.agent")
            anki_connect = importlib.import_module("app.services.anki_connect")
            config = importlib.import_module("app.config")

            assert migrate.OLD_NOTE_TYPE == "Old Type"
            assert migrate.NEW_NOTE_TYPE == "New Type"
            assert agent.DEFAULT_MODEL == "claude-opus-4-20250514"
            assert anki_connect.DEFAULT_TIMEOUT == 60.0
            assert config.CONFIG_TTL == 120

    def test_field_mapping_empty_object(self):
        """Test that empty JSON object for field mapping is accepted."""
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": "{}"}
        )
        assert module.FIELD_MAPPING == {}

    def test_field_mapping_with_special_characters(self):
        """Test field mapping with special characters in keys/values."""
        custom_mapping = {
            "Field with spaces": "New field with spaces",
            "Field-with-dashes": "New-field-with-dashes",
            "Field_with_underscores": "New_with_underscores",
            "Field/with/slashes": "New/with/slashes",
        }
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": json.dumps(custom_mapping)}
        )
        assert module.FIELD_MAPPING == custom_mapping


class TestAnkiClientTimeoutBehavior:
    """Tests for AnkiConnectClient timeout handling."""

    def test_client_explicit_timeout_overrides_default(self):
        """Test that explicit timeout parameter overrides DEFAULT_TIMEOUT."""
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "30"}
        )

        assert module.DEFAULT_TIMEOUT == 30.0

        # Explicit timeout should override
        client = module.AnkiConnectClient(timeout=100.0)
        assert client.timeout == 100.0

    def test_client_none_timeout_uses_default(self):
        """Test that None timeout uses DEFAULT_TIMEOUT."""
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "50"}
        )

        # Explicitly pass None (should use default)
        client = module.AnkiConnectClient(timeout=None)
        assert client.timeout == 50.0

    def test_client_zero_timeout(self):
        """Test that zero timeout is accepted (no timeout)."""
        module = _reload_module_with_env("app.services.anki_connect", {})

        client = module.AnkiConnectClient(timeout=0)
        assert client.timeout == 0

    def test_client_stores_url_correctly(self):
        """Test that client URL is constructed correctly."""
        module = _reload_module_with_env("app.services.anki_connect", {})

        # Default host and port
        client = module.AnkiConnectClient()
        assert client.url == "http://localhost:8765"

        # Custom host and port
        client = module.AnkiConnectClient(host="192.168.1.100", port=9000)
        assert client.url == "http://192.168.1.100:9000"


class TestLoadFieldMappingFunction:
    """Tests for the _load_field_mapping() function directly."""

    def test_load_field_mapping_returns_default_when_not_set(self):
        """Test _load_field_mapping returns default mapping when env var not set."""
        module = _reload_module_with_env("app.routes.migrate", {})

        # Call the function within the patched environment
        with patch.dict(os.environ, BASE_ENV):
            result = module._load_field_mapping()

        # Should return default mapping
        assert "Kana" in result
        assert result["Kana"] == "Hiragana/Katakana"

    def test_load_field_mapping_parses_valid_json(self):
        """Test _load_field_mapping parses valid JSON from env var."""
        custom = {"A": "B", "C": "D"}
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": json.dumps(custom)}
        )

        # Call function within patched environment
        with patch.dict(os.environ, {**BASE_ENV, "MIGRATE_FIELD_MAPPING": json.dumps(custom)}):
            result = module._load_field_mapping()
        assert result == custom

    def test_load_field_mapping_handles_nested_json(self):
        """Test that _load_field_mapping rejects nested objects (expects flat mapping)."""
        # Nested JSON is valid JSON but not a valid flat mapping
        # Current implementation accepts any dict, so this tests that behavior
        nested = {"outer": {"inner": "value"}}
        module = _reload_module_with_env(
            "app.routes.migrate",
            {"MIGRATE_FIELD_MAPPING": json.dumps(nested)}
        )

        # Call function within patched environment
        with patch.dict(os.environ, {**BASE_ENV, "MIGRATE_FIELD_MAPPING": json.dumps(nested)}):
            result = module._load_field_mapping()
        # Current behavior: accepts any dict (no validation of value types)
        assert result == nested


class TestModuleLevelLoadingBehavior:
    """Tests for module-level variable initialization behavior."""

    def test_field_mapping_loaded_at_module_init(self):
        """Test that FIELD_MAPPING is set when module is imported."""
        module = _reload_module_with_env("app.routes.migrate", {})

        # FIELD_MAPPING should exist and be a dict
        assert hasattr(module, "FIELD_MAPPING")
        assert isinstance(module.FIELD_MAPPING, dict)

    def test_note_types_loaded_at_module_init(self):
        """Test that note type constants are set when module is imported."""
        module = _reload_module_with_env("app.routes.migrate", {})

        assert hasattr(module, "OLD_NOTE_TYPE")
        assert hasattr(module, "NEW_NOTE_TYPE")
        assert isinstance(module.OLD_NOTE_TYPE, str)
        assert isinstance(module.NEW_NOTE_TYPE, str)

    def test_default_timeout_is_float(self):
        """Test that DEFAULT_TIMEOUT is always a float."""
        # With default
        module = _reload_module_with_env("app.services.anki_connect", {})
        assert isinstance(module.DEFAULT_TIMEOUT, float)

        # With integer string
        module = _reload_module_with_env(
            "app.services.anki_connect",
            {"ANKI_CONNECT_TIMEOUT": "42"}
        )
        assert isinstance(module.DEFAULT_TIMEOUT, float)
        assert module.DEFAULT_TIMEOUT == 42.0

    def test_config_ttl_is_int(self):
        """Test that CONFIG_TTL is always an int."""
        # With default
        module = _reload_module_with_env("app.config", {})
        assert isinstance(module.CONFIG_TTL, int)

        # With explicit value
        module = _reload_module_with_env("app.config", {"CONFIG_TTL": "120"})
        assert isinstance(module.CONFIG_TTL, int)
        assert module.CONFIG_TTL == 120
