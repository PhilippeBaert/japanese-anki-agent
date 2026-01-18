"""Migration endpoints for migrating old Anki notes to the new format."""

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from ..models import DraftCard, GeneratedCard, CardType
from ..config import load_config
from ..services.agent import generate_cards_with_agent, CardGenerationError
from ..services.anki_connect import (
    get_anki_client,
    AnkiConnectError,
    DeckInfo,
    NoteInfo,
)
from ..auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migrate", tags=["migrate"])

# Note type names - could be made configurable
OLD_NOTE_TYPE = "Philippe's Japanese v3"
NEW_NOTE_TYPE = "Japanese Vocabulary (Agent)"

# Regex pattern for validating deck names - allows alphanumeric, spaces, and basic punctuation
# This prevents injection of Anki query operators and special characters
DECK_NAME_PATTERN = r"^[\w\s\-_.,'():/]+$"


def escape_anki_query_value(value: str) -> str:
    """Escape special characters for safe use in Anki search queries.

    Anki's search syntax uses quotes and backslashes as special characters.
    This function escapes them to prevent query injection attacks.

    Args:
        value: The raw string value to escape

    Returns:
        The escaped string safe for use in quoted Anki query values
    """
    # First escape backslashes, then escape double quotes
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    return escaped

# Field mapping from old to new format
# Design note: "Nederlands" → "Dutch" - the old format used Dutch language naming ("Nederlands"),
# while the new format uses English ("Dutch") for consistency with other field names.
# "Sound Example" → "Sound example" - standardized casing (capital S, lowercase e).
FIELD_MAPPING = {
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


# Response models
class DecksResponse(BaseModel):
    """Response containing list of decks."""
    decks: list[DeckInfo]


class MigrationNote(BaseModel):
    """A note ready for migration."""
    note_id: int
    old_fields: dict[str, str]
    sound: str = ""
    sound_example: str = ""


class NotesResponse(BaseModel):
    """Response containing notes from a deck."""
    notes: list[MigrationNote]
    total: int


class PreviewRequest(BaseModel):
    """Request to generate a preview of a migrated note."""
    note_id: int
    raw_input: str = Field(..., description="Kana input for the agent")
    fixed_english: Optional[str] = None
    fixed_dutch: Optional[str] = None
    extra_notes: Optional[str] = None
    preserve_sound: Optional[str] = None
    preserve_sound_example: Optional[str] = None


class PreviewResponse(BaseModel):
    """Response with the preview of regenerated fields."""
    note_id: int
    new_fields: dict[str, str]
    auto_classified_type: CardType


# Batch preview models
class BatchPreviewItem(BaseModel):
    """Single item in a batch preview request."""
    model_config = {"populate_by_name": True}

    note_id: int = Field(alias="noteId")
    raw_input: str = Field(alias="rawInput")
    fixed_english: Optional[str] = Field(default=None, alias="fixedEnglish")
    fixed_dutch: Optional[str] = Field(default=None, alias="fixedDutch")
    extra_notes: Optional[str] = Field(default=None, alias="extraNotes")
    preserve_sound: Optional[str] = Field(default=None, alias="preserveSound")
    preserve_sound_example: Optional[str] = Field(default=None, alias="preserveSoundExample")


class BatchPreviewRequest(BaseModel):
    """Request to generate previews for multiple notes at once."""
    items: list[BatchPreviewItem] = Field(..., min_length=1, max_length=10)


class BatchPreviewItemResult(BaseModel):
    """Result for a single item in a batch preview."""
    note_id: int
    success: bool
    new_fields: Optional[dict[str, str]] = None
    auto_classified_type: Optional[CardType] = None
    error: Optional[str] = None


class BatchPreviewResponse(BaseModel):
    """Response containing results for all items in the batch."""
    results: list[BatchPreviewItemResult]
    successful_count: int
    failed_count: int


class ApproveRequest(BaseModel):
    """Request to approve and commit a migrated note."""
    note_id: int
    new_fields: dict[str, str]
    tags: list[str] = Field(default_factory=list)


class ApproveResponse(BaseModel):
    """Response after approving a note."""
    success: bool
    note_id: int


class ConnectionResponse(BaseModel):
    """Response for connection check."""
    connected: bool
    message: str


@router.get("/check-connection", response_model=ConnectionResponse)
async def check_anki_connection() -> ConnectionResponse:
    """Check if AnkiConnect is available.

    Returns:
        ConnectionResponse indicating if Anki is connected
    """
    client = get_anki_client()
    try:
        await client.check_connection()
        return ConnectionResponse(connected=True, message="Connected to AnkiConnect")
    except AnkiConnectError as e:
        return ConnectionResponse(connected=False, message=str(e))


@router.get("/decks", response_model=DecksResponse, dependencies=[Depends(verify_api_key)])
async def get_migration_decks() -> DecksResponse:
    """Get all decks containing notes with the old note type.

    Returns:
        DecksResponse with list of decks and their note counts
    """
    client = get_anki_client()

    try:
        decks = await client.get_decks_with_note_type(OLD_NOTE_TYPE)
        return DecksResponse(decks=decks)
    except AnkiConnectError as e:
        logger.error(f"AnkiConnect error getting decks: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot communicate with Anki: {e}"
        )


@router.get("/notes", response_model=NotesResponse, dependencies=[Depends(verify_api_key)])
async def get_notes_for_migration(
    deck: str = Query(
        ...,
        description="Deck name to get notes from",
        min_length=1,
        max_length=255,
        pattern=DECK_NAME_PATTERN,
    )
) -> NotesResponse:
    """Get all notes from a deck that need migration.

    Args:
        deck: Name of the deck to fetch notes from

    Returns:
        NotesResponse with list of notes and their old field values
    """
    client = get_anki_client()

    try:
        # Find notes with old note type in this deck
        # Escape values to prevent query injection attacks
        escaped_deck = escape_anki_query_value(deck)
        escaped_note_type = escape_anki_query_value(OLD_NOTE_TYPE)
        query = f'"deck:{escaped_deck}" "note:{escaped_note_type}"'
        note_ids = await client.find_notes(query)

        if not note_ids:
            return NotesResponse(notes=[], total=0)

        # Get full note info
        notes_info = await client.get_notes_info(note_ids)

        # Convert to migration notes
        migration_notes = []
        for note in notes_info:
            # Extract sound fields for preservation
            sound = note.fields.get("Sound", "")
            sound_example = note.fields.get("Sound Example", "")

            migration_notes.append(MigrationNote(
                note_id=note.note_id,
                old_fields=note.fields,
                sound=sound,
                sound_example=sound_example
            ))

        return NotesResponse(notes=migration_notes, total=len(migration_notes))

    except AnkiConnectError as e:
        logger.error(f"AnkiConnect error getting notes: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot communicate with Anki: {e}"
        )


@router.post("/preview", response_model=PreviewResponse, dependencies=[Depends(verify_api_key)])
async def generate_migration_preview(request: PreviewRequest) -> PreviewResponse:
    """Generate a preview of what the migrated note will look like.

    This calls the agent to regenerate the card content based on the kana input.

    Args:
        request: PreviewRequest with the note ID and input data

    Returns:
        PreviewResponse with the new field values
    """
    config = load_config()

    # Create a draft card for the agent
    # Note: We don't pass old translations - the agent generates fresh ones from kana input.
    # Users can copy-paste old translations into the preview if they want to preserve them.
    draft_card = DraftCard(
        raw_input=request.raw_input,
        fixed_english=None,
        fixed_dutch=None,
        extra_notes=request.extra_notes,
        card_type_override=None  # Let agent classify
    )

    try:
        generated_cards = await generate_cards_with_agent(
            draft_cards=[draft_card],
            fields=config.fields,
            tags=config.tags,
        )

        if not generated_cards:
            raise HTTPException(status_code=500, detail="Agent returned no cards")

        generated = generated_cards[0]

        # Copy fields so we can add preserved sounds without mutating the original
        new_fields = generated.fields.copy()

        # Preserve the original sounds if provided
        if request.preserve_sound:
            new_fields["Sound"] = request.preserve_sound
        if request.preserve_sound_example:
            new_fields["Sound example"] = request.preserve_sound_example

        return PreviewResponse(
            note_id=request.note_id,
            new_fields=new_fields,
            auto_classified_type=generated.auto_classified_type
        )

    except CardGenerationError as e:
        logger.error(f"Card generation error during preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error during preview generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate preview. Please try again.")


@router.post("/preview-batch", response_model=BatchPreviewResponse, dependencies=[Depends(verify_api_key)])
async def generate_batch_migration_preview(request: BatchPreviewRequest) -> BatchPreviewResponse:
    """Generate previews for multiple notes in a single batch.

    This endpoint processes up to 10 notes at once, returning results for each.
    Individual item failures don't fail the entire batch - partial results are returned.

    Args:
        request: BatchPreviewRequest containing up to 10 items

    Returns:
        BatchPreviewResponse with results for each item
    """
    config = load_config()

    # Build draft cards for all items
    draft_cards = []
    item_mapping = []  # Track which draft card corresponds to which note_id

    for item in request.items:
        # Don't pass old translations - let agent generate new ones
        draft_card = DraftCard(
            raw_input=item.raw_input,
            fixed_english=None,
            fixed_dutch=None,
            extra_notes=item.extra_notes,
            card_type_override=None  # Let agent auto-classify
        )
        draft_cards.append(draft_card)
        item_mapping.append({
            'note_id': item.note_id,
            'preserve_sound': item.preserve_sound,
            'preserve_sound_example': item.preserve_sound_example,
        })

    try:
        # Generate all cards in a single agent call
        generated_cards = await generate_cards_with_agent(
            draft_cards=draft_cards,
            fields=config.fields,
            tags=config.tags,
        )

        if not generated_cards or len(generated_cards) != len(request.items):
            logger.error(f"Agent returned {len(generated_cards) if generated_cards else 0} cards, expected {len(request.items)}")
            raise HTTPException(status_code=500, detail="Agent returned unexpected number of cards")

        # Build results
        results = []
        for i, generated in enumerate(generated_cards):
            item_info = item_mapping[i]

            # Copy fields so we can add preserved sounds without mutating the original
            new_fields = generated.fields.copy()
            if item_info['preserve_sound']:
                new_fields['Sound'] = item_info['preserve_sound']
            if item_info['preserve_sound_example']:
                new_fields['Sound example'] = item_info['preserve_sound_example']

            results.append(BatchPreviewItemResult(
                note_id=item_info['note_id'],
                success=True,
                new_fields=new_fields,
                auto_classified_type=generated.auto_classified_type,
            ))

        return BatchPreviewResponse(
            results=results,
            successful_count=len(results),
            failed_count=0,
        )

    except CardGenerationError as e:
        logger.error(f"Batch preview generation failed: {e}")
        # Return all items as failed
        results = [
            BatchPreviewItemResult(
                note_id=item.note_id,
                success=False,
                error="Generation failed - please retry",
            )
            for item in request.items
        ]
        return BatchPreviewResponse(
            results=results,
            successful_count=0,
            failed_count=len(results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in batch preview: {e}")
        raise HTTPException(status_code=500, detail="Batch preview generation failed")


@router.post("/approve", response_model=ApproveResponse, dependencies=[Depends(verify_api_key)])
async def approve_migration(request: ApproveRequest) -> ApproveResponse:
    """Approve and commit a migrated note to Anki.

    This changes the note's model (note type) to the new format and updates all fields.
    The change is immediately reflected in Anki.

    Args:
        request: ApproveRequest with note ID and new field values

    Returns:
        ApproveResponse indicating success
    """
    client = get_anki_client()

    try:
        # Change the note model (note type) and update all fields in one operation
        # This converts the note from the old format to the new format
        await client.change_note_model(
            note_id=request.note_id,
            new_model_name=NEW_NOTE_TYPE,
            fields=request.new_fields,
            tags=request.tags
        )

        return ApproveResponse(success=True, note_id=request.note_id)

    except AnkiConnectError as e:
        logger.error(f"AnkiConnect error approving migration: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to update note in Anki: {e}"
        )
