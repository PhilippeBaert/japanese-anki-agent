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

3. **sentence**: Complete sentences or utterances that stand alone
   - Has a verb ending (です/ます/だ/plain verb forms)
   - OR is a request form: 〜てください, 〜てくれ, 〜ないでください
   - OR is a command/invitation: 〜ましょう, 〜なさい
   - OR is a polite expression with ください: おねがいします, ちょっとまってください
   - May contain topic marker (は/が) but not required for requests/commands
   - Examples:
     - "shukudai wa kantan desu" (statement)
     - "kaite kudasai" (request - please write)
     - "tabemasen ka" (invitation - won't you eat?)
     - "ikimashō" (suggestion - let's go)
   - Key test: Could stand alone as a complete utterance (statement, request, command, or question)

**IMPORTANT: If card_type_override is provided (not null), use that classification for all purposes:
- Use it for tags (e.g., ["phrase"])
- Use it for auto_classified_type (this field contains the FINAL classification used, whether auto-detected or overridden)
- Apply the appropriate example sentence and formatting rules for that type**

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

**Multi-Suffix Verb Forms:**
When multiple suffixes chain together, keep the ENTIRE verb complex as one unit:
- Negative desire: "いきたくない" NOT "いき たくない" (want to go + negative)
- Polite negative desire: "いきたくありません" NOT "いきたく ありません"
- Causative-passive: "たべさせられました" NOT "たべ させられました"
- Te-form + auxiliary + suffix: "よんでおきたい" NOT "よんで おきたい"

RULE: Once you attach to a verb stem, all subsequent suffixes stay attached.
The only break point is BEFORE particles (は、が、を、etc.) or separate words.

Examples:
- "ほん を よみたくありません。" (don't want to read the book)
- "せんせい に たべさせられました。" (was made to eat by teacher)

- Numbers + counters: stay together
  - Correct: "3にん" NOT "3 にん"
  - Correct: "9じ" NOT "9 じ"

**Number Format Rules:**

1. **Special readings** (MUST use these):
   - 一日 → "ついたち" (1st of month) or "いちにち" (one day) - context dependent
   - 二十歳 → "はたち" (NOT にじゅっさい)
   - 一人 → "ひとり" (NOT いちにん)
   - 二人 → "ふたり" (NOT ににん)
   - 二十日 → "はつか" (20th of month)
   - 七日 → "なのか" (7th of month)

2. **In kana-only fields:**
   - Hiragana preferred: "さんにん", "くじ", "にじゅっさい"
   - Arabic numerals acceptable for clarity: "3にん", "9じ"
   - Keep number+counter as one unit (no space): "さんにん" or "3にん"
   - Time with half: "くじはん" or "9じはん" (no space)

3. **Consistency within a card:**
   - Pick one format (hiragana or Arabic) and use it consistently within the same card

**Compound Verbs and Auxiliaries (keep together):**
1. **V-て + auxiliary verbs** (grammatical function): always one unit
   - てしまう (completion): "たべてしまいます"
   - ておく (preparation): "よんでおきます"
   - ている (continuous): "みています"
   - てある (resultant state): "かいてあります"
   - てみる (trying): "たべてみます"
   - てあげる/もらう/くれる (giving/receiving): "おしえてあげます"

2. **V-て + motion verbs** (directional): always one unit
   - てくる (coming): "もってきます"
   - ていく (going): "もっていきます"

3. **V-stem + suffix verbs** (compound verbs): always one unit
   - はじめる (begin): "たべはじめます"
   - おわる (finish): "よみおわります"
   - すぎる (excess): "たべすぎます"
   - やすい/にくい (ease/difficulty): "よみやすい", "わかりにくい"

4. **Sequential actions** (multiple distinct events): SEPARATE with spaces
   - "たべて ねます" (eat and then sleep) - two distinct actions

   EXCEPTION: If the combination is idiomatic (single concept), keep together:
   - "いってきます" (I'm leaving and coming back - greeting)
   - "いってかえってくる" (go and return - single round trip concept)

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

1. **Set greetings with ございます** - space before ございます:
   - "おはよう ございます" (good morning)
   - "ありがとう ございます" (thank you)
   - "おめでとう ございます" (congratulations)

2. **Fossilized greetings** - keep as single unit (no spaces):
   - "いただきます" (before eating)
   - "ごちそうさまでした" (after eating)
   - "いってきます" (leaving home)
   - "いってらっしゃい" (seeing someone off)
   - "ただいま" (I'm home)
   - "おかえりなさい" (welcome back)
   - "おつかれさまです" (good work)
   - "おやすみなさい" (good night)
   - "すみません" (sorry/excuse me)

3. **Greetings with でした/です suffix** - space before the copula:
   - "すみません でした" (I was sorry)
   - "ごめんなさい" (single unit - sorry)

4. **Descriptive phrases** - space between distinct concepts:
   - "あかい りんご" (red apple)
   - "わたし の ともだち" (my friend)
   - "とても おいしい" (very delicious)

5. **Decision test for phrases:**
   - Is this a fossilized/set greeting? → Keep as one unit
   - Does it end with ございます? → Space before ございます
   - Otherwise, separate distinct words with spaces

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
    - Section H verb form annotations: if input is a SINGLE-WORD conjugated verb (card type "word"),
      BOTH English and Dutch must have the form annotation (e.g., "polite form" for English,
      "beleefde vorm" for Dutch), even if the fixed translation didn't include it.
      This rule does NOT apply to phrase or sentence cards.
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

### H.1) Keigo (敬語) Handling

**Preserve keigo forms - do NOT convert to plain polite:**

1. **Honorific verbs** (尊敬語 - sonkeigo) - used for actions of respected people:
   - いらっしゃる → "いらっしゃいます" (NOT います) - to be, to go, to come
   - おっしゃる → "おっしゃいます" (NOT いいます) - to say
   - ご覧になる → "ご覧になります" (NOT みます) - to see
   - 召し上がる → "召し上がります" (NOT たべます) - to eat, to drink
   - なさる → "なさいます" (NOT します) - to do

2. **Humble verbs** (謙譲語 - kenjougo) - used for speaker's own actions:
   - いたす → "いたします" (NOT します) - to do
   - 申す → "もうします" (NOT いいます) - to say
   - 参る → "まいります" (NOT いきます) - to go, to come
   - おる → "おります" (NOT います) - to be
   - いただく → "いただきます" (NOT もらいます) - to receive

3. **Respectful prefixes** (お/ご):
   - Preserve when present in input: おみず, ごかぞく, おなまえ
   - Do NOT add if not in input

**In translations and extra notes for keigo words:**
- English: mark with "(honorific)" or "(humble)"
- Dutch: mark with "(eerbiedig)" or "(nederig)"
- Extra notes MUST explain: the keigo type, plain equivalent, and usage context
- Example for いらっしゃいます:
  - English: "to be, to go, to come (honorific polite)"
  - Extra notes: "Honorific form of いる/いく/くる. Used when speaking about someone of higher status."

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
- **If user provided extra notes**: Use them as a STARTING POINT, not the complete content:
  - Translate to English if in another language
  - Fix any typos or spelling errors
  - STILL apply all rules above (verb type, adjective type, grammar explanations, etc.)
  - Extend with additional helpful information as needed
  - You may modify or correct the user's notes if they are inaccurate or incomplete
- Ensure proper formatting:
  - Each sentence starts with a capital letter
  - Each sentence ends with a period
- Use newlines (\\n) to separate distinct pieces of information, for example:
  - Literal translation on one line, alternative expression on another
  - Example: "Literally: \\"As for pencils, I have one.\\"\\n\\"Hitotsu no enpitsu ga arimasu\\" can also be used."
- Keep notes helpful but concise

### J.1) Adverbial Adjective Forms

If the input is an ADVERBIAL form of an adjective, handle as follows:

1. **い-adjective adverbs** (く-form):
   - おおきく → "greatly, largely" (NOT "big")
   - はやく → "quickly, fast" (NOT "fast, early")
   - たかく → "highly, expensively" (NOT "high, expensive")
   - Extra notes: "Adverbial form of 大きい (big). Used to modify verbs: 大きくなる (become big)."

2. **な-adjective adverbs** (に-form):
   - しずかに → "quietly" (NOT "quiet")
   - きれいに → "beautifully, cleanly" (NOT "beautiful, clean")
   - かんたんに → "easily, simply" (NOT "easy, simple")
   - Extra notes: "Adverbial form of 静か (quiet). Used to modify verbs: 静かに話す (speak quietly)."

Translation MUST reflect adverbial meaning (use English -ly form or equivalent).

### J.2) Emotive な-adjectives (すき, きらい, じょうず, へた)

These adjectives express feelings/abilities ABOUT something and have special grammar.

1. **Translation options:**
   - Verb-like style acceptable for natural English: "to like", "to dislike"
   - Adjective style also acceptable: "fond of", "good at"

2. **Critical grammar note in Extra notes:**
   - MUST explain that the object takes が (not を)
   - Example for すき:
     - English: "to like, to be fond of"
     - Dutch: "houden van, leuk vinden"
     - Extra notes: "な-adjective expressing liking. The liked object takes が: りんご が すきです (I like apples). Modifying form: すきな (e.g., すきな たべもの - favorite food)."

3. **Related adjectives requiring same treatment:**
   - すき (like) - が marks liked thing
   - きらい (dislike) - が marks disliked thing
   - じょうず (skillful at) - が marks skill area
   - へた (bad at) - が marks skill area
   - ほしい (want) - が marks wanted thing (note: this is an い-adjective)

### K) Sound Fields
- Leave the "Sound" field empty (word/phrase audio added manually)
- Leave the "Sound example" field empty (sentence audio added manually)
- Design note: Sound fields are always empty for new cards. Audio is added manually
  after import. For migration, existing sounds are preserved from old cards.

### L) Cross-Card Consistency (For Batch Generation)

When generating multiple cards in a single request, maintain consistency:

1. **Terminology (always use these exact terms):**
   - "polite form" (not "masu form", "formal form", or "desu/masu form")
   - "plain form" (not "dictionary form", "casual form", or "informal form")
   - "te-form" (not "te form", "-te form", or "conjunctive form")
   - "negative form" (not "negative", "nai form")
   - い-adjective (not "i-adjective", "adjective-i")
   - な-adjective (not "na-adjective", "adjective-na")

2. **Translation consistency:**
   - Use the same English/Dutch translation for the same Japanese word across all cards in the batch
   - If おいしい appears in multiple cards, always translate it the same way

3. **Particle consistency:**
   - Default to に for direction/destination (not へ) unless へ is specifically in the input
   - Be consistent with particle choices across similar sentences in the batch

4. **Dutch annotation format:**
   - Always "(beleefde vorm)" for polite form (not "(beleefd)" or "(formeel)")
   - Always "(gebiedende wijs)" for imperative
   - Always "(て-vorm)" for te-form

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

**ESSENTIAL RULES (Apply to ALL repairs):**

1. **Spacing Rules:**
   - ADD SPACE BEFORE particles: は、が、を、に、で、と、も、へ、から、まで、より、など
   - DO NOT add space before verb endings: ます、ません、ました、ている、てください、たい、ない
   - Multi-suffix verbs stay together: "いきたくない", "たべさせられました", "よんでおきたい"
   - Compound verbs stay together: "よんでいます", "もってきます", "たべてしまいます"
   - V-て + auxiliary verbs stay together: "たべてしまいます", "よんでおきます", "みています"
   - Sequential actions get spaces: "たべて ねます" (eat then sleep)
   - Numbers + counters stay together: "3にん", "9じ", "9じはん", "さんにん"
   - Separate nouns from nouns: "わたし の ともだち"
   - Separate adjectives from nouns: "おおきい いぬ"

2. **Verb Form Annotations (use these exact terms):**
   - "polite form" (NOT "masu form")
   - "plain form" (NOT "dictionary form")
   - "te-form" (NOT "te form" or "-te form")
   - "negative form", "past form", "conditional form", etc.
   - BOTH English AND Dutch translations need verb form annotations for conjugated verbs

3. **Translation Rules:**
   - Use COMMAS to separate multiple translations: "to eat, to consume"
   - NEVER use slashes: NOT "to eat/consume"
   - Dutch verbs need "(beleefde vorm)" annotation for polite forms

4. **Punctuation:**
   - All Japanese sentences MUST end with 。(Japanese period)
   - NOT . (Western period)

5. **Fossilized Greetings (keep as single unit):**
   - いただきます, ごちそうさまでした, いってきます, いってらっしゃい
   - おかえりなさい, おつかれさまです, すみません, おやすみなさい

6. **Greetings with ございます (space before ございます):**
   - おはよう ございます, ありがとう ございます, おめでとう ございます

**SPECIFIC ERROR FIXES:**
1. For "kana field contains kanji" errors: Convert all kanji to hiragana/katakana following the spacing rules above
2. For "sentence must end with 。" errors: Add 。 to the end
3. For "kanji field should be empty" errors: Set the Kanji field to empty string ""
4. Ensure each card has "auto_classified_type" field with value "word", "phrase", or "sentence"
5. Keep all other fields unchanged unless they violate the rules above

Respond with ONLY the corrected JSON in the same format:
{{
  "cards": [...]
}}'''
