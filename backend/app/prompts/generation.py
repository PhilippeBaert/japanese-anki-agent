"""Prompt engineering for Anki card generation."""

from typing import Optional


def build_generation_prompt(
    draft_cards: list[dict],
    fields: list[str],
    tags: list[str]
) -> str:
    """Build the full prompt for the Claude agent to generate Anki cards."""

    cards_json = "\n".join([
        f"""Card {i+1}:
- raw_input: "{card['raw_input']}"
- fixed_english: {f'"{card["fixed_english"]}"' if card.get('fixed_english') else 'null'}
- fixed_dutch: {f'"{card["fixed_dutch"]}"' if card.get('fixed_dutch') else 'null'}
- extra_notes: {f'"{card["extra_notes"]}"' if card.get('extra_notes') else 'null'}
- card_type_override: {f'"{card["card_type_override"]}"' if card.get('card_type_override') else 'null'}"""
        for i, card in enumerate(draft_cards)
    ])

    fields_list = "\n".join([f"- {field}" for field in fields])

    return f'''You are an expert Japanese language instructor creating Anki flashcards.

## Your Task
Generate complete Anki flashcard data for each input provided below.
**You MUST also classify each input as "word", "phrase", or "sentence".**

## Output Fields (in this exact order):
{fields_list}

## Critical Generation Rules

### A) Card Type Classification - CRITICAL RULE

**You MUST classify each input into one of three types:**

1. **word**: A single word OR compound words that represent ONE English concept
   - Single words: "hon" (book), "ookii" (big), "taberu" (to eat), "kantan" (easy)
   - Compound concepts that translate to ONE word/concept in English:
     - "toukei gakusha" → "statistician" (one concept = word)
     - "daigakusei" → "university student" (one concept = word)
     - "kinou" → "yesterday" (one concept = word)
   - Key test: Would this translate to a single word or single concept in English?

2. **phrase**: Multiple words that form a descriptive unit but NOT a complete sentence
   - Adjective + noun: "aoi ie" (blue house), "kantan na shukudai" (easy homework)
   - Noun phrases: "watashi no tomodachi" (my friend), "ookii neko" (big cat)
   - Key test: No predicate/verb ending, just a descriptive grouping of multiple concepts

3. **sentence**: Complete sentences with a predicate
   - Has a verb ending (です/ます/だ/plain verb forms at the end)
   - Contains topic marker (は/が) with a complete predicate
   - Examples: "shukudai wa kantan desu", "watashi wa nihongo wo benkyou shimasu"
   - Key test: Could stand alone as a complete thought with a verb

**IMPORTANT: If card_type_override is provided (not null), use that classification instead of auto-detecting.**

### B) Example Sentence Rules Based on Classification

**WHEN TYPE IS "sentence":**
- The main fields contain the sentence itself
- **LEAVE ALL THREE EXAMPLE SENTENCE FIELDS COMPLETELY EMPTY:**
  - "Example sentence hiragana/katakana": "" (empty string)
  - "Example sentence kanji": "" (empty string)
  - "Example sentence translation": "" (empty string)
- WHY: The sentence IS the example - don't duplicate it!

**WHEN TYPE IS "word" OR "phrase":**
- Generate exactly ONE simple beginner-friendly example sentence in polite Japanese
- **ALL THREE EXAMPLE SENTENCE FIELDS MUST BE FILLED (not empty)**
- The example should demonstrate natural usage of the word/phrase

### C) Polite Japanese + Punctuation
- ALL Japanese sentences MUST be in polite style (です/ます form)
- ALL Japanese sentences MUST end with Japanese full stop: 。 (NOT a period)

### D) Kana-Only Fields (NO KANJI ALLOWED)
- "Hiragana/Katakana" field: ONLY kana, NO kanji
  - Use katakana for loanwords (e.g., オランダ, コンピュータ)
  - Use hiragana for native Japanese words
- "Example sentence hiragana/katakana": ONLY kana, NO kanji
  - Use SPACES between words for readability
  - Keep katakana words in katakana, everything else in hiragana
  - Examples: "オランダ に すんでいます。" or "ふつう でんしゃ で いきます。"

### D.1) SPACING RULES FOR KANA FIELDS (CRITICAL)
Use spaces to separate logical units for readability. Follow these rules:

**ADD SPACE BEFORE:**
- Particles: は、が、を、に、で、と、も、へ、から、まで、より、など
  - Example: "わたし は ほん を よみます。" (I read a book)
  - Example: "がっこう に いきます。" (I go to school)

**DO NOT ADD SPACE (keep attached):**
- Verb endings and suffixes: ます、ません、ました、ている、てください、たい、ない
  - Correct: "たべます" NOT "たべ ます"
  - Correct: "よんでいます" NOT "よんで います"
  - Correct: "いきたい" NOT "いき たい"
- Numbers + counters: stay together
  - Correct: "3にん" NOT "3 にん"
  - Correct: "9じ" NOT "9 じ"
- Compound verbs: stay together
  - Correct: "もってきます" NOT "もって きます"

**SEPARATE WITH SPACE:**
- Nouns from other nouns: "わたし の ともだち"
- Adjectives from nouns: "おおきい いぬ" (big dog)
- Adverbs from verbs: "はやく たべます" (eat quickly)
- Multiple adjectives: "あかい おおきい くるま" (red big car)

**SPACING EXAMPLES:**
- "きょう は 9じ に ねます。" (Today I sleep at 9)
- "わたし の ともだち は オランダ に すんでいます。" (My friend lives in the Netherlands)
- "おおきい いぬ が います。" (There is a big dog)
- "ほん を よんでいます。" (I am reading a book)

**FOR PHRASE-TYPE CARDS - MAIN KANA FIELD:**
- The spacing rules above ALSO apply to the main "Hiragana/Katakana" field for phrase-type cards
- Separate distinct words/components with spaces, even without particles
- Examples:
  - "akemashite omedetou" → "あけまして おめでとう" (NOT "あけましておめでとう")
  - "ohayou gozaimasu" → "おはよう ございます"
  - "yoroshiku onegaishimasu" → "よろしく おねがいします"
- This makes phrases readable and shows word boundaries clearly

### E) Kanji Fields
- "Kanji" field:
  - Provide the standard kanji spelling if one exists
  - If no kanji exists (e.g., katakana loanwords), leave EMPTY (not "N/A" or "none")
- "Example sentence kanji":
  - Write the sentence with proper kanji where standard
  - Do NOT use spaces (write like real Japanese)
  - End with 。

### F) Romaji (Hepburn Romanization)
- Use Hepburn system consistently
- Long vowels: use "ou" for おう (e.g., とうきょう → toukyou), "oo" for おお where standard (e.g., おおきい → ookii)
- "ei" stays "ei" (e.g., せんせい → sensei)
- Katakana long vowel mark ー: reflect appropriately (e.g., ベルギー → berugii)
- Use: shi, chi, tsu, fu

### F.1) User Input Romanization for Particles
- When parsing user input (raw_input), accept alternate romanizations for particles:
  - "wa" should be interpreted as the topic particle は (not わ) when used as a particle
  - "o" should be interpreted as the object particle を (not お) when used as a particle
- Examples:
  - User input "watashi wa" → わたしは (私は)
  - User input "hon o yomu" → ほんをよむ (本を読む)
- In output Romaji field, continue using standard Hepburn romanization (wa, o for these particles)

### G) Translation Rules with Fixed Translations
- Generate both English and Dutch translations
- **ALL translations must use COMMA as separator** (never use "/" to separate alternatives)
- If user provided a fixed translation, treat it as a STARTING POINT, not a hard constraint:
  - Fix any typos or spelling errors
  - Ensure proper capitalization (start with capital letter)
  - For full sentence translations: ensure they end with a period
  - For single words/phrases: no period needed
  - **Convert any "/" separators to commas** for consistency
  - **IMPORTANT: Still apply ALL other rules from this prompt** - especially:
    - Section H verb form annotations: if input is a conjugated verb, BOTH English and Dutch
      must have the form annotation (e.g., "polite form" / "beleefde vorm"), even if the
      fixed translation didn't include it
    - If the fixed translation is plainly wrong or misleading, correct it
  - Place the (corrected/enhanced) fixed term FIRST, then add additional translations after, comma-separated
  - Example: fixed Dutch "juist-teken" → "Juist-teken, correct teken, cirkel"
  - Example: fixed English "to read / peruse" → "To read, peruse" (/ converted to comma)
  - Example: fixed English "to read (masu form)" with fixed Dutch "lezen" for よみます
    → English: "To read (polite form)" and Dutch: "Lezen (beleefde vorm)"
    (annotation added to Dutch to match verb form rules)
- If user only fixed one language, generate the other normally but ensure BOTH comply with all rules

### H) Verb Form Translations
When the input is a VERB (single word), handle the form as follows:

**Dictionary form** (base form ending in -u: taberu, nomu, kiku, iku):
- Translate with simple infinitive, NO form annotation
- English: "to eat", "to drink", "to listen", "to go"
- Dutch: "eten", "drinken", "luisteren", "gaan"

**Other verb forms** - add form name in brackets after translation:
- **Polite form** (ます form: tabemasu, nomimasu):
  - English: "eat (polite form)" or "to eat (polite form)"
  - Dutch: "eten (beleefde vorm)"
- **Plain negative form** (ない form: tabenai, nomanai):
  - English: "not eat (plain negative form)"
  - Dutch: "niet eten (gewone ontkennende vorm)"
- **Plain past form** (た form: tabeta, nonda):
  - English: "ate (plain past form)"
  - Dutch: "at (gewone verleden tijd)"
- **Te form** (て form: tabete, nonde):
  - English: "eating (te form)" - used for requests, continuous, connecting
  - Dutch: "etend (te-vorm)"
- **Other forms**: follow the same pattern - translate appropriately and add form name in brackets

### I) Example Sentence Translation
- "Example sentence translation" must be in ENGLISH

### J) Extra Notes
- **For SENTENCE-type cards: ALWAYS add extra notes** explaining:
  - Grammar points used (e.g., polite form, te-form, etc.)
  - Particles and their function (e.g., を marks the direct object, は marks the topic)
  - Verb forms and conjugations
  - Any other helpful linguistic information
- **For WORD-type cards:**
  - If the word is a VERB: MUST include the verb type in extra notes:
    - "う-verb" (also called godan/Group 1) - e.g., 飲む, 書く, 話す
    - "る-verb" (also called ichidan/Group 2) - e.g., 食べる, 見る, 寝る
    - "Irregular verb" - する and 来る (くる)
  - If the word is an ADJECTIVE: MUST include the adjective type in extra notes:
    - "い-adjective" - e.g., 大きい, 寒い, 美味しい
    - "な-adjective" - e.g., 静か, 綺麗, 簡単
  - **The type classification should come first, but you can (and should) add more helpful notes after it.**
    - Example for うまい: "い-adjective. Informal/casual way to say 'delicious.' Can also mean 'skillful' or 'good at something.'"
    - Example for できる: "る-verb. Potential form of する. Means 'to be able to do' or 'to be completed.'"
  - **Note irregular conjugations** when applicable:
    - Example for いい: "い-adjective (irregular). Conjugates with よ- stem: よくない (negative), よかった (past)."
    - Example for かっこいい: "い-adjective (irregular). Conjugates with よ- stem: かっこよくない, かっこよかった."
  - For other word types (nouns, adverbs, etc.): MAY add extra notes if helpful
- For PHRASE-type cards: You MAY add extra notes if helpful (e.g., literal translations, usage notes)
- If user provided extra notes, rewrite them into clear, concise English
- Fix any typos or spelling errors
- Ensure proper formatting:
  - Each sentence starts with a capital letter
  - Each sentence ends with a period
- Use newlines (\\n) to separate distinct pieces of information, for example:
  - Literal translation on one line, alternative expression on another
  - Example: "Literally: \\"As for pencils, I have one.\\"\\n\\"Hitotsu no enpitsu ga arimasu\\" can also be used."
- Keep notes helpful but concise

### K) Sound Fields
- Leave the "Sound" field empty (word/phrase audio added manually)
- Leave the "Sound example" field empty (sentence audio added manually)
- Design note: Sound fields are always empty for new cards. Audio is added manually
  after import. For migration, existing sounds are preserved from old cards.

## Input Cards to Process:

{cards_json}

## Output Format
Respond with ONLY valid JSON in this exact structure:
{{
  "cards": [
    {{
      "fields": {{
        "Hiragana/Katakana": "...",
        "Romaji": "...",
        "Kanji": "...",
        "English": "...",
        "Dutch": "...",
        "Example sentence hiragana/katakana": "...",
        "Example sentence kanji": "...",
        "Example sentence translation": "...",
        "Extra notes": "...",
        "Sound": "",
        "Sound example": ""
      }},
      "tags": ["word"],
      "auto_classified_type": "word"
    }}
  ]
}}

**CRITICAL**: Each card MUST include:
- "tags": array containing the classified type (e.g., ["word"], ["phrase"], or ["sentence"])
- "auto_classified_type": string with the classification ("word", "phrase", or "sentence")

Generate one card object for each input.'''


def build_repair_prompt(original_cards: list[dict], errors: list[str]) -> str:
    """Build a prompt to repair invalid generated cards."""

    import json
    cards_json = json.dumps(original_cards, ensure_ascii=False, indent=2)
    errors_list = "\n".join([f"- {error}" for error in errors])

    return f'''The following generated Anki cards have validation errors that need to be fixed.

## Errors Found:
{errors_list}

## Original Cards (with errors):
{cards_json}

## Repair Instructions:
1. Fix each error while preserving correct data
2. For "kana field contains kanji" errors: Convert all kanji to hiragana/katakana
3. For "sentence must end with 。" errors: Add 。 to the end
4. For "kanji field should be empty" errors: Set the Kanji field to empty string ""
5. Ensure each card has "auto_classified_type" field with value "word", "phrase", or "sentence"
6. Keep all other fields unchanged

Respond with ONLY the corrected JSON in the same format:
{{
  "cards": [...]
}}'''
