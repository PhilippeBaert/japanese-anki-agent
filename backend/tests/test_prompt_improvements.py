"""Tests for prompt improvements in generation.py.

This test file verifies all the prompt improvements made to:
/Users/pbr2j2t/japanese-anki-agent/backend/app/prompts/generation.py

Changes tested:
1. Multi-suffix verb spacing rules (lines 106-118)
2. Compound verb definition with 4 categories (lines 124-148)
3. Number format rules with special readings (lines 124-141)
4. Phrase-type card definitions with fossilized greetings (lines 181-211)
5. Keigo handling section H.1 (lines 284-312)
6. Adverbial adjective forms section J.1 (lines 349-365)
7. Emotive adjectives (suki/kirai) section J.2 (lines 367-387)
8. Cross-card consistency section L (lines 325-348)
9. Expanded repair prompt with full rules (lines 400-443)
"""

import pytest
from app.prompts.generation import build_generation_prompt, build_repair_prompt


class TestPromptStructure:
    """Test that prompts return correct types and contain all new sections."""

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

    def test_build_generation_prompt_returns_string(self):
        """Verify build_generation_prompt() returns a string."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_build_repair_prompt_returns_string(self):
        """Verify build_repair_prompt() returns a string."""
        prompt = build_repair_prompt([], ["test error"])
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_contains_multi_suffix_term(self):
        """Verify prompt contains 'Multi-Suffix' key term."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Multi-Suffix" in prompt

    def test_prompt_contains_keigo_term(self):
        """Verify prompt contains 'Keigo' key term."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Keigo" in prompt

    def test_prompt_contains_adverbial_term(self):
        """Verify prompt contains 'Adverbial' key term."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Adverbial" in prompt

    def test_prompt_contains_cross_card_consistency_term(self):
        """Verify prompt contains 'Cross-Card Consistency' key term."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Cross-Card Consistency" in prompt

    def test_prompt_contains_emotive_term(self):
        """Verify prompt contains 'Emotive' key term."""
        prompt = build_generation_prompt(
            self.get_sample_draft_cards(),
            self.get_sample_fields(),
            self.get_sample_tags()
        )
        assert "Emotive" in prompt

    def test_repair_prompt_contains_expanded_rules(self):
        """Verify build_repair_prompt() returns expanded rules."""
        prompt = build_repair_prompt([], ["test error"])
        # Check for essential rules section header
        assert "ESSENTIAL RULES" in prompt
        # Check for numbered rule sections
        assert "1. **Spacing Rules:**" in prompt
        assert "2. **Verb Form Annotations" in prompt
        assert "3. **Translation Rules:**" in prompt


class TestMultiSuffixVerbExamples:
    """Test that multi-suffix verb examples are present (lines 106-118)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_ikitakunai_example(self):
        """Check prompt contains 'ikitakunai' example."""
        prompt = self.get_prompt()
        assert "いきたくない" in prompt

    def test_contains_tabesaseraremashita_example(self):
        """Check prompt contains 'tabesaseraremashita' example."""
        prompt = self.get_prompt()
        assert "たべさせられました" in prompt

    def test_contains_ikitakuarimasen_example(self):
        """Check prompt contains 'ikitakuarimasen' example."""
        prompt = self.get_prompt()
        assert "いきたくありません" in prompt

    def test_contains_multi_suffix_rule_explanation(self):
        """Check that the rule about suffix chaining is explained."""
        prompt = self.get_prompt()
        assert "Once you attach to a verb stem, all subsequent suffixes stay attached" in prompt


class TestCompoundVerbCategories:
    """Test all 4 compound verb categories are present (lines 124-148)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_category_1_v_te_auxiliary(self):
        """Check 'V-te + auxiliary' category is present."""
        prompt = self.get_prompt()
        assert "V-て + auxiliary verbs" in prompt

    def test_category_2_v_te_motion(self):
        """Check 'V-te + motion' category is present."""
        prompt = self.get_prompt()
        assert "V-て + motion verbs" in prompt

    def test_category_3_v_stem_suffix(self):
        """Check 'V-stem + suffix' category is present."""
        prompt = self.get_prompt()
        assert "V-stem + suffix verbs" in prompt

    def test_category_4_sequential_actions(self):
        """Check 'Sequential actions' category is present."""
        prompt = self.get_prompt()
        assert "Sequential actions" in prompt

    def test_idiomatic_exception_mentioned(self):
        """Check exception for idiomatic combinations is mentioned."""
        prompt = self.get_prompt()
        assert "EXCEPTION" in prompt
        assert "idiomatic" in prompt


class TestNumberFormatRules:
    """Test number format rules with special readings (lines 124-141)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_tsuitachi(self):
        """Check 'tsuitachi' (1st of month) is listed."""
        prompt = self.get_prompt()
        assert "ついたち" in prompt

    def test_contains_hatachi(self):
        """Check 'hatachi' (20 years old) is listed."""
        prompt = self.get_prompt()
        assert "はたち" in prompt

    def test_contains_hitori(self):
        """Check 'hitori' (one person) is listed."""
        prompt = self.get_prompt()
        assert "ひとり" in prompt

    def test_contains_futari(self):
        """Check 'futari' (two people) is listed."""
        prompt = self.get_prompt()
        assert "ふたり" in prompt

    def test_contains_hatsuka(self):
        """Check 'hatsuka' (20th of month) is mentioned."""
        prompt = self.get_prompt()
        assert "はつか" in prompt

    def test_contains_nanoka(self):
        """Check 'nanoka' (7th of month) is mentioned."""
        prompt = self.get_prompt()
        assert "なのか" in prompt


class TestPhraseGreetingRules:
    """Test phrase-type card definitions with fossilized greetings (lines 181-211)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_itadakimasu(self):
        """Check 'itadakimasu' fossilized greeting is listed."""
        prompt = self.get_prompt()
        assert "いただきます" in prompt

    def test_contains_gochisousamadeshita(self):
        """Check 'gochisousamadeshita' fossilized greeting is listed."""
        prompt = self.get_prompt()
        assert "ごちそうさまでした" in prompt

    def test_contains_ittekimasu(self):
        """Check 'ittekimasu' fossilized greeting is listed."""
        prompt = self.get_prompt()
        assert "いってきます" in prompt

    def test_contains_ohayou_gozaimasu(self):
        """Check 'ohayou gozaimasu' greeting format is shown."""
        prompt = self.get_prompt()
        assert "おはよう ございます" in prompt

    def test_contains_arigatou_gozaimasu(self):
        """Check 'arigatou gozaimasu' greeting format is shown."""
        prompt = self.get_prompt()
        assert "ありがとう ございます" in prompt

    def test_fossilized_greetings_section_exists(self):
        """Check fossilized greetings section header exists."""
        prompt = self.get_prompt()
        assert "Fossilized greetings" in prompt


class TestKeigoHandling:
    """Test Keigo handling section H.1 (lines 284-312)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_irassharu(self):
        """Check honorific verb 'irassharu' is listed."""
        prompt = self.get_prompt()
        assert "いらっしゃる" in prompt

    def test_contains_ossharu(self):
        """Check honorific verb 'ossharu' is listed."""
        prompt = self.get_prompt()
        assert "おっしゃる" in prompt

    def test_contains_itasu(self):
        """Check humble verb 'itasu' is listed."""
        prompt = self.get_prompt()
        assert "いたす" in prompt

    def test_contains_mousu(self):
        """Check humble verb 'mousu' is listed."""
        prompt = self.get_prompt()
        assert "申す" in prompt

    def test_contains_mairu(self):
        """Check humble verb 'mairu' is listed."""
        prompt = self.get_prompt()
        assert "参る" in prompt

    def test_contains_honorific_annotation(self):
        """Check '(honorific)' is mentioned for translations."""
        prompt = self.get_prompt()
        assert "(honorific)" in prompt

    def test_contains_humble_annotation(self):
        """Check '(humble)' is mentioned for translations."""
        prompt = self.get_prompt()
        assert "(humble)" in prompt

    def test_keigo_section_header(self):
        """Check Keigo section header exists."""
        prompt = self.get_prompt()
        assert "Keigo" in prompt
        assert "敬語" in prompt


class TestAdverbialForms:
    """Test adverbial adjective forms section J.1 (lines 349-365)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_ookiku_example(self):
        """Check ku-form example 'ookiku' is present."""
        prompt = self.get_prompt()
        assert "おおきく" in prompt

    def test_contains_hayaku_example(self):
        """Check ku-form example 'hayaku' is present."""
        prompt = self.get_prompt()
        assert "はやく" in prompt

    def test_contains_shizukani_example(self):
        """Check ni-form example 'shizukani' is present."""
        prompt = self.get_prompt()
        assert "しずかに" in prompt

    def test_contains_kireini_example(self):
        """Check ni-form example 'kireini' is present."""
        prompt = self.get_prompt()
        assert "きれいに" in prompt

    def test_adverbial_section_header(self):
        """Check adverbial section header exists."""
        prompt = self.get_prompt()
        assert "Adverbial Adjective Forms" in prompt


class TestEmotiveAdjectives:
    """Test emotive adjectives (suki/kirai) section J.2 (lines 367-387)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_contains_suki(self):
        """Check 'suki' is mentioned."""
        prompt = self.get_prompt()
        assert "すき" in prompt

    def test_contains_kirai(self):
        """Check 'kirai' is mentioned."""
        prompt = self.get_prompt()
        assert "きらい" in prompt

    def test_contains_jouzu(self):
        """Check 'jouzu' is mentioned."""
        prompt = self.get_prompt()
        assert "じょうず" in prompt

    def test_contains_heta(self):
        """Check 'heta' is mentioned."""
        prompt = self.get_prompt()
        assert "へた" in prompt

    def test_contains_ga_particle_explanation(self):
        """Check ga particle explanation is present."""
        prompt = self.get_prompt()
        # Check for the explanation that objects take ga
        assert "が" in prompt
        # Verify there's an explanation about the ga particle usage with emotive adjectives
        assert "object takes が" in prompt or "takes が" in prompt

    def test_contains_ringo_ga_suki_example(self):
        """Check 'ringo ga suki desu' example is present."""
        prompt = self.get_prompt()
        assert "りんご が すきです" in prompt

    def test_emotive_section_header(self):
        """Check emotive section header exists."""
        prompt = self.get_prompt()
        assert "Emotive" in prompt


class TestCrossCardConsistency:
    """Test cross-card consistency section L (lines 325-348)."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_terminology_polite_form(self):
        """Check terminology standard: 'polite form' not 'masu form'."""
        prompt = self.get_prompt()
        # Check that the terminology section specifies polite form
        assert '"polite form"' in prompt
        assert 'not "masu form"' in prompt

    def test_particle_consistency_mentioned(self):
        """Check particle consistency is mentioned."""
        prompt = self.get_prompt()
        assert "Particle consistency" in prompt

    def test_dutch_annotation_beleefde_vorm(self):
        """Check Dutch annotation format '(beleefde vorm)' is specified."""
        prompt = self.get_prompt()
        assert "(beleefde vorm)" in prompt

    def test_cross_card_section_header(self):
        """Check Cross-Card Consistency section header exists."""
        prompt = self.get_prompt()
        assert "Cross-Card Consistency" in prompt


class TestRepairPromptExpanded:
    """Test expanded repair prompt with full rules (lines 400-443)."""

    def get_prompt(self):
        """Generate a repair prompt for testing."""
        return build_repair_prompt([], ["test error"])

    def test_contains_spacing_rules(self):
        """Check repair prompt contains spacing rules."""
        prompt = self.get_prompt()
        assert "Spacing Rules" in prompt

    def test_contains_verb_form_annotation_standards(self):
        """Check repair prompt contains verb form annotation standards."""
        prompt = self.get_prompt()
        assert "Verb Form Annotations" in prompt
        assert '"polite form"' in prompt
        assert 'NOT "masu form"' in prompt

    def test_contains_translation_rules_commas_not_slashes(self):
        """Check repair prompt contains translation rules (commas not slashes)."""
        prompt = self.get_prompt()
        assert "Translation Rules" in prompt
        assert "COMMAS" in prompt or "commas" in prompt.lower()
        assert "slashes" in prompt.lower() or "NEVER use slashes" in prompt

    def test_contains_fossilized_greetings_list(self):
        """Check repair prompt contains fossilized greetings list."""
        prompt = self.get_prompt()
        assert "Fossilized Greetings" in prompt
        assert "いただきます" in prompt
        assert "ごちそうさまでした" in prompt
        assert "いってきます" in prompt

    def test_contains_greetings_with_gozaimasu(self):
        """Check repair prompt contains greetings with gozaimasu rule."""
        prompt = self.get_prompt()
        assert "おはよう ございます" in prompt
        assert "ありがとう ございます" in prompt

    def test_contains_multi_suffix_examples(self):
        """Check repair prompt contains multi-suffix verb examples."""
        prompt = self.get_prompt()
        assert "いきたくない" in prompt or "たべさせられました" in prompt

    def test_contains_compound_verb_examples(self):
        """Check repair prompt contains compound verb examples."""
        prompt = self.get_prompt()
        assert "V-て + auxiliary verbs" in prompt
        assert "たべてしまいます" in prompt or "よんでおきます" in prompt

    def test_contains_punctuation_rules(self):
        """Check repair prompt contains punctuation rules."""
        prompt = self.get_prompt()
        assert "Punctuation" in prompt
        assert "。" in prompt  # Japanese period

    def test_contains_dutch_beleefde_vorm(self):
        """Check repair prompt contains Dutch annotation format."""
        prompt = self.get_prompt()
        assert "(beleefde vorm)" in prompt


class TestRepairPromptSpecificErrorFixes:
    """Test that repair prompt contains specific error fix instructions."""

    def get_prompt(self):
        """Generate a repair prompt for testing."""
        return build_repair_prompt([], ["test error"])

    def test_contains_kana_kanji_error_fix(self):
        """Check repair prompt addresses kana field containing kanji errors."""
        prompt = self.get_prompt()
        assert "kana field contains kanji" in prompt.lower() or "kanji to hiragana" in prompt.lower()

    def test_contains_sentence_ending_fix(self):
        """Check repair prompt addresses sentence ending errors."""
        prompt = self.get_prompt()
        assert '。' in prompt  # Japanese period
        assert "end with" in prompt.lower() or "must end" in prompt.lower()

    def test_contains_auto_classified_type_fix(self):
        """Check repair prompt addresses auto_classified_type requirement."""
        prompt = self.get_prompt()
        assert "auto_classified_type" in prompt


class TestPromptContentIntegrity:
    """Test overall prompt content integrity and completeness."""

    def get_prompt(self):
        """Generate a prompt for testing."""
        draft_cards = [{"raw_input": "test", "fixed_english": None, "fixed_dutch": None, "extra_notes": None, "card_type_override": None}]
        return build_generation_prompt(draft_cards, ["Field1"], ["word"])

    def test_section_d1_exists(self):
        """Check section D.1 (Spacing Rules) exists."""
        prompt = self.get_prompt()
        assert "D.1)" in prompt or "SPACING RULES" in prompt

    def test_section_h1_exists(self):
        """Check section H.1 (Keigo Handling) exists."""
        prompt = self.get_prompt()
        assert "H.1)" in prompt

    def test_section_j1_exists(self):
        """Check section J.1 (Adverbial Adjective Forms) exists."""
        prompt = self.get_prompt()
        assert "J.1)" in prompt

    def test_section_j2_exists(self):
        """Check section J.2 (Emotive adjectives) exists."""
        prompt = self.get_prompt()
        assert "J.2)" in prompt

    def test_section_l_exists(self):
        """Check section L (Cross-Card Consistency) exists."""
        prompt = self.get_prompt()
        assert "### L)" in prompt

    def test_all_major_sections_present(self):
        """Verify all major section headers A through L are present."""
        prompt = self.get_prompt()
        expected_sections = ["### A)", "### B)", "### C)", "### D)", "### E)",
                           "### F)", "### G)", "### H)", "### I)", "### J)", "### K)", "### L)"]
        for section in expected_sections:
            assert section in prompt, f"Missing section: {section}"
