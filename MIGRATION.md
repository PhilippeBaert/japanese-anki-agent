# Anki Note Migration Guide

Migrate old notes from "Philippe's Japanese v3" to "Japanese Vocabulary (Agent)" format while preserving scheduling and review history.

## Prerequisites

1. **AnkiConnect add-on** installed in Anki (add-on code: `2055492159`)
2. **Anki running** during migration
3. **Backend running** at `localhost:8000`
4. **"Japanese Vocabulary (Agent)" note type** exists in Anki

## Important: Change Note Type First

**Before using the migration tool, you must change the note type in Anki.**

The migration tool updates field *content*, but cannot change the note type itself. If you skip this step, updates will silently fail because the field names won't match.

### Step-by-step:

1. Open **Anki** → **Browse**
2. In the search bar, filter by deck: `deck:"Japanse les - jaar 1::Les 01"` (or your deck name)
3. Select all notes (Ctrl+A / Cmd+A)
4. Go to **Notes** → **Change Note Type...**
5. Set:
   - **Current Note Type**: Philippe's Japanese v3
   - **New Note Type**: Japanese Vocabulary (Agent)
6. Map the fields:

| Old Field (Philippe's Japanese v3) | New Field (Japanese Vocabulary Agent) |
|------------------------------------|---------------------------------------|
| Kana                               | Hiragana/Katakana                     |
| Romaji                             | Romaji                                |
| Kanji                              | Kanji                                 |
| English                            | English                               |
| Nederlands                         | Dutch                                 |
| Example                            | Example sentence hiragana/katakana    |
| Example Kanji                      | Example sentence kanji                |
| Example translation                | Example sentence translation          |
| Extra                              | Extra notes                           |
| Sound                              | Sound                                 |
| Sound Example                      | Sound example                         |

7. Click **OK**

**This preserves all scheduling data** because the note IDs remain unchanged.

## Using the Migration Tool

1. Start the backend:
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```

2. Start the frontend:
   ```bash
   cd frontend && npm run dev
   ```

3. Navigate to http://localhost:3000/migrate

4. **Select a deck** from the dropdown

5. For each note:
   - **Left side**: Original field values (read-only)
   - **Right side**: AI-regenerated preview (editable)
   - **Regenerate**: Get a fresh AI preview
   - **Skip**: Leave this note unchanged
   - **Approve**: Commit changes to Anki

## What the Migration Tool Does

- Reads your existing kana/kanji as input
- Passes your existing English/Dutch translations as "fixed" values (preserved)
- Generates improved content via Claude AI:
  - Proper spacing in kana fields
  - Correct romaji (Hepburn)
  - Example sentences for words/phrases
  - Consistent formatting
- Preserves your Sound field references
- Updates the note in Anki when you click Approve

## What Gets Preserved

- **Scheduling**: Intervals, due dates, ease factors
- **Review history**: All past reviews remain intact
- **Sound files**: Original `[sound:...]` references kept (both word and example sentence audio)
- **Your translations**: English/Dutch you provided stay (placed first)

## Troubleshooting

### "Approved but nothing changed"
You likely haven't changed the note type yet. See "Change Note Type First" above.

### "Cannot connect to AnkiConnect"
- Make sure Anki is running
- Install AnkiConnect add-on (code: `2055492159`)
- Restart Anki after installing

### "No decks found"
The tool looks for notes with "Philippe's Japanese v3" note type. If you've already changed all notes to the new type, there's nothing to migrate.

## Batch Processing Multiple Decks

Repeat the process for each lesson deck:
1. Change note type in Anki for that deck
2. Select the deck in the migration tool
3. Process each note (Approve/Skip)
4. Move to next deck
