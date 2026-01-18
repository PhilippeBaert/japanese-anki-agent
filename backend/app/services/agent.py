"""Claude Agent SDK integration for card generation."""

import json
import logging
import os
from collections.abc import Callable

from claude_agent_sdk import query, ClaudeAgentOptions

from ..models import DraftCard, GeneratedCard
from ..prompts.generation import build_generation_prompt, build_repair_prompt
from .validator import validate_all_cards

# Set up logging for debugging
logger = logging.getLogger(__name__)

# Check if debug mode is enabled
DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

# Model configuration
# Note: Generation is non-idempotent - calling with the same input may produce slightly
# different results (different example sentences, wording variations) due to model sampling.
# This is expected behavior; each generation is a fresh creative task.
DEFAULT_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_MAX_TURNS = 1

# Default card type when not specified
DEFAULT_CARD_TYPE = "word"

# Log preview lengths for debugging output
LOG_PREVIEW_SHORT = 200
LOG_PREVIEW_MEDIUM = 500
LOG_PREVIEW_LONG = 1000


def _create_stderr_handler() -> Callable[[str], None]:
    """Create a stderr handler that logs CLI output."""
    def handler(text: str) -> None:
        # Log each line of stderr output
        for line in text.strip().split('\n'):
            if line:
                logger.warning(f"[Claude CLI stderr]: {line}")
    return handler


class CardGenerationError(Exception):
    """Raised when card generation fails."""
    pass


async def generate_cards_with_agent(
    draft_cards: list[DraftCard],
    fields: list[str],
    tags: list[str],
    max_repair_attempts: int = 1
) -> list[GeneratedCard]:
    """
    Generate Anki cards using Claude Agent SDK.

    Args:
        draft_cards: List of draft card inputs from user
        fields: List of field names from config
        tags: List of available tags from config
        max_repair_attempts: Number of repair attempts if validation fails

    Returns:
        List of validated GeneratedCard objects
    """
    # Convert DraftCard models to dicts for prompt building
    cards_data = [
        {
            'raw_input': card.raw_input,
            'fixed_english': card.fixed_english,
            'fixed_dutch': card.fixed_dutch,
            'extra_notes': card.extra_notes,
            'card_type_override': card.card_type_override
        }
        for card in draft_cards
    ]

    # Build the generation prompt
    prompt = build_generation_prompt(cards_data, fields, tags)

    # Configure agent options - simple approach
    # Prompt asks for JSON, we parse the text response
    # Note: Don't use include_partial_messages with FastAPI to avoid asyncio task issues
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        max_turns=DEFAULT_MAX_TURNS,
        allowed_tools=[],
        stderr=_create_stderr_handler(),  # Capture CLI stderr for debugging
    )

    logger.info(f"Generating cards for {len(draft_cards)} draft card(s)")
    if DEBUG_MODE:
        logger.debug(f"Prompt (first {LOG_PREVIEW_LONG} chars):\n{prompt[:LOG_PREVIEW_LONG]}...")

    # Generate cards
    result_text = await _run_agent_query(prompt, options)
    cards_data = _parse_json_result(result_text)

    # Validate cards
    is_valid, errors = validate_all_cards(cards_data, fields)

    # Repair if needed
    repair_attempts = 0
    while not is_valid and repair_attempts < max_repair_attempts:
        repair_attempts += 1
        repair_prompt = build_repair_prompt(cards_data, errors)
        result_text = await _run_agent_query(repair_prompt, options)
        cards_data = _parse_json_result(result_text)
        is_valid, errors = validate_all_cards(cards_data, fields)

    if not is_valid:
        raise CardGenerationError(f"Card validation failed after {repair_attempts} repair attempts. Errors: {errors}")

    # Convert to GeneratedCard models
    return [
        GeneratedCard(
            fields=card['fields'],
            tags=card['tags'],
            auto_classified_type=card.get('auto_classified_type', DEFAULT_CARD_TYPE)
        )
        for card in cards_data
    ]


async def _run_agent_query(prompt: str, options: ClaudeAgentOptions) -> str:
    """Run the Claude agent and extract the result.

    The Claude Agent SDK yields different message types:
    - SystemMessage: Initialization message
    - AssistantMessage: Contains the actual text content in TextBlock objects
    - ResultMessage: Contains metadata (duration, cost, etc.)

    We collect text from AssistantMessage TextBlocks and return it.

    IMPORTANT: We must fully consume the async generator to avoid cancel scope issues.
    """
    collected_text: list[str] = []
    error_occurred: str | None = None

    logger.debug("Starting agent query...")

    # IMPORTANT: Must fully consume the generator - don't break or raise during iteration
    # to avoid "Attempted to exit cancel scope in a different task" errors
    try:
        async for message in query(prompt=prompt, options=options):
            message_type = type(message).__name__
            logger.debug(f"Received message type: {message_type}")

            if message_type == 'SystemMessage':
                # Initialization message - log details
                logger.debug("Received SystemMessage")
                if DEBUG_MODE and hasattr(message, 'subtype'):
                    logger.debug(f"  SystemMessage.subtype = {message.subtype}")
                if DEBUG_MODE and hasattr(message, 'data'):
                    logger.debug(f"  SystemMessage.data = {message.data}")

            elif message_type == 'AssistantMessage':
                # Extract text from content blocks
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            preview = block.text[:LOG_PREVIEW_SHORT] if len(block.text) > LOG_PREVIEW_SHORT else block.text
                            logger.debug(f"TextBlock content (first {LOG_PREVIEW_SHORT} chars): {preview}...")
                            collected_text.append(block.text)

            elif message_type == 'ResultMessage':
                # Completion message with metadata - log all available info
                logger.debug("ResultMessage received - query complete")

                # Log all attributes for debugging
                if DEBUG_MODE:
                    for attr in ['subtype', 'is_error', 'result', 'duration_ms', 'num_turns', 'session_id']:
                        if hasattr(message, attr):
                            value = getattr(message, attr)
                            if attr == 'result' and value:
                                value = f"{str(value)[:LOG_PREVIEW_SHORT]}..." if len(str(value)) > LOG_PREVIEW_SHORT else value
                            logger.debug(f"  ResultMessage.{attr} = {value}")

                if hasattr(message, 'is_error') and message.is_error:
                    # Try to get more error details
                    subtype = getattr(message, 'subtype', 'unknown')
                    result = getattr(message, 'result', None)
                    error_occurred = f"Claude agent returned error (subtype={subtype})"
                    if result:
                        error_occurred += f": {result[:LOG_PREVIEW_MEDIUM]}"
                    logger.error(error_occurred)
                    # Don't raise here - let the generator finish
    except Exception as e:
        logger.error(f"Error during agent query: {e}")
        error_occurred = str(e)

    # Now that generator is fully consumed, we can raise errors
    if error_occurred:
        raise CardGenerationError(error_occurred)

    if not collected_text:
        logger.error("No text content received from Claude agent")
        raise CardGenerationError("No result received from Claude agent")

    final_result = "".join(collected_text)
    preview = final_result[:LOG_PREVIEW_MEDIUM] if len(final_result) > LOG_PREVIEW_MEDIUM else final_result
    logger.debug(f"Final result (first {LOG_PREVIEW_MEDIUM} chars): {preview}...")
    return final_result


def _parse_json_result(result_text: str) -> list[dict]:
    """Parse the JSON result from the agent."""
    try:
        # Try to extract JSON from the result
        # Sometimes the model might include markdown code blocks
        text = result_text.strip()

        # Remove markdown code blocks if present
        if text.startswith('```'):
            lines = text.split('\n')
            # Find the JSON content between code blocks
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith('```') and not in_block:
                    in_block = True
                    continue
                elif line.startswith('```') and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            text = '\n'.join(json_lines)

        data = json.loads(text)

        if 'cards' not in data:
            raise CardGenerationError("Response missing 'cards' key")

        return data['cards']

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}\nResponse: {result_text[:LOG_PREVIEW_MEDIUM]}")
        raise CardGenerationError("Failed to parse response from AI model")
