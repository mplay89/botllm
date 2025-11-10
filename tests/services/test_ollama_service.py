"""
Unit tests for services.ollama_service module.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.ollama_service import OllamaService, get_ollama_service


@pytest.mark.asyncio
class TestOllamaService:
    """Tests for OllamaService class."""

    async def test_init_with_defaults(self, mock_settings):
        """Test initialization with default settings."""
        mock_settings.OLLAMA_HOST = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "qwen2.5:7b-instruct-q5_K_M"

        with patch('bot.services.ollama_service.settings', mock_settings):
            with patch('bot.services.ollama_service.ollama.AsyncClient'):
                service = OllamaService()

                assert service.host == "http://localhost:11434"
                assert service.model == "qwen2.5:7b-instruct-q5_K_M"

    async def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('bot.services.ollama_service.ollama.AsyncClient'):
            service = OllamaService(
                host="http://custom:11434",
                model="custom-model"
            )

            assert service.host == "http://custom:11434"
            assert service.model == "custom-model"

    async def test_generate_response_success(self):
        """Test successful response generation."""
        mock_response = {
            "message": {
                "content": "Test response from Ollama"
            }
        }

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            service = OllamaService()
            response = await service.generate_response("Test prompt")

            assert response == "Test response from Ollama"
            mock_client.chat.assert_called_once()

    async def test_generate_response_with_system_prompt(self):
        """Test response generation with system prompt."""
        mock_response = {
            "message": {
                "content": "Response with system prompt"
            }
        }

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            service = OllamaService()
            response = await service.generate_response(
                "Test prompt",
                system_prompt="You are a helpful assistant"
            )

            assert response == "Response with system prompt"

            # Verify system message was included
            call_args = mock_client.chat.call_args
            messages = call_args[1]['messages']
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == 'You are a helpful assistant'
            assert messages[1]['role'] == 'user'

    async def test_generate_response_with_custom_parameters(self):
        """Test response generation with custom temperature and max_tokens."""
        mock_response = {
            "message": {
                "content": "Custom response"
            }
        }

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            service = OllamaService()
            await service.generate_response(
                "Test",
                temperature=0.9,
                max_tokens=4096
            )

            # Verify custom parameters were passed
            call_args = mock_client.chat.call_args
            options = call_args[1]['options']
            assert options['temperature'] == 0.9
            assert options['num_predict'] == 4096

    async def test_generate_response_exception(self):
        """Test handling of exceptions during generation."""
        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(side_effect=Exception("Connection error"))
            mock_client_class.return_value = mock_client

            service = OllamaService()

            with pytest.raises(Exception) as exc_info:
                await service.generate_response("Test")

            assert "Connection error" in str(exc_info.value)

    async def test_generate_response_stream_success(self):
        """Test successful streaming response generation."""
        mock_chunks = [
            {"message": {"content": "Hello "}},
            {"message": {"content": "world"}},
            {"message": {"content": "!"}}
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_stream())
            mock_client_class.return_value = mock_client

            service = OllamaService()
            chunks = []

            async for chunk in service.generate_response_stream("Test prompt"):
                chunks.append(chunk)

            assert chunks == ["Hello ", "world", "!"]

    async def test_generate_response_stream_with_system_prompt(self):
        """Test streaming with system prompt."""
        mock_chunks = [
            {"message": {"content": "Response"}}
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_stream())
            mock_client_class.return_value = mock_client

            service = OllamaService()
            chunks = []

            async for chunk in service.generate_response_stream(
                "Test",
                system_prompt="System"
            ):
                chunks.append(chunk)

            # Verify system message was included
            call_args = mock_client.chat.call_args
            messages = call_args[1]['messages']
            assert messages[0]['role'] == 'system'
            assert call_args[1]['stream'] is True

    async def test_generate_response_stream_exception(self):
        """Test handling of exceptions during streaming."""
        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(side_effect=Exception("Stream error"))
            mock_client_class.return_value = mock_client

            service = OllamaService()

            with pytest.raises(Exception) as exc_info:
                async for _ in service.generate_response_stream("Test"):
                    pass

            assert "Stream error" in str(exc_info.value)

    async def test_generate_with_context_success(self):
        """Test generation with conversation context."""
        mock_response = {
            "message": {
                "content": "Context-aware response"
            }
        }

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            service = OllamaService()
            response = await service.generate_with_context(messages)

            assert response == "Context-aware response"

            # Verify all messages were passed
            call_args = mock_client.chat.call_args
            assert call_args[1]['messages'] == messages

    async def test_generate_with_context_custom_parameters(self):
        """Test context generation with custom parameters."""
        mock_response = {
            "message": {
                "content": "Response"
            }
        }

        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            service = OllamaService()
            await service.generate_with_context(
                [{"role": "user", "content": "Test"}],
                temperature=0.5,
                max_tokens=1024
            )

            call_args = mock_client.chat.call_args
            options = call_args[1]['options']
            assert options['temperature'] == 0.5
            assert options['num_predict'] == 1024

    async def test_generate_with_context_exception(self):
        """Test handling of exceptions during context generation."""
        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat = AsyncMock(side_effect=Exception("Context error"))
            mock_client_class.return_value = mock_client

            service = OllamaService()

            with pytest.raises(Exception) as exc_info:
                await service.generate_with_context([{"role": "user", "content": "Test"}])

            assert "Context error" in str(exc_info.value)

    async def test_check_health_success(self):
        """Test successful health check."""
        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.list = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client

            service = OllamaService()
            is_healthy = await service.check_health()

            assert is_healthy is True
            mock_client.list.assert_called_once()

    async def test_check_health_failure(self):
        """Test health check failure."""
        with patch('bot.services.ollama_service.ollama.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.list = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_class.return_value = mock_client

            service = OllamaService()
            is_healthy = await service.check_health()

            assert is_healthy is False


@pytest.mark.asyncio
class TestGetOllamaService:
    """Tests for get_ollama_service singleton function."""

    async def test_get_ollama_service_creates_instance(self):
        """Test that get_ollama_service creates an instance."""
        with patch('bot.services.ollama_service.ollama_service', None):
            with patch('bot.services.ollama_service.ollama.AsyncClient'):
                service = get_ollama_service()

                assert service is not None
                assert isinstance(service, OllamaService)

    async def test_get_ollama_service_returns_same_instance(self):
        """Test that get_ollama_service returns the same instance."""
        with patch('bot.services.ollama_service.ollama.AsyncClient'):
            service1 = get_ollama_service()
            service2 = get_ollama_service()

            assert service1 is service2

    async def test_get_ollama_service_with_existing_instance(self):
        """Test that get_ollama_service returns existing instance."""
        with patch('bot.services.ollama_service.ollama.AsyncClient'):
            existing_service = OllamaService()

            with patch('bot.services.ollama_service.ollama_service', existing_service):
                service = get_ollama_service()

                assert service is existing_service
