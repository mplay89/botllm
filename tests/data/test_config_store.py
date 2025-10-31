"""
Unit tests for data.config_store module.
"""
import pytest
from unittest.mock import AsyncMock, patch

from data.config_store import (
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

        with patch('data.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            value = await get_setting("test_key")

            assert value == "test_value"
            mock_conn.fetchval.assert_called_once()

    async def test_get_setting_not_exists_default(self):
        """Test retrieving non-existent setting returns default."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=None)

        with patch('data.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            value = await get_setting("missing_key", default="default_val")

            assert value == "default_val"

    async def test_set_setting(self):
        """Test setting a configuration value."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch('data.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            await set_setting("test_key", "test_value")

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "INSERT INTO bot_config" in call_args[0]
            assert "ON CONFLICT" in call_args[0]
            assert call_args[1] == "test_key"
            assert call_args[2] == "test_value"


@pytest.mark.asyncio
class TestModelConfig:
    """Tests for model configuration."""

    async def test_get_text_model_name(self):
        """Test retrieving current text model name."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="models/gemini-2.5-flash")

        with patch('data.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            model = await get_text_model_name()

            assert model == "models/gemini-2.5-flash"

    async def test_get_text_model_name_empty(self):
        """Test retrieving text model when none is set."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=None)

        with patch('data.config_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            model = await get_text_model_name()

            assert model == ""

    async def test_set_text_model_available(self):
        """Test setting text model when it's available."""
        with patch('data.config_store.get_available_models') as mock_get_models:
            mock_get_models.return_value = ["models/gemini-2.5-flash", "models/gemini-2.5-pro"]

            with patch('data.config_store.set_setting') as mock_set:
                result = await set_text_model("models/gemini-2.5-flash")

                assert result is True
                mock_set.assert_called_once_with("current_text_model", "models/gemini-2.5-flash")

    async def test_set_text_model_unavailable(self):
        """Test setting text model when it's not available."""
        with patch('data.config_store.get_available_models') as mock_get_models:
            mock_get_models.return_value = ["models/gemini-2.5-flash"]

            with patch('data.config_store.set_setting') as mock_set:
                result = await set_text_model("models/invalid-model")

                assert result is False
                mock_set.assert_not_called()
