"""
Unit tests for bot.db.config_store module.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

# Очищення кешу перед кожним тестом, щоб уникнути взаємного впливу
@pytest.fixture(autouse=True)
def reset_cache():
    from bot.db import cache
    cache.settings_cache = {}

from bot.db.config_store import (
    get_setting,
    set_setting,
    get_text_model_name,
    set_text_model
)


@pytest.mark.asyncio
class TestConfigStore:
    """Tests for config store operations."""

    async def test_get_setting_exists(self):
        """Test retrieving existing setting."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="test_value")

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            value = await get_setting("test_key")

            assert value == "test_value"
            mock_conn.fetchval.assert_called_once()

    async def test_get_setting_not_exists_default(self):
        """Test retrieving non-existent setting returns default."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=None)

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            value = await get_setting("missing_key", default="default_val")

            assert value == "default_val"

    async def test_set_setting(self):
        """Test setting a configuration value."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            await set_setting("test_key", "test_value")

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "INSERT INTO bot_config" in call_args[0]
            assert "ON CONFLICT" in call_args[0]
            assert call_args[1] == "test_key"
            assert call_args[2] == "test_value"

    async def test_get_setting_caching(self):
        """Test that settings are cached to avoid repeated DB calls."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="cached_value")

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            # Перший виклик - має піти в БД
            val1 = await get_setting("cached_key")
            assert val1 == "cached_value"
            mock_conn.fetchval.assert_called_once()

            # Другий виклик - має повернути значення з кешу
            val2 = await get_setting("cached_key")
            assert val2 == "cached_value"
            mock_conn.fetchval.assert_called_once()  # Кількість викликів не змінилась

            # Скидаємо лічильник і перевіряємо, що після зміни налаштування кеш інвалідується
            await set_setting("cached_key", "new_value")
            mock_conn.fetchval.reset_mock()
            mock_conn.fetchval.return_value = "new_value"

            val3 = await get_setting("cached_key")
            assert val3 == "new_value"
            mock_conn.fetchval.assert_called_once() # Знову був 1 виклик до БД


@pytest.mark.asyncio
class TestModelConfig:
    """Tests for model configuration."""

    async def test_get_text_model_name(self):
        """Test retrieving current text model name."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="models/gemini-2.5-flash")

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            model = await get_text_model_name()

            assert model == "models/gemini-2.5-flash"

    async def test_get_text_model_name_empty(self):
        """Test retrieving text model when none is set."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=None)

        with patch('bot.db.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            model = await get_text_model_name()

            assert model == ""

    async def test_set_text_model_available(self):
        """Test setting text model when it's available."""
        with patch('bot.db.config_store.get_available_models') as mock_get_models:
            mock_get_models.return_value = ["models/gemini-2.5-flash", "models/gemini-2.5-pro"]

            with patch('bot.db.config_store.set_setting') as mock_set:
                result = await set_text_model("models/gemini-2.5-flash")

                assert result is True
                mock_set.assert_called_once_with("current_text_model", "models/gemini-2.5-flash")

    async def test_set_text_model_unavailable(self):
        """Test setting text model when it's not available."""
        with patch('bot.db.config_store.get_available_models') as mock_get_models:
            mock_get_models.return_value = ["models/gemini-2.5-flash"]

            with patch('bot.db.config_store.set_setting') as mock_set:
                result = await set_text_model("models/invalid-model")

                assert result is False
                mock_set.assert_not_called()
