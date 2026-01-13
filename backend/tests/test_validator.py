"""Tests for the validator service."""

import pytest
from app.services.validator import (
    has_kanji,
    is_kana_only,
    ends_with_maru,
    validate_card,
    validate_all_cards,
)


class TestHasKanji:
    """Tests for has_kanji function."""

    def test_detects_kanji(self):
        assert has_kanji("日本語") == True
        assert has_kanji("漢字") == True
        assert has_kanji("食べる") == True

    def test_no_kanji_in_hiragana(self):
        assert has_kanji("ひらがな") == False
        assert has_kanji("たべる") == False

    def test_no_kanji_in_katakana(self):
        assert has_kanji("カタカナ") == False
        assert has_kanji("オランダ") == False

    def test_no_kanji_in_romaji(self):
        assert has_kanji("romaji") == False
        assert has_kanji("nihongo") == False

    def test_mixed_with_kanji(self):
        assert has_kanji("私はたべます") == True
        assert has_kanji("オランダに住んでいます") == True

    def test_empty_string(self):
        assert has_kanji("") == False


class TestIsKanaOnly:
    """Tests for is_kana_only function."""

    def test_hiragana_only(self):
        assert is_kana_only("ひらがな") == True
        assert is_kana_only("たべます") == True

    def test_katakana_only(self):
        assert is_kana_only("カタカナ") == True
        assert is_kana_only("オランダ") == True

    def test_mixed_kana(self):
        assert is_kana_only("オランダ に すんでいます") == True
        assert is_kana_only("ふつう でんしゃ で いきます") == True

    def test_with_punctuation(self):
        assert is_kana_only("たべます。") == True
        assert is_kana_only("なに？") == True

    def test_with_numbers(self):
        assert is_kana_only("9じ") == True
        assert is_kana_only("１０にん") == True

    def test_rejects_kanji(self):
        assert is_kana_only("日本") == False
        assert is_kana_only("漢字") == False
        assert is_kana_only("たべ物") == False

    def test_empty_string(self):
        assert is_kana_only("") == True


class TestEndsWithMaru:
    """Tests for ends_with_maru function."""

    def test_ends_with_maru(self):
        assert ends_with_maru("たべます。") == True
        assert ends_with_maru("オランダ に すんでいます。") == True

    def test_no_maru(self):
        assert ends_with_maru("たべます") == False
        assert ends_with_maru("オランダ") == False

    def test_with_trailing_space(self):
        assert ends_with_maru("たべます。 ") == True

    def test_empty_string(self):
        assert ends_with_maru("") == True

    def test_none(self):
        assert ends_with_maru(None) == True


class TestValidateCard:
    """Tests for validate_card function."""

    def get_valid_card(self):
        return {
            "fields": {
                "Hiragana/Katakana": "オランダ",
                "Romaji": "oranda",
                "Kanji": "",
                "English": "Netherlands",
                "Dutch": "Nederland",
                "Example sentence hiragana/katakana": "オランダ に すんでいます。",
                "Example sentence kanji": "オランダに住んでいます。",
                "Example sentence translation": "I live in the Netherlands.",
                "Extra notes": "",
                "Sound": "",
            },
            "tags": ["vocabulary"],
        }

    def test_valid_card_passes(self):
        card = self.get_valid_card()
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert errors == []

    def test_kanji_in_kana_field_fails(self):
        card = self.get_valid_card()
        card["fields"]["Hiragana/Katakana"] = "日本"
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert len(errors) == 1
        assert "kanji" in errors[0].lower()

    def test_kanji_in_example_sentence_kana_fails(self):
        card = self.get_valid_card()
        card["fields"]["Example sentence hiragana/katakana"] = "日本に行きます。"
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert len(errors) == 1
        assert "kanji" in errors[0].lower()

    def test_sentence_without_maru_fails(self):
        card = self.get_valid_card()
        card["fields"]["Example sentence hiragana/katakana"] = "オランダ に すんでいます"
        card["fields"]["Example sentence kanji"] = "オランダに住んでいます"
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert len(errors) == 2  # Both sentence fields missing 。

    def test_missing_translation_fails(self):
        card = self.get_valid_card()
        card["fields"]["Example sentence translation"] = ""
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert len(errors) == 1
        assert "translation" in errors[0].lower()

    def test_missing_field_fails(self):
        card = self.get_valid_card()
        del card["fields"]["Romaji"]
        fields = list(self.get_valid_card()["fields"].keys())
        errors = validate_card(card, fields)
        assert any("missing" in e.lower() for e in errors)

    def test_tags_not_list_fails(self):
        card = self.get_valid_card()
        card["tags"] = "vocabulary"  # Should be a list
        fields = list(card["fields"].keys())
        errors = validate_card(card, fields)
        assert any("list" in e.lower() for e in errors)


class TestValidateAllCards:
    """Tests for validate_all_cards function."""

    def get_valid_card(self):
        return {
            "fields": {
                "Hiragana/Katakana": "オランダ",
                "Romaji": "oranda",
                "Kanji": "",
                "English": "Netherlands",
                "Dutch": "Nederland",
                "Example sentence hiragana/katakana": "オランダ に すんでいます。",
                "Example sentence kanji": "オランダに住んでいます。",
                "Example sentence translation": "I live in the Netherlands.",
                "Extra notes": "",
                "Sound": "",
            },
            "tags": ["vocabulary"],
        }

    def test_all_valid_cards(self):
        cards = [self.get_valid_card(), self.get_valid_card()]
        fields = list(cards[0]["fields"].keys())
        is_valid, errors = validate_all_cards(cards, fields)
        assert is_valid == True
        assert errors == []

    def test_one_invalid_card(self):
        card1 = self.get_valid_card()
        card2 = self.get_valid_card()
        card2["fields"]["Hiragana/Katakana"] = "日本"
        cards = [card1, card2]
        fields = list(card1["fields"].keys())
        is_valid, errors = validate_all_cards(cards, fields)
        assert is_valid == False
        assert "Card 2" in errors[0]
