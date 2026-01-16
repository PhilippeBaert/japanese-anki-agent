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


def strip_asterisk_markers(fields: dict[str, str]) -> dict[str, str]:
    """Remove asterisk markers from translation fields.

    The agent adds * to mark user-provided fixed translations (e.g., "Self-introduction*, zelfintroductie").
    For migration, we want clean translations without these markers.
    """
    result = fields.copy()

    # Fields that may contain asterisk markers
    translation_fields = ["English", "Dutch"]

    for field in translation_fields:
        if field in result and result[field]:
            # Remove asterisk that appears after a word (e.g., "Word*" -> "Word")
            # This handles patterns like "Word*, other" -> "Word, other"
            result[field] = re.sub(r'\*(?=,|$)', '', result[field])

    return result

# Old note type name - could be made configurable
OLD_NOTE_TYPE = "Philippe's Japanese v3"

# Field mapping from old to new format
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
    deck: str = Query(..., description="Deck name to get notes from")
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
        query = f'"deck:{deck}" "note:{OLD_NOTE_TYPE}"'
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
    draft_card = DraftCard(
        raw_input=request.raw_input,
        fixed_english=request.fixed_english,
        fixed_dutch=request.fixed_dutch,
        extra_notes=request.extra_notes,
        tags=[],
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

        # Strip asterisk markers from translations (used in normal app, not needed for migration)
        new_fields = strip_asterisk_markers(generated.fields)

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


@router.post("/approve", response_model=ApproveResponse, dependencies=[Depends(verify_api_key)])
async def approve_migration(request: ApproveRequest) -> ApproveResponse:
    """Approve and commit a migrated note to Anki.

    This updates the note's fields in Anki with the new values.

    Args:
        request: ApproveRequest with note ID and new field values

    Returns:
        ApproveResponse indicating success
    """
    client = get_anki_client()

    try:
        # Update the note fields
        await client.update_note_fields(request.note_id, request.new_fields)

        # Update tags if provided
        if request.tags:
            # First remove old card type tags, then add new ones
            await client.remove_tags([request.note_id], "word phrase sentence")
            await client.add_tags([request.note_id], " ".join(request.tags))

        return ApproveResponse(success=True, note_id=request.note_id)

    except AnkiConnectError as e:
        logger.error(f"AnkiConnect error approving migration: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to update note in Anki: {e}"
        )
