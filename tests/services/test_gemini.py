"""
Unit tests for services.gemini module.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from google.api_core import exceptions as google_exceptions

from services.gemini import GeminiService, refresh_available_models


@pytest.mark.asyncio
class TestRefreshAvailableModels:
    """Tests for model refresh functionality."""

    async def test_refresh_available_models_success(self):
        """Test successful model refresh."""
        mock_model1 = MagicMock()
        mock_model1.name = "models/gemini-2.5-flash"
        mock_model2 = MagicMock()
        mock_model2.name = "models/gemini-2.5-pro"

        with patch('services.gemini.client') as mock_client:
            mock_client.models.list = MagicMock(return_value=[mock_model1, mock_model2])

            with patch('services.gemini.sync_models') as mock_sync:
                await refresh_available_models()

                mock_sync.assert_called_once()
                call_args = mock_sync.call_args[0][0]
                assert "models/gemini-2.5-flash" in call_args
                assert "models/gemini-2.5-pro" in call_args

    async def test_refresh_filters_preview_models(self):
        """Test that preview models are filtered out."""
        mock_model1 = MagicMock()
        mock_model1.name = "models/gemini-2.5-flash"
        mock_model2 = MagicMock()
        mock_model2.name = "models/gemini-2.5-preview"  # Should be filtered

        with patch('services.gemini.client') as mock_client:
            mock_client.models.list = MagicMock(return_value=[mock_model1, mock_model2])

            with patch('services.gemini.sync_models') as mock_sync:
                await refresh_available_models()

                call_args = mock_sync.call_args[0][0]
                assert "models/gemini-2.5-flash" in call_args
                assert "models/gemini-2.5-preview" not in call_args

    async def test_refresh_filters_audio_models(self):
        """Test that audio models are filtered out."""
        mock_model1 = MagicMock()
        mock_model1.name = "models/gemini-2.5-flash"
        mock_model2 = MagicMock()
        mock_model2.name = "models/gemini-2.5-audio"  # Should be filtered

        with patch('services.gemini.client') as mock_client:
            mock_client.models.list = MagicMock(return_value=[mock_model1, mock_model2])

            with patch('services.gemini.sync_models') as mock_sync:
                await refresh_available_models()

                call_args = mock_sync.call_args[0][0]
                assert "models/gemini-2.5-flash" in call_args
                assert "models/gemini-2.5-audio" not in call_args

    async def test_refresh_client_not_initialized(self):
        """Test refresh when client is not initialized."""
        with patch('services.gemini.client', None):
            with patch('services.gemini.sync_models') as mock_sync:
                await refresh_available_models()

                mock_sync.assert_not_called()


@pytest.mark.asyncio
class TestGeminiService:
    """Tests for GeminiService class."""

    async def test_generate_text_response_success(self, mock_settings):
        """Test successful text generation."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner", full_name="Owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        mock_response = MagicMock()
        mock_response.text = "Test response"

        with patch('services.gemini.client') as mock_client:
            mock_client.models.generate_content = MagicMock(return_value=mock_response)

            with patch('services.gemini.get_api_text_model_name', return_value="models/gemini-2.5-flash"):
                with patch('services.gemini.get_user_context', return_value=[]):
                    with patch('services.gemini.add_message_to_context'):
                        response = await service.generate_text_response("Test prompt")

                        assert response == "Test response"

    async def test_generate_text_response_no_client(self, mock_settings):
        """Test generation when client is not initialized."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner", full_name="Owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        with patch('services.gemini.client', None):
            response = await service.generate_text_response("Test")

            assert "не налаштований для роботи з AI-моделями" in response

    async def test_generate_text_response_no_model(self, mock_settings):
        """Test generation when no model is configured."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner", full_name="Owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        with patch('services.gemini.client') as mock_client:
            with patch('services.gemini.get_api_text_model_name', new_callable=AsyncMock) as mock_get_model:
                mock_get_model.return_value = ""
                response = await service.generate_text_response("Test")

                assert "Не вдалося отримати назву моделі" in response

    async def test_generate_text_response_timeout_retry(self, mock_settings):
        """Test retry logic on timeout."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        with patch('services.gemini.client') as mock_client:
            with patch('services.gemini.get_api_text_model_name', return_value="models/gemini-2.5-flash"):
                with patch('services.gemini.get_user_context', return_value=[]):
                    with patch('services.gemini.add_message_to_context'):
                        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError):
                            with patch('asyncio.sleep'):
                                response = await service.generate_text_response("Test")

                                # Should fail after all retries
                                assert "помилка під час генерації відповіді" in response

    async def test_generate_text_response_resource_exhausted(self, mock_settings):
        """Test handling of ResourceExhausted error."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        with patch('services.gemini.client') as mock_client:
            with patch('services.gemini.get_api_text_model_name', return_value="models/gemini-2.5-flash"):
                with patch('services.gemini.get_user_context', return_value=[]):
                    with patch('asyncio.wait_for', side_effect=google_exceptions.ResourceExhausted("Quota exceeded")):
                        with patch('asyncio.sleep'):
                            response = await service.generate_text_response("Test")

                            assert "помилка під час генерації відповіді" in response

    async def test_generate_text_response_model_not_found(self, mock_settings):
        """Test handling of model not found error."""
        mock_bot = AsyncMock()
        mock_bot.get_chat = AsyncMock(return_value=MagicMock(username="owner"))

        service = GeminiService(user_id=123, bot=mock_bot)

        with patch('services.gemini.client') as mock_client:
            with patch('services.gemini.get_api_text_model_name', return_value="models/invalid"):
                with patch('services.gemini.get_user_context', return_value=[]):
                    with patch('asyncio.wait_for', side_effect=Exception("Model is not found")):
                        with patch('services.gemini.refresh_available_models'):
                            response = await service.generate_text_response("Test")

                            assert "модель не знайдено" in response

    async def test_generate_text_context_trimming(self, mock_settings):
        """Test that context is trimmed to CONTEXT_MESSAGE_LIMIT."""
        mock_bot = AsyncMock()
        service = GeminiService(user_id=123, bot=mock_bot)

        mock_response = MagicMock()
        mock_response.text = "Response"

        # Create context with more messages than limit
        large_context = [{'role': 'user', 'parts': [{'text': f'msg{i}'}]} for i in range(15)]

        with patch('services.gemini.client') as mock_client:
            mock_client.models.generate_content = MagicMock(return_value=mock_response)

            with patch('services.gemini.get_api_text_model_name', return_value="models/gemini-2.5-flash"):
                with patch('services.gemini.get_user_context', return_value=large_context):
                    with patch('services.gemini.add_message_to_context'):
                        with patch('services.gemini.runtime_config') as mock_config:
                            mock_config.CONTEXT_MESSAGE_LIMIT = 10
                            mock_config.GEMINI_API_TIMEOUT = 60
                            mock_config.API_RETRY_ATTEMPTS = 1

                            await service.generate_text_response("Test")

                            # Verify generate_content was called
                            call_args = mock_client.models.generate_content.call_args
                            contents = call_args[1]['contents']

                            # Should have 10 context messages + 1 new prompt = 11 total
                            assert len(contents) == 11
