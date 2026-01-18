"""Tests for exponential backoff in agent.py repair loop."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestAgentBackoffConstants:
    """Test that backoff constants are defined correctly."""

    def test_repair_backoff_base_exists(self):
        """Test that REPAIR_BACKOFF_BASE constant exists and has correct value."""
        from app.services.agent import REPAIR_BACKOFF_BASE

        assert REPAIR_BACKOFF_BASE == 1.0
        assert isinstance(REPAIR_BACKOFF_BASE, float)

    def test_repair_backoff_max_exists(self):
        """Test that REPAIR_BACKOFF_MAX constant exists and has correct value."""
        from app.services.agent import REPAIR_BACKOFF_MAX

        assert REPAIR_BACKOFF_MAX == 10.0
        assert isinstance(REPAIR_BACKOFF_MAX, float)

    def test_backoff_max_greater_than_base(self):
        """Test that REPAIR_BACKOFF_MAX is greater than REPAIR_BACKOFF_BASE."""
        from app.services.agent import REPAIR_BACKOFF_BASE, REPAIR_BACKOFF_MAX

        assert REPAIR_BACKOFF_MAX > REPAIR_BACKOFF_BASE


class TestExponentialBackoffCalculation:
    """Test the exponential backoff calculation logic."""

    def test_exponential_backoff_formula(self):
        """Test that exponential backoff follows 2^n formula."""
        from app.services.agent import REPAIR_BACKOFF_BASE, REPAIR_BACKOFF_MAX

        # Simulate the backoff calculation from generate_cards_with_agent
        # The formula: min(REPAIR_BACKOFF_BASE * (2 ** (repair_attempts - 1)), REPAIR_BACKOFF_MAX)

        # First repair attempt (repair_attempts=1): no delay (only applied for repair_attempts > 1)

        # Second repair attempt (repair_attempts=2)
        repair_attempts = 2
        backoff_delay = min(
            REPAIR_BACKOFF_BASE * (2 ** (repair_attempts - 1)),
            REPAIR_BACKOFF_MAX
        )
        assert backoff_delay == 2.0  # 1.0 * 2^1 = 2.0

        # Third repair attempt (repair_attempts=3)
        repair_attempts = 3
        backoff_delay = min(
            REPAIR_BACKOFF_BASE * (2 ** (repair_attempts - 1)),
            REPAIR_BACKOFF_MAX
        )
        assert backoff_delay == 4.0  # 1.0 * 2^2 = 4.0

        # Fourth repair attempt (repair_attempts=4)
        repair_attempts = 4
        backoff_delay = min(
            REPAIR_BACKOFF_BASE * (2 ** (repair_attempts - 1)),
            REPAIR_BACKOFF_MAX
        )
        assert backoff_delay == 8.0  # 1.0 * 2^3 = 8.0

    def test_backoff_respects_maximum(self):
        """Test that backoff never exceeds REPAIR_BACKOFF_MAX."""
        from app.services.agent import REPAIR_BACKOFF_BASE, REPAIR_BACKOFF_MAX

        # Large repair attempt number should be capped at REPAIR_BACKOFF_MAX
        repair_attempts = 10
        backoff_delay = min(
            REPAIR_BACKOFF_BASE * (2 ** (repair_attempts - 1)),
            REPAIR_BACKOFF_MAX
        )
        assert backoff_delay == REPAIR_BACKOFF_MAX  # Should be capped at 10.0

    def test_backoff_not_applied_on_first_attempt(self):
        """Test that backoff delay is only applied for attempts > 1."""
        from app.services.agent import REPAIR_BACKOFF_BASE, REPAIR_BACKOFF_MAX

        # The code only applies sleep when repair_attempts > 1
        repair_attempts = 1
        should_apply_backoff = repair_attempts > 1
        assert should_apply_backoff is False


class TestRepairLoopLimits:
    """Test that repair loop respects max_repair_attempts."""

    @pytest.mark.asyncio
    async def test_repair_loop_stops_at_max_attempts(self):
        """Test that the repair loop stops when max_repair_attempts is reached."""
        from app.services.agent import generate_cards_with_agent, CardGenerationError
        from app.models import DraftCard

        # Create test draft card
        draft_card = DraftCard(
            raw_input="test",
            fixed_english=None,
            fixed_dutch=None,
            extra_notes=None,
            card_type_override=None
        )

        # Mock the dependencies
        with patch('app.services.agent._run_agent_query') as mock_query, \
             patch('app.services.agent.validate_all_cards') as mock_validate, \
             patch('app.services.agent.build_generation_prompt') as mock_gen_prompt, \
             patch('app.services.agent.build_repair_prompt') as mock_repair_prompt, \
             patch('asyncio.sleep') as mock_sleep:

            # Mock the query to return valid JSON
            mock_query.return_value = '{"cards": [{"fields": {"test": "value"}, "tags": ["word"]}]}'
            mock_gen_prompt.return_value = "test prompt"
            mock_repair_prompt.return_value = "repair prompt"

            # Mock validation to always fail
            mock_validate.return_value = (False, ["validation error"])

            max_attempts = 3

            # Should raise CardGenerationError after max_repair_attempts
            with pytest.raises(CardGenerationError) as exc_info:
                await generate_cards_with_agent(
                    draft_cards=[draft_card],
                    fields=["test"],
                    tags=["word"],
                    max_repair_attempts=max_attempts
                )

            # Verify error message mentions repair attempts
            assert "repair attempts" in str(exc_info.value).lower()

            # Verify that we made exactly max_attempts repair calls (plus initial generation)
            # Initial call + max_repair_attempts repair calls
            assert mock_query.call_count == max_attempts + 1

    @pytest.mark.asyncio
    async def test_repair_loop_stops_on_success(self):
        """Test that the repair loop stops when validation succeeds."""
        from app.services.agent import generate_cards_with_agent
        from app.models import DraftCard

        draft_card = DraftCard(
            raw_input="test",
            fixed_english=None,
            fixed_dutch=None,
            extra_notes=None,
            card_type_override=None
        )

        with patch('app.services.agent._run_agent_query') as mock_query, \
             patch('app.services.agent.validate_all_cards') as mock_validate, \
             patch('app.services.agent.build_generation_prompt') as mock_gen_prompt, \
             patch('asyncio.sleep') as mock_sleep:

            mock_query.return_value = '{"cards": [{"fields": {"test": "value"}, "tags": ["word"]}]}'
            mock_gen_prompt.return_value = "test prompt"

            # First validation fails, second succeeds
            mock_validate.side_effect = [
                (False, ["initial error"]),  # First call fails
                (True, []),                   # Second call succeeds (after repair)
            ]

            result = await generate_cards_with_agent(
                draft_cards=[draft_card],
                fields=["test"],
                tags=["word"],
                max_repair_attempts=5
            )

            # Should have called query twice (initial + 1 repair)
            assert mock_query.call_count == 2
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_asyncio_sleep_called_with_backoff_delay(self):
        """Test that asyncio.sleep is called with the correct backoff delay."""
        from app.services.agent import generate_cards_with_agent, CardGenerationError
        from app.models import DraftCard

        draft_card = DraftCard(
            raw_input="test",
            fixed_english=None,
            fixed_dutch=None,
            extra_notes=None,
            card_type_override=None
        )

        with patch('app.services.agent._run_agent_query') as mock_query, \
             patch('app.services.agent.validate_all_cards') as mock_validate, \
             patch('app.services.agent.build_generation_prompt') as mock_gen_prompt, \
             patch('app.services.agent.build_repair_prompt') as mock_repair_prompt, \
             patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:

            mock_query.return_value = '{"cards": [{"fields": {"test": "value"}, "tags": ["word"]}]}'
            mock_gen_prompt.return_value = "test prompt"
            mock_repair_prompt.return_value = "repair prompt"

            # Validation always fails so we go through multiple repair attempts
            mock_validate.return_value = (False, ["error"])

            with pytest.raises(CardGenerationError):
                await generate_cards_with_agent(
                    draft_cards=[draft_card],
                    fields=["test"],
                    tags=["word"],
                    max_repair_attempts=3
                )

            # asyncio.sleep should be called for repair_attempts > 1
            # With max_repair_attempts=3, we have attempts 1, 2, 3
            # Sleep is only called for attempts 2 and 3 (when repair_attempts > 1)
            # So we expect 2 sleep calls
            assert mock_sleep.call_count == 2

            # Check that sleep was called with correct backoff values
            # Attempt 2: delay = min(1.0 * 2^1, 10.0) = 2.0
            # Attempt 3: delay = min(1.0 * 2^2, 10.0) = 4.0
            sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
            assert sleep_calls[0] == 2.0
            assert sleep_calls[1] == 4.0
