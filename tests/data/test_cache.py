from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.db.cache import (
    _warm_up_models_cache,
    _warm_up_settings_cache,
    _warm_up_users_cache,
    invalidate_models_cache,
    invalidate_settings_cache,
    invalidate_user_cache,
    warm_up_caches,
)

USER_ID = 12345


@pytest.mark.asyncio
@patch("bot.db.model_store.get_available_models", new_callable=AsyncMock)
async def test_warm_up_models_cache(mock_get_available_models):
    """Тестує _warm_up_models_cache."""
    await _warm_up_models_cache()
    mock_get_available_models.assert_called_once()


@pytest.mark.asyncio
@patch("bot.db.config_store.get_text_model_name", new_callable=AsyncMock)
async def test_warm_up_settings_cache(mock_get_text_model_name):
    """Тестує _warm_up_settings_cache."""
    await _warm_up_settings_cache()
    mock_get_text_model_name.assert_called_once()


@pytest.mark.asyncio
@patch("bot.db.cache.get_db_connection")
@patch("bot.db.user_settings.get_user_role", new_callable=AsyncMock)
@patch("bot.db.user_settings.get_user_tts_settings", new_callable=AsyncMock)
async def test_warm_up_users_cache(mock_get_user_tts_settings, mock_get_user_role, mock_get_db_connection):
    """Тестує _warm_up_users_cache."""
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[{"user_id": USER_ID}])
    mock_get_db_connection.return_value.__aenter__.return_value = mock_conn

    await _warm_up_users_cache()

    mock_get_user_role.assert_called_once_with(USER_ID)
    mock_get_user_tts_settings.assert_called_once_with(USER_ID)


@pytest.mark.asyncio
@patch("bot.db.cache._warm_up_models_cache", new_callable=AsyncMock)
@patch("bot.db.cache._warm_up_settings_cache", new_callable=AsyncMock)
@patch("bot.db.cache._warm_up_users_cache", new_callable=AsyncMock)
async def test_warm_up_caches(mock_warm_up_users_cache, mock_warm_up_settings_cache, mock_warm_up_models_cache):
    """Тестує warm_up_caches."""
    await warm_up_caches()
    mock_warm_up_models_cache.assert_called_once()
    mock_warm_up_settings_cache.assert_called_once()
    mock_warm_up_users_cache.assert_called_once()


def test_invalidate_settings_cache():
    """Тестує invalidate_settings_cache."""
    from bot.db import cache
    cache.settings_cache = {"test_key": "test_value"}
    invalidate_settings_cache("test_key")
    assert "test_key" not in cache.settings_cache

    cache.settings_cache = {"test_key": "test_value"}
    invalidate_settings_cache("non_existent_key")
    assert "test_key" in cache.settings_cache

    cache.settings_cache = {"test_key": "test_value"}
    invalidate_settings_cache()
    assert not cache.settings_cache


def test_invalidate_models_cache():
    """Тестує invalidate_models_cache."""
    from bot.db import cache
    cache.models_cache = {"test": "test"}
    invalidate_models_cache()
    assert cache.models_cache is None


def test_invalidate_user_cache():
    """Тестує invalidate_user_cache."""
    from bot.db import cache
    cache.user_cache = {USER_ID: {"test_key": "test_value"}}
    invalidate_user_cache(USER_ID, "test_key")
    assert "test_key" not in cache.user_cache[USER_ID]

    cache.user_cache = {USER_ID: {"test_key": "test_value"}}
    invalidate_user_cache(USER_ID)
    assert USER_ID not in cache.user_cache