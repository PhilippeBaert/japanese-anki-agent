"""AnkiConnect API client for interacting with Anki desktop."""

import httpx
from typing import Any, Optional
from pydantic import BaseModel


class AnkiConnectError(Exception):
    """Error from AnkiConnect API."""
    pass


class DeckInfo(BaseModel):
    """Information about a deck."""
    name: str
    note_count: int


class NoteInfo(BaseModel):
    """Information about a note from Anki."""
    model_config = {"protected_namespaces": ()}

    note_id: int
    model_name: str
    fields: dict[str, str]
    tags: list[str]


class AnkiConnectClient:
    """Client for AnkiConnect REST API.

    AnkiConnect runs on localhost:8765 when Anki is open with the add-on installed.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.url = f"http://{host}:{port}"
        self.timeout = 30.0

    async def _invoke(self, action: str, **params: Any) -> Any:
        """Execute an AnkiConnect action.

        Args:
            action: The AnkiConnect action name
            **params: Parameters for the action

        Returns:
            The result from AnkiConnect

        Raises:
            AnkiConnectError: If AnkiConnect returns an error
        """
        payload = {
            "action": action,
            "version": 6,
            "params": params
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.url, json=payload)
                response.raise_for_status()
            except httpx.ConnectError:
                raise AnkiConnectError(
                    "Cannot connect to AnkiConnect. Is Anki running with AnkiConnect add-on installed?"
                )
            except httpx.HTTPError as e:
                raise AnkiConnectError(f"HTTP error communicating with AnkiConnect: {e}")

        result = response.json()

        if result.get("error"):
            raise AnkiConnectError(f"AnkiConnect error: {result['error']}")

        return result.get("result")

    async def check_connection(self) -> bool:
        """Check if AnkiConnect is available.

        Returns:
            True if connected, raises AnkiConnectError otherwise
        """
        version = await self._invoke("version")
        if version < 6:
            raise AnkiConnectError(f"AnkiConnect version {version} is too old. Please update.")
        return True

    async def get_deck_names(self) -> list[str]:
        """Get all deck names.

        Returns:
            List of deck names
        """
        return await self._invoke("deckNames")

    async def find_notes(self, query: str) -> list[int]:
        """Find note IDs matching a query.

        Args:
            query: Anki search query (e.g. 'deck:MyDeck note:MyNoteType')

        Returns:
            List of note IDs
        """
        return await self._invoke("findNotes", query=query)

    async def get_notes_info(self, note_ids: list[int]) -> list[NoteInfo]:
        """Get detailed information about notes.

        Args:
            note_ids: List of note IDs to fetch

        Returns:
            List of NoteInfo objects
        """
        if not note_ids:
            return []

        results = await self._invoke("notesInfo", notes=note_ids)

        notes = []
        for note_data in results:
            # Extract field values (AnkiConnect returns {fieldName: {value: "...", order: N}})
            fields = {}
            for field_name, field_data in note_data.get("fields", {}).items():
                fields[field_name] = field_data.get("value", "")

            notes.append(NoteInfo(
                note_id=note_data["noteId"],
                model_name=note_data["modelName"],
                fields=fields,
                tags=note_data.get("tags", [])
            ))

        return notes

    async def update_note_fields(self, note_id: int, fields: dict[str, str]) -> None:
        """Update the fields of a note.

        Args:
            note_id: The note ID to update
            fields: Dictionary of field name to new value
        """
        await self._invoke("updateNoteFields", note={
            "id": note_id,
            "fields": fields
        })

    async def change_note_model(
        self,
        note_id: int,
        new_model_name: str,
        fields: dict[str, str],
        tags: list[str] | None = None
    ) -> None:
        """Change a note's model (note type) and update its fields.

        This is used for migration - converting notes from one type to another.

        Args:
            note_id: The note ID to update
            new_model_name: Name of the new note type
            fields: Dictionary mapping new field names to their values
            tags: Optional list of tags to set (replaces existing tags)
        """
        # Build the fields mapping for the new model
        # AnkiConnect expects {newFieldName: newValue}
        await self._invoke("updateNoteModel", note={
            "id": note_id,
            "modelName": new_model_name,
            "fields": fields,
            "tags": tags if tags else []
        })

    async def add_tags(self, note_ids: list[int], tags: str) -> None:
        """Add tags to notes.

        Args:
            note_ids: List of note IDs
            tags: Space-separated tags to add
        """
        await self._invoke("addTags", notes=note_ids, tags=tags)

    async def remove_tags(self, note_ids: list[int], tags: str) -> None:
        """Remove tags from notes.

        Args:
            note_ids: List of note IDs
            tags: Space-separated tags to remove
        """
        await self._invoke("removeTags", notes=note_ids, tags=tags)

    async def get_model_names(self) -> list[str]:
        """Get all note type (model) names.

        Returns:
            List of note type names
        """
        return await self._invoke("modelNames")

    async def get_decks_with_note_type(
        self,
        note_type: str,
        exclude_empty: bool = True
    ) -> list[DeckInfo]:
        """Get decks that contain notes of a specific type.

        Args:
            note_type: Name of the note type to search for
            exclude_empty: If True, exclude decks with 0 matching notes

        Returns:
            List of DeckInfo with deck names and note counts
        """
        # Get all decks
        all_decks = await self.get_deck_names()

        deck_infos = []
        for deck_name in all_decks:
            # Count notes of this type in this deck
            query = f'"deck:{deck_name}" "note:{note_type}"'
            note_ids = await self.find_notes(query)

            if exclude_empty and len(note_ids) == 0:
                continue

            deck_infos.append(DeckInfo(
                name=deck_name,
                note_count=len(note_ids)
            ))

        return deck_infos


# Singleton instance for reuse
_client: Optional[AnkiConnectClient] = None


def get_anki_client() -> AnkiConnectClient:
    """Get the AnkiConnect client singleton."""
    global _client
    if _client is None:
        _client = AnkiConnectClient()
    return _client
