"""Validation and repair logic for generated Anki cards."""

import re
from typing import Tuple

# Unicode ranges for Japanese character detection
HIRAGANA_PATTERN = re.compile(r'[\u3040-\u309f]')
KATAKANA_PATTERN = re.compile(r'[\u30a0-\u30ff]')
KANJI_PATTERN = re.compile(r'[\u4e00-\u9faf\u3400-\u4dbf]')

# Allowed characters in kana-only fields: hiragana, katakana, punctuation, spaces, numbers
KANA_ONLY_PATTERN = re.compile(r'^[\u3040-\u309f\u30a0-\u30ff\u3000-\u303f\s0-9０-９。、・「」（）]*$')


def has_kanji(text: str) -> bool:
    """Check if text contains any kanji characters."""
    return bool(KANJI_PATTERN.search(text))


def is_kana_only(text: str) -> bool:
    """Check if text contains only kana, punctuation, spaces, and numbers."""
    if not text:
        return True
    return bool(KANA_ONLY_PATTERN.match(text))


def ends_with_maru(text: str) -> bool:
    """Check if text ends with Japanese full stop 。"""
    return text.strip().endswith('。') if text else True


def validate_card(card: dict, fields: list[str]) -> list[str]:
    """
    Validate a single generated card.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    card_fields = card.get('fields', {})

    # Check kana-only fields for kanji
    kana_only_fields = ['Hiragana/Katakana', 'Example sentence hiragana/katakana']
    for field in kana_only_fields:
        value = card_fields.get(field, '')
        if value and has_kanji(value):
            errors.append(f"Field '{field}' contains kanji but should be kana-only: '{value}'")

    # Check example sentence fields
    # For sentence cards: all 3 example fields should be empty
    # For word/phrase cards: all 3 example fields should be filled
    example_kana = card_fields.get('Example sentence hiragana/katakana', '').strip()
    example_kanji = card_fields.get('Example sentence kanji', '').strip()
    example_translation = card_fields.get('Example sentence translation', '').strip()

    all_empty = not example_kana and not example_kanji and not example_translation
    all_filled = example_kana and example_kanji and example_translation

    if not all_empty and not all_filled:
        errors.append("Example sentence fields must be either all empty (sentence card) or all filled (word/phrase card)")

    # If example sentences are filled, validate them
    if example_kana and not ends_with_maru(example_kana):
        errors.append(f"Field 'Example sentence hiragana/katakana' should end with 。: '{example_kana}'")
    if example_kanji and not ends_with_maru(example_kanji):
        errors.append(f"Field 'Example sentence kanji' should end with 。: '{example_kanji}'")

    # Check all required fields are present
    for field in fields:
        if field not in card_fields:
            errors.append(f"Missing required field: '{field}'")

    # Check tags is a list
    if not isinstance(card.get('tags'), list):
        errors.append("'tags' must be a list")

    return errors


def validate_all_cards(cards: list[dict], fields: list[str]) -> Tuple[bool, list[str]]:
    """
    Validate all generated cards.
    Returns (is_valid, all_errors).
    """
    all_errors = []

    for i, card in enumerate(cards):
        card_errors = validate_card(card, fields)
        for error in card_errors:
            all_errors.append(f"Card {i + 1}: {error}")

    return len(all_errors) == 0, all_errors
