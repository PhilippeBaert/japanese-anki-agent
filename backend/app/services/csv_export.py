"""CSV export service for Anki cards."""

import csv
import io
from typing import Optional

from ..models import GeneratedCard, AnkiConfig


def generate_csv(
    cards: list[GeneratedCard],
    config: AnkiConfig,
    source: Optional[str] = None,
) -> str:
    """
    Generate a CSV string from generated cards in Anki-compatible format.

    Anki's text import format (2.1.54+):
    - Uses #directive:value headers at top of file
    - First regular line determines field count
    - Tags are in a column that user maps to "tags" during import
    - NO regular CSV header row (would be imported as a card!)

    Args:
        cards: List of generated cards
        config: Anki configuration with field order and tag settings
        source: Optional source tag to prepend to all cards

    Returns:
        CSV content as a string
    """
    output = io.StringIO()

    # Determine column names for Anki directive
    columns = list(config.fields)
    if config.tagsColumnEnabled:
        columns.append(config.tagsColumnName)

    # Write Anki-specific header directives (Anki 2.1.54+)
    # #separator:Comma - explicit comma separator
    # #html:false - treat as plain text
    # #columns: - column names (separated by the set separator)
    # #tags column: - tell Anki which column contains tags (1-indexed)
    output.write("#separator:Comma\n")
    output.write("#html:false\n")
    output.write(f"#columns:{','.join(columns)}\n")
    if config.tagsColumnEnabled:
        # Tags column is the last column (1-indexed)
        tags_column_index = len(config.fields) + 1
        output.write(f"#tags column:{tags_column_index}\n")

    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Write data rows
    for card in cards:
        row = []

        # Add field values in config order
        for field in config.fields:
            value = card.fields.get(field, '')
            row.append(value)

        # Add tags column if enabled
        if config.tagsColumnEnabled:
            # Build tags list with source prepended if provided
            tags_list = []
            if source:
                tags_list.append(source)
            tags_list.extend(card.tags)
            tags_value = ' '.join(tags_list)
            row.append(tags_value)

        writer.writerow(row)

    return output.getvalue()


def generate_csv_with_priority(
    cards: list[GeneratedCard],
    config: AnkiConfig,
    source: Optional[str] = None,
    is_core: bool = False,
) -> str:
    """
    Generate CSV with optional 'core' tag for priority cards.

    Args:
        cards: List of generated cards
        config: Anki configuration with field order and tag settings
        source: Optional source tag to prepend to all cards
        is_core: If True, adds 'core' tag to all cards in this batch

    Returns:
        CSV content as a string
    """
    output = io.StringIO()

    columns = list(config.fields)
    if config.tagsColumnEnabled:
        columns.append(config.tagsColumnName)

    output.write("#separator:Comma\n")
    output.write("#html:false\n")
    output.write(f"#columns:{','.join(columns)}\n")
    if config.tagsColumnEnabled:
        tags_column_index = len(config.fields) + 1
        output.write(f"#tags column:{tags_column_index}\n")

    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    for card in cards:
        row = []

        for field in config.fields:
            value = card.fields.get(field, '')
            row.append(value)

        if config.tagsColumnEnabled:
            tags_list = []
            if source:
                tags_list.append(source)
            if is_core:
                tags_list.append('core')
            else:
                tags_list.append('extra')
            tags_list.extend(card.tags)
            tags_value = ' '.join(tags_list)
            row.append(tags_value)

        writer.writerow(row)

    return output.getvalue()


def get_csv_filename(base_name: Optional[str]) -> str:
    """Generate a safe filename for the CSV export."""
    if not base_name:
        base_name = 'anki_cards'

    # Remove any path separators and unsafe characters
    safe_name = ''.join(c for c in base_name if c.isalnum() or c in ('_', '-', ' '))
    safe_name = safe_name.strip() or 'anki_cards'

    return f"{safe_name}.csv"
