"""Tests for prompt generation functions."""

import pytest
from app.prompts.generation import build_generation_prompt, build_repair_prompt


class TestBuildGenerationPromptContainsKeyElements:
    """Test that build_generation_prompt contains all required elements."""

    def get_sample_draft_cards(self):
        """Return sample draft cards for testing."""
        return [
            {
                "raw_input": "tabemasu",
                "fixed_english": None,
                "fixed_dutch": None,
                "extra_notes": None,
                "card_type_override": None
            }
        ]

    def get_sample_fields(self):
        """Return sample fields for testing."""
        return [
            "Hiragana/Katakana",
            "Romaji",
            "Kanji",
            "English",
            "Dutch",
            "Example sentence hiragana/katakana",
            "Example sentence kanji",
            "Example sentence translation",
            "Extra notes",
            "Sound",
            "Sound example"
        ]

    def get_sample_tags(self):
        """Return sample tags for testing."""
        return ["word", "phrase", "sentence"]

    def test_contains_single_word_conjugated_verb(self):
        """Fix 1: Verify prompt contains SINGLE-WORD conjugated verb reference."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "SINGLE-WORD conjugated verb" in prompt

    def test_contains_does_not_apply_to_phrase_or_sentence(self):
        """Fix 1: Verify prompt clarifies rule does NOT apply to phrase or sentence cards."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "does NOT apply to phrase or sentence cards" in prompt

    def test_contains_compound_verbs_and_auxiliaries(self):
        """Fix 3: Verify prompt contains compound verb definition."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Compound Verbs and Auxiliaries" in prompt

    def test_contains_v_te_auxiliary_verbs(self):
        """Fix 3: Verify prompt contains V-te + auxiliary verbs examples."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "V-て + auxiliary verbs" in prompt

    def test_contains_auto_classified_type_final_classification(self):
        """Fix 4: Verify prompt contains FINAL classification clarification."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "auto_classified_type (this field contains the FINAL classification" in prompt

    def test_contains_use_for_tags(self):
        """Fix 4: Verify prompt contains use for tags bullet point."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Use it for tags" in prompt

    def test_contains_use_that_classification_for_all_purposes(self):
        """Fix 4: Verify prompt contains classification for all purposes."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "use that classification for all purposes" in prompt


class TestBuildRepairPromptContainsSpacingRules:
    """Test that build_repair_prompt contains all required spacing rules."""

    def test_contains_add_space_before_particles(self):
        """Fix 2: Verify repair prompt contains particle spacing rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "ADD SPACE BEFORE particles" in prompt

    def test_contains_do_not_add_space_before_verb_endings(self):
        """Fix 2: Verify repair prompt contains verb ending rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "DO NOT add space before verb endings" in prompt

    def test_contains_compound_verbs_stay_together(self):
        """Fix 2: Verify repair prompt contains compound verb rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "Compound verbs stay together" in prompt

    def test_contains_v_te_auxiliary_verbs_example(self):
        """Fix 2: Verify repair prompt contains V-te + auxiliary verbs example."""
        prompt = build_repair_prompt([], ["test error"])
        assert "V-て + auxiliary verbs stay together" in prompt

    def test_contains_particle_list(self):
        """Fix 2: Verify repair prompt contains particle list."""
        prompt = build_repair_prompt([], ["test error"])
        assert "は、が、を、に、で、と、も、へ、から、まで、より、など" in prompt

    def test_contains_verb_ending_list(self):
        """Fix 2: Verify repair prompt contains verb ending list."""
        prompt = build_repair_prompt([], ["test error"])
        assert "ます、ません、ました、ている、てください、たい、ない" in prompt

    def test_contains_spacing_examples(self):
        """Fix 2: Verify repair prompt contains spacing examples."""
        prompt = build_repair_prompt([], ["test error"])
        # Check for spacing examples in repair prompt
        assert "わたし の ともだち" in prompt
        assert "おおきい いぬ" in prompt

    def test_contains_noun_separation_rule(self):
        """Fix 2: Verify repair prompt contains noun separation rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "Separate nouns from nouns" in prompt
        assert "わたし の ともだち" in prompt

    def test_contains_adjective_separation_rule(self):
        """Fix 2: Verify repair prompt contains adjective separation rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "Separate adjectives from nouns" in prompt
        assert "おおきい いぬ" in prompt

    def test_contains_number_counter_rule(self):
        """Fix 2: Verify repair prompt contains number+counter rule."""
        prompt = build_repair_prompt([], ["test error"])
        assert "Numbers + counters stay together" in prompt
        assert "3にん" in prompt
        assert "9じ" in prompt


class TestPromptFunctionsAreCallable:
    """Test that prompt functions are callable and return expected types."""

    def test_build_generation_prompt_returns_non_empty_string(self):
        """Verify build_generation_prompt returns a non-empty string."""
        draft_cards = [
            {
                "raw_input": "test",
                "fixed_english": None,
                "fixed_dutch": None,
                "extra_notes": None,
                "card_type_override": None
            }
        ]
        fields = ["Field1", "Field2"]
        tags = ["word"]

        result = build_generation_prompt(draft_cards, fields, tags)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_repair_prompt_returns_non_empty_string(self):
        """Verify build_repair_prompt returns a non-empty string with errors embedded."""
        original_cards = [
            {
                "fields": {"Hiragana/Katakana": "たべます"},
                "tags": ["word"],
                "auto_classified_type": "word"
            }
        ]
        errors = ["Test error 1", "Test error 2"]

        result = build_repair_prompt(original_cards, errors)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_repair_prompt_embeds_errors(self):
        """Verify build_repair_prompt embeds the provided errors."""
        errors = ["Kana field contains kanji", "Sentence must end with maru"]
        result = build_repair_prompt([], errors)

        assert "Kana field contains kanji" in result
        assert "Sentence must end with maru" in result

    def test_build_repair_prompt_embeds_cards_json(self):
        """Verify build_repair_prompt embeds the original cards as JSON."""
        original_cards = [
            {
                "fields": {"Hiragana/Katakana": "テスト"},
                "tags": ["word"],
                "auto_classified_type": "word"
            }
        ]
        result = build_repair_prompt(original_cards, ["error"])

        assert "テスト" in result
        assert "Hiragana/Katakana" in result

    def test_build_generation_prompt_includes_draft_card_data(self):
        """Verify build_generation_prompt includes the draft card data."""
        draft_cards = [
            {
                "raw_input": "unique_test_input_xyz",
                "fixed_english": "Test translation",
                "fixed_dutch": None,
                "extra_notes": "Some notes here",
                "card_type_override": "phrase"
            }
        ]
        result = build_generation_prompt(draft_cards, ["Field1"], ["word"])

        assert "unique_test_input_xyz" in result
        assert "Test translation" in result
        assert "Some notes here" in result
        assert '"phrase"' in result

    def test_build_generation_prompt_includes_fields(self):
        """Verify build_generation_prompt includes the provided fields."""
        fields = ["Custom_Field_1", "Custom_Field_2", "Custom_Field_3"]
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]

        result = build_generation_prompt(draft_cards, fields, ["word"])

        assert "Custom_Field_1" in result
        assert "Custom_Field_2" in result
        assert "Custom_Field_3" in result


class TestCompoundVerbExamples:
    """Test that generation prompt contains all compound verb examples from Fix 3."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_v_te_motion_verbs_example(self):
        """Verify prompt contains V-te + motion verbs example."""
        prompt = self.get_prompt()
        assert "もってきます" in prompt

    def test_contains_tabeteshimaimasu_example(self):
        """Verify prompt contains tabeteshimaimasu example."""
        prompt = self.get_prompt()
        assert "たべてしまいます" in prompt

    def test_contains_yondeokimasu_example(self):
        """Verify prompt contains yondeokimasu example."""
        prompt = self.get_prompt()
        assert "よんでおきます" in prompt

    def test_contains_miteimasu_example(self):
        """Verify prompt contains miteimasu example (continuous form)."""
        prompt = self.get_prompt()
        assert "みています" in prompt

    def test_contains_v_stem_suffix_verbs_examples(self):
        """Verify prompt contains V-stem + suffix verbs examples."""
        prompt = self.get_prompt()
        assert "たべはじめます" in prompt
        assert "よみおわります" in prompt

    def test_contains_idiomatic_greeting_example(self):
        """Verify prompt contains idiomatic greeting example."""
        prompt = self.get_prompt()
        assert "いってきます" in prompt
