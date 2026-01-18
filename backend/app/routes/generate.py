"""Generate endpoint for creating Anki cards."""

import logging

from fastapi import APIRouter, HTTPException, Depends
from ..models import GenerateRequest, GenerateResponse, RegenerateCardRequest, GeneratedCard, DraftCard
from ..config import load_config
from ..services.agent import generate_cards_with_agent, CardGenerationError
from ..auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse, dependencies=[Depends(verify_api_key)])
async def generate_cards(request: GenerateRequest) -> GenerateResponse:
    """
    Generate Anki cards from draft inputs using Claude AI.

    Args:
        request: GenerateRequest containing draft cards and optional filename

    Returns:
        GenerateResponse with generated cards and filename
    """
    config = load_config()

    try:
        # Generate cards using Claude Agent
        generated_cards = await generate_cards_with_agent(
            draft_cards=request.draft_cards,
            fields=config.fields,
            tags=config.tags,
        )

        # Determine filename
        filename = request.filename or 'anki_cards'

        return GenerateResponse(
            cards=generated_cards,
            filename=filename,
        )

    except CardGenerationError as e:
        logger.error(f"Card generation error: {e}")
        raise HTTPException(status_code=500, detail="Card generation failed. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error during card generation: {e}")
        raise HTTPException(status_code=500, detail="Card generation failed. Please try again.")


@router.post("/regenerate-card", response_model=GeneratedCard, dependencies=[Depends(verify_api_key)])
async def regenerate_card(request: RegenerateCardRequest) -> GeneratedCard:
    """
    Regenerate a single card with a specific card type.

    Used when user changes the tag and content needs updating
    (e.g., add/remove example sentences).

    Args:
        request: RegenerateCardRequest with raw input and target type

    Returns:
        A single regenerated GeneratedCard
    """
    config = load_config()

    # Create a draft card with the type override
    draft_card = DraftCard(
        raw_input=request.raw_input,
        fixed_english=request.fixed_english,
        fixed_dutch=request.fixed_dutch,
        extra_notes=request.extra_notes,
        card_type_override=request.target_type
    )

    try:
        generated_cards = await generate_cards_with_agent(
            draft_cards=[draft_card],
            fields=config.fields,
            tags=config.tags,
        )
        return generated_cards[0]

    except CardGenerationError as e:
        logger.error(f"Card regeneration error: {e}")
        raise HTTPException(status_code=500, detail="Card regeneration failed. Please try again.")
    except Exception as e:
        logger.error(f"Unexpected error during card regeneration: {e}")
        raise HTTPException(status_code=500, detail="Card regeneration failed. Please try again.")
