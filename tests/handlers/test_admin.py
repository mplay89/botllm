import os
import time
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.admin import (
    AdminActions,
    AdminFilter,
    OwnerFilter,
    add_admin_start_handler,
    admin_panel_handler,
    back_to_admin_panel_handler,
    cache_info_handler,
    cancel_fsm_handler,
    change_model_handler,
    list_admins_handler,
    manage_admins_handler,
    process_add_admin_handler,
    process_remove_admin_handler,
    remove_admin_start_handler,
    set_model_callback_handler,
)
from keyboards.reply import get_admin_menu

# pytest_plugins = ("pytest_asyncio",)

OWNER_ID = 12345
ADMIN_ID = 67890
USER_ID = 54321


@pytest.fixture
def mock_message():
    """Створює мок об'єкта Message."""
    message = MagicMock()
    message.from_user = MagicMock()
    message.answer = AsyncMock()
    message.answer_document = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query():
    """Створює мок об'єкта CallbackQuery."""
    callback = MagicMock()
    callback.from_user = MagicMock()
    callback.from_user.id = OWNER_ID
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def fsm_context():
    """Створює мок FSMContext."""
    storage = MemoryStorage()
    return FSMContext(storage, key=MagicMock())


@pytest.mark.asyncio
@patch("handlers.admin.settings")
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
async def test_admin_panel_handler(mock_is_admin, mock_settings, mock_message):
    """Тестує вхід в адмін-панель."""
    mock_settings.OWNER_ID = OWNER_ID
    mock_message.from_user.id = OWNER_ID
    mock_is_admin.return_value = True

    await admin_panel_handler(mock_message)

    mock_message.answer.assert_called_once()
    assert "Ви в адмін-панелі." in mock_message.answer.call_args[0]


@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings")
@patch("builtins.open", new_callable=mock_open)
@patch("os.remove")
async def test_cache_info_handler_sends_file_owner(
    mock_remove, mock_open_func, mock_settings, mock_cache, mock_is_admin, mock_message
):
    """Тестує, що cache_info_handler надсилає повний файл для власника."""
    mock_settings.OWNER_ID = OWNER_ID
    mock_message.from_user.id = OWNER_ID

    mock_cache.settings_cache = {}
    mock_cache.models_cache = {}
    mock_cache.user_cache = {
        ADMIN_ID: {"some_data": {"value": "admin_value", "timestamp": time.time()}},
        USER_ID: {"some_data": {"value": "user_value", "timestamp": time.time()}},
    }
    mock_cache.USER_CACHE_TTL = 3600

    async def is_admin_side_effect(user_id):
        return user_id == ADMIN_ID or user_id == OWNER_ID

    mock_is_admin.side_effect = is_admin_side_effect

    await cache_info_handler(mock_message)

    mock_message.answer_document.assert_called_once()
    # Перевіряємо вміст файлу
    mock_open_func().write.assert_called_once()
    file_content = mock_open_func().write.call_args[0][0]
    assert "👑 **Адміністратори:**" in file_content
    assert "👥 **Користувачі:**" in file_content
    assert f"Користувач {ADMIN_ID}" in file_content
    assert f"Користувач {USER_ID}" in file_content


@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings")
@patch("builtins.open", new_callable=mock_open)
@patch("os.remove")
async def test_cache_info_handler_sends_file_admin(
    mock_remove, mock_open_func, mock_settings, mock_cache, mock_is_admin, mock_message
):
    """Тестує, що cache_info_handler надсилає відфільтрований файл для адміна."""
    mock_settings.OWNER_ID = OWNER_ID
    mock_message.from_user.id = ADMIN_ID  # Запит від адміна

    mock_cache.settings_cache = {}
    mock_cache.models_cache = {}
    mock_cache.user_cache = {
        OWNER_ID: {"some_data": {"value": "owner_value", "timestamp": time.time()}},
        ADMIN_ID: {"some_data": {"value": "admin_value", "timestamp": time.time()}},
        USER_ID: {"some_data": {"value": "user_value", "timestamp": time.time()}},
    }
    mock_cache.USER_CACHE_TTL = 3600

    async def is_admin_side_effect(user_id):
        return user_id == OWNER_ID or user_id == ADMIN_ID

    mock_is_admin.side_effect = is_admin_side_effect

    await cache_info_handler(mock_message)

    mock_message.answer_document.assert_called_once()
    # Перевіряємо вміст файлу
    mock_open_func().write.assert_called_once()
    file_content = mock_open_func().write.call_args[0][0]
    assert f"Користувач {OWNER_ID}" not in file_content
    assert f"Користувач {ADMIN_ID}" not in file_content
    assert f"Користувач {USER_ID}" in file_content
