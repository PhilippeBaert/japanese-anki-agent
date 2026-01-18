from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

# Card type classification
CardType = Literal["word", "phrase", "sentence"]


class Source(BaseModel):
    """A source configuration for cards"""
    label: str = Field(..., min_length=1, max_length=100, description="Display label for the source")
    tag: str = Field(..., min_length=1, max_length=50, description="Tag value to use in Anki")


class DraftCard(BaseModel):
    """A draft card input from the user"""
    raw_input: str = Field(..., max_length=10000, description="The raw input text (romaji, kana, kanji, Dutch, or mixed)")
    fixed_english: Optional[str] = Field(None, max_length=2000, description="Optional fixed English translation")
    fixed_dutch: Optional[str] = Field(None, max_length=2000, description="Optional fixed Dutch translation")
    extra_notes: Optional[str] = Field(None, max_length=2000, description="Optional extra notes")
    card_type_override: Optional[CardType] = Field(None, description="Override auto-classification")


class GeneratedCard(BaseModel):
    """A fully generated Anki card"""
    fields: dict[str, str] = Field(..., description="Field name to value mapping")
    tags: list[str] = Field(default_factory=list, max_length=50, description="Tags for this card")
    auto_classified_type: CardType = Field(..., description="Auto-classified card type (word/phrase/sentence)")

    @field_validator("fields")
    @classmethod
    def validate_fields_size(cls, v: dict[str, str]) -> dict[str, str]:
        if len(v) > 50:
            raise ValueError("fields cannot have more than 50 entries")
        return v


class GenerateRequest(BaseModel):
    """Request to generate cards"""
    draft_cards: list[DraftCard] = Field(..., min_length=1, max_length=100)
    filename: Optional[str] = Field(None, max_length=255, description="Output filename without extension")


class GenerateResponse(BaseModel):
    """Response from card generation"""
    cards: list[GeneratedCard]
    filename: str


class ExportRequest(BaseModel):
    """Request to export cards to CSV"""
    cards: list[GeneratedCard] = Field(..., max_length=1000)
    filename: str = Field(..., min_length=1, max_length=255)
    source: Optional[str] = Field(None, max_length=50, description="Source tag to prepend to all cards")


class AnkiConfig(BaseModel):
    """Configuration for Anki card generation.

    Uses snake_case internally (Python convention) but camelCase for JSON serialization
    (matching the config file format and frontend expectations).
    """
    model_config = {"populate_by_name": True, "serialize_by_alias": True}

    fields: list[str] = Field(default_factory=list, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=50)
    tags_column_enabled: bool = Field(default=True, alias="tagsColumnEnabled")
    tags_column_name: str = Field(default="Tags", max_length=100, alias="tagsColumnName")
    sources: list[Source] = Field(default_factory=list, max_length=20)
    default_source: Optional[str] = Field(None, max_length=50, alias="defaultSource")


class RegenerateCardRequest(BaseModel):
    """Request to regenerate a single card with a specific type"""
    raw_input: str = Field(..., max_length=10000, description="The raw input text")
    fixed_english: Optional[str] = Field(None, max_length=2000, description="Optional fixed English translation")
    fixed_dutch: Optional[str] = Field(None, max_length=2000, description="Optional fixed Dutch translation")
    extra_notes: Optional[str] = Field(None, max_length=2000, description="Optional extra notes")
    target_type: CardType = Field(..., description="The target card type (word/phrase/sentence)")


class ExportWithPriorityRequest(BaseModel):
    """Request to export cards split by core/extra priority"""
    core_cards: list[GeneratedCard] = Field(default_factory=list, max_length=1000)
    extra_cards: list[GeneratedCard] = Field(default_factory=list, max_length=1000)
    filename: str = Field(..., min_length=1, max_length=255)
    source: Optional[str] = Field(None, max_length=50, description="Source tag to prepend to all cards")
