"""
Unit tests for utils.message_utils module.
"""
import pytest
from unittest.mock import AsyncMock, patch

from utils.message_utils import send_long_message, MAX_MESSAGE_LENGTH


class TestSendLongMessage:
    """Tests for send_long_message function."""

    @pytest.mark.asyncio
    async def test_send_short_message(self):
        """Test sending a message shorter than MAX_MESSAGE_LENGTH."""
        message_mock = AsyncMock()
        short_text = "Це коротке повідомлення"

        await send_long_message(message_mock, short_text)

        message_mock.answer.assert_called_once_with(short_text)

    @pytest.mark.asyncio
    async def test_send_exact_limit_message(self):
        """Test sending a message exactly at MAX_MESSAGE_LENGTH."""
        message_mock = AsyncMock()
        exact_text = "A" * MAX_MESSAGE_LENGTH

        await send_long_message(message_mock, exact_text)

        message_mock.answer.assert_called_once_with(exact_text)

    @pytest.mark.asyncio
    async def test_send_long_message_splits_by_newline(self):
        """Test that long messages are split by newline."""
        message_mock = AsyncMock()

        # Create a long message with newlines
        part1 = "A" * (MAX_MESSAGE_LENGTH - 100)
        part2 = "B" * 200
        long_text = f"{part1}\n{part2}"

        await send_long_message(message_mock, long_text)

        # Should be called twice (2 parts)
        assert message_mock.answer.call_count == 2

        # First call should have part1
        first_call_text = message_mock.answer.call_args_list[0][0][0]
        assert first_call_text.startswith(part1[:100])

    @pytest.mark.asyncio
    async def test_send_long_message_splits_by_space(self):
        """Test that messages without newlines split by space."""
        message_mock = AsyncMock()

        # Create a long message with spaces but no newlines
        words = ["слово"] * 1000
        long_text = " ".join(words)

        await send_long_message(message_mock, long_text)

        # Should be split into multiple parts
        assert message_mock.answer.call_count >= 2

    @pytest.mark.asyncio
    async def test_send_very_long_message_multiple_parts(self):
        """Test sending a very long message that needs multiple splits."""
        message_mock = AsyncMock()

        # Create a message that's 3x the limit
        very_long_text = "X" * (MAX_MESSAGE_LENGTH * 3)

        await send_long_message(message_mock, very_long_text)

        # Should be split into at least 3 parts
        assert message_mock.answer.call_count >= 3

    @pytest.mark.asyncio
    async def test_send_long_message_strips_leading_whitespace(self):
        """Test that leading whitespace is stripped from continuation parts."""
        message_mock = AsyncMock()

        # Create message with newline near the limit
        part1 = "A" * (MAX_MESSAGE_LENGTH - 10)
        part2 = "B" * 100
        long_text = f"{part1}\n    {part2}"  # Extra spaces after newline

        await send_long_message(message_mock, long_text)

        # Second part should not start with whitespace
        second_call_text = message_mock.answer.call_args_list[1][0][0]
        assert not second_call_text.startswith(" ")
        assert not second_call_text.startswith("\n")

    @pytest.mark.asyncio
    async def test_send_empty_message(self):
        """Test sending an empty message."""
        message_mock = AsyncMock()

        await send_long_message(message_mock, "")

        message_mock.answer.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_send_message_with_unicode(self):
        """Test sending a message with Ukrainian characters."""
        message_mock = AsyncMock()
        ukrainian_text = "Привіт! Це тестове повідомлення українською мовою. 🇺🇦"

        await send_long_message(message_mock, ukrainian_text)

        message_mock.answer.assert_called_once_with(ukrainian_text)
