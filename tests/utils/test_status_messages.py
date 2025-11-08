"""
Unit tests for utils.status_messages module.
"""
import pytest
from unittest.mock import AsyncMock

from bot.presentation.status_messages import send_status, update_status, delete_status


class TestSendStatus:
    """Tests for send_status function."""

    @pytest.mark.asyncio
    async def test_send_status_creates_message(self):
        """Test that send_status sends a formatted status message."""
        message_mock = AsyncMock()
        status_msg_mock = AsyncMock()
        message_mock.answer.return_value = status_msg_mock

        stage = "Генерація відповіді."
        result = await send_status(message_mock, stage)

        # Should call answer with formatted text
        message_mock.answer.assert_called_once_with(f"**Очікуйте...**\n{stage}")

        # Should return the status message
        assert result == status_msg_mock

    @pytest.mark.asyncio
    async def test_send_status_with_different_stages(self):
        """Test send_status with various stage descriptions."""
        message_mock = AsyncMock()
        status_msg_mock = AsyncMock()
        message_mock.answer.return_value = status_msg_mock

        stages = [
            "Генерація відповіді.",
            "Розпізнавання повідомлення.",
            "Обробка запиту.",
        ]

        for stage in stages:
            message_mock.reset_mock()
            await send_status(message_mock, stage)
            expected_text = f"**Очікуйте...**\n{stage}"
            message_mock.answer.assert_called_once_with(expected_text)


class TestUpdateStatus:
    """Tests for update_status function."""

    @pytest.mark.asyncio
    async def test_update_status_edits_message(self):
        """Test that update_status edits the status message."""
        status_msg_mock = AsyncMock()
        new_stage = "Відповідь отримана. Формування повідомлення.."

        await update_status(status_msg_mock, new_stage)

        # Should call edit_text with new formatted text
        expected_text = f"**Очікуйте...**\n{new_stage}"
        status_msg_mock.edit_text.assert_called_once_with(expected_text)

    @pytest.mark.asyncio
    async def test_update_status_handles_exception(self):
        """Test that update_status handles exceptions gracefully."""
        status_msg_mock = AsyncMock()
        status_msg_mock.edit_text.side_effect = Exception("Edit failed")

        # Should not raise exception
        await update_status(status_msg_mock, "New stage")

        # edit_text should have been called despite the error
        status_msg_mock.edit_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_with_various_stages(self):
        """Test updating status with different stage descriptions."""
        status_msg_mock = AsyncMock()

        stages = [
            "Розпізнано. Генерація відповіді.",
            "Відповідь отримана. Формування повідомлення..",
            "Майже готово...",
        ]

        for stage in stages:
            status_msg_mock.reset_mock()
            await update_status(status_msg_mock, stage)
            expected_text = f"**Очікуйте...**\n{stage}"
            status_msg_mock.edit_text.assert_called_once_with(expected_text)


class TestDeleteStatus:
    """Tests for delete_status function."""

    @pytest.mark.asyncio
    async def test_delete_status_deletes_message(self):
        """Test that delete_status deletes the status message."""
        status_msg_mock = AsyncMock()

        await delete_status(status_msg_mock)

        status_msg_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_status_handles_exception(self):
        """Test that delete_status handles exceptions gracefully."""
        status_msg_mock = AsyncMock()
        status_msg_mock.delete.side_effect = Exception("Delete failed")

        # Should not raise exception
        await delete_status(status_msg_mock)

        # delete should have been called despite the error
        status_msg_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_status_handles_message_not_found(self):
        """Test delete_status when message is already deleted."""
        status_msg_mock = AsyncMock()
        status_msg_mock.delete.side_effect = Exception("Message not found")

        # Should handle gracefully without raising
        await delete_status(status_msg_mock)

        status_msg_mock.delete.assert_called_once()


class TestStatusMessagesIntegration:
    """Integration tests for status messages workflow."""

    @pytest.mark.asyncio
    async def test_full_status_workflow(self):
        """Test complete workflow: send -> update -> delete."""
        message_mock = AsyncMock()
        status_msg_mock = AsyncMock()
        message_mock.answer.return_value = status_msg_mock

        # Send initial status
        status_msg = await send_status(message_mock, "Генерація відповіді.")
        assert status_msg == status_msg_mock
        message_mock.answer.assert_called_once()

        # Update status
        await update_status(status_msg, "Відповідь отримана. Формування повідомлення..")
        status_msg_mock.edit_text.assert_called_once()

        # Delete status
        await delete_status(status_msg)
        status_msg_mock.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_updates_before_delete(self):
        """Test multiple status updates before deletion."""
        message_mock = AsyncMock()
        status_msg_mock = AsyncMock()
        message_mock.answer.return_value = status_msg_mock

        # Send initial status
        status_msg = await send_status(message_mock, "Етап 1")

        # Multiple updates
        await update_status(status_msg, "Етап 2")
        await update_status(status_msg, "Етап 3")
        await update_status(status_msg, "Етап 4")

        assert status_msg_mock.edit_text.call_count == 3

        # Final delete
        await delete_status(status_msg)
        status_msg_mock.delete.assert_called_once()
