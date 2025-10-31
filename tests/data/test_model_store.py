"""
Unit tests for data.model_store module.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from data.model_store import sync_models, get_available_models, _get_model_priority


class TestModelPriority:
    """Tests for model priority calculation."""

    def test_flash_lite_priority(self):
        """Test flash-lite models have highest priority."""
        priority = _get_model_priority("models/gemini-2.5-flash-lite")
        assert priority == 1

    def test_flash_priority(self):
        """Test flash models have second priority."""
        priority = _get_model_priority("models/gemini-2.5-flash")
        assert priority == 2

    def test_pro_priority(self):
        """Test pro models have third priority."""
        priority = _get_model_priority("models/gemini-2.5-pro")
        assert priority == 3

    def test_other_priority(self):
        """Test other models have default priority."""
        priority = _get_model_priority("models/gemini-2.5-unknown")
        assert priority == 100


@pytest.mark.asyncio
class TestSyncModels:
    """Tests for model synchronization."""

    async def test_sync_models_no_changes(self):
        """Test sync when models are already up to date."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {'model_name': 'models/gemini-2.5-flash'},
            {'model_name': 'models/gemini-2.5-pro'}
        ])

        with patch('data.model_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            api_models = ['models/gemini-2.5-flash', 'models/gemini-2.5-pro']
            await sync_models(api_models)

            # Should not delete or insert since models match
            assert mock_conn.execute.call_count == 0

    async def test_sync_models_with_changes(self):
        """Test sync when models need updating."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {'model_name': 'models/old-model'}
        ])
        mock_conn.execute = AsyncMock()
        mock_conn.transaction = MagicMock()

        # Mock transaction context manager
        mock_transaction = AsyncMock()
        mock_transaction.__aenter__ = AsyncMock()
        mock_transaction.__aexit__ = AsyncMock()
        mock_conn.transaction.return_value = mock_transaction

        with patch('data.model_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            api_models = ['models/gemini-2.5-flash', 'models/gemini-2.5-pro']
            await sync_models(api_models)

            # Should delete old models and insert new ones
            assert mock_conn.execute.call_count == 3  # 1 DELETE + 2 INSERTs

@pytest.mark.asyncio
class TestGetAvailableModels:
    """Tests for retrieving available models."""

    async def test_get_available_models(self):
        """Test retrieving active models."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {'model_name': 'models/gemini-2.5-flash'},
            {'model_name': 'models/gemini-2.5-pro'}
        ])

        with patch('data.model_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            models = await get_available_models()

            assert len(models) == 2
            assert 'models/gemini-2.5-flash' in models
            assert 'models/gemini-2.5-pro' in models

    async def test_get_available_models_empty(self):
        """Test retrieving models when none are available."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        with patch('data.model_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            models = await get_available_models()

            assert models == []

    async def test_get_available_models_sorted(self):
        """Test that models are returned sorted by priority."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {'model_name': 'models/gemini-2.5-flash'},
            {'model_name': 'models/gemini-2.5-pro'},
            {'model_name': 'models/gemini-2.5-flash-lite'}
        ])

        with patch('data.model_store.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            await get_available_models()

            # Verify fetch was called with ORDER BY clause
            call_args = mock_conn.fetch.call_args[0][0]
            assert "ORDER BY priority ASC" in call_args
