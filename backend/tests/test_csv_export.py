"""Tests for the CSV export service."""

import pytest
from app.services.csv_export import generate_csv, get_csv_filename
from app.models import GeneratedCard, AnkiConfig


class TestGenerateCsv:
    """Tests for generate_csv function."""

    def get_config(self) -> AnkiConfig:
        return AnkiConfig(
            fields=["Field1", "Field2", "Field3"],
            tags=["tag1", "tag2"],
            tagsColumnEnabled=True,
            tagsColumnName="Tags",
        )

    def get_card(self) -> GeneratedCard:
        return GeneratedCard(
            fields={
                "Field1": "Value1",
                "Field2": "Value2",
                "Field3": "Value3",
            },
            tags=["tag1", "tag2"],
            auto_classified_type="word",
        )

    def test_generates_csv_with_all_fields(self):
        config = self.get_config()
        card = self.get_card()
        csv_content = generate_csv([card], config)

        # Should have one row with quoted values
        assert '"Value1"' in csv_content
        assert '"Value2"' in csv_content
        assert '"Value3"' in csv_content

    def test_tags_column_when_enabled(self):
        config = self.get_config()
        card = self.get_card()
        csv_content = generate_csv([card], config)

        # Tags should be space-separated
        assert '"tag1 tag2"' in csv_content

    def test_no_tags_column_when_disabled(self):
        config = self.get_config()
        config.tagsColumnEnabled = False
        card = self.get_card()
        csv_content = generate_csv([card], config)

        # Should not have tags at the end
        lines = csv_content.strip().split('\n')
        # Count columns (should be 3, not 4)
        first_line = lines[0]
        columns = first_line.count('","') + 1
        assert columns == 3

    def test_handles_commas_in_values(self):
        config = self.get_config()
        card = GeneratedCard(
            fields={
                "Field1": "Value, with, commas",
                "Field2": "Normal",
                "Field3": "End",
            },
            tags=[],
            auto_classified_type="word",
        )
        csv_content = generate_csv([card], config)

        # Value with commas should be properly quoted
        assert '"Value, with, commas"' in csv_content

    def test_handles_newlines_in_values(self):
        config = self.get_config()
        card = GeneratedCard(
            fields={
                "Field1": "Line1\nLine2",
                "Field2": "Normal",
                "Field3": "End",
            },
            tags=[],
            auto_classified_type="word",
        )
        csv_content = generate_csv([card], config)

        # Should handle newlines in quoted strings
        assert 'Line1\nLine2' in csv_content

    def test_handles_quotes_in_values(self):
        config = self.get_config()
        card = GeneratedCard(
            fields={
                "Field1": 'Value "with" quotes',
                "Field2": "Normal",
                "Field3": "End",
            },
            tags=[],
            auto_classified_type="word",
        )
        csv_content = generate_csv([card], config)

        # Quotes should be escaped (doubled)
        assert '""with""' in csv_content

    def test_field_order_matches_config(self):
        config = AnkiConfig(
            fields=["Z_Field", "A_Field", "M_Field"],
            tags=[],
            tagsColumnEnabled=False,
            tagsColumnName="Tags",
        )
        card = GeneratedCard(
            fields={
                "A_Field": "A",
                "Z_Field": "Z",
                "M_Field": "M",
            },
            tags=[],
            auto_classified_type="word",
        )
        csv_content = generate_csv([card], config)

        # Order should be Z, A, M (as per config, not alphabetical)
        line = csv_content.strip()
        # The order of values should match config order
        assert line == '"Z","A","M"'

    def test_multiple_cards(self):
        config = self.get_config()
        cards = [
            GeneratedCard(fields={"Field1": "Card1-1", "Field2": "Card1-2", "Field3": "Card1-3"}, tags=["tag1"], auto_classified_type="word"),
            GeneratedCard(fields={"Field1": "Card2-1", "Field2": "Card2-2", "Field3": "Card2-3"}, tags=["tag2"], auto_classified_type="phrase"),
        ]
        csv_content = generate_csv(cards, config)

        lines = csv_content.strip().split('\n')
        assert len(lines) == 2


class TestGetCsvFilename:
    """Tests for get_csv_filename function."""

    def test_adds_csv_extension(self):
        result = get_csv_filename("myfile")
        assert result == "myfile.csv"

    def test_handles_empty_name(self):
        result = get_csv_filename("")
        assert result == "anki_cards.csv"

    def test_handles_none(self):
        result = get_csv_filename(None)
        assert result == "anki_cards.csv"

    def test_sanitizes_path_separators(self):
        result = get_csv_filename("path/to/file")
        assert "/" not in result
        assert result.endswith(".csv")

    def test_allows_underscores_and_hyphens(self):
        result = get_csv_filename("my_file-name")
        assert result == "my_file-name.csv"

    def test_allows_spaces(self):
        result = get_csv_filename("my file name")
        assert result == "my file name.csv"
