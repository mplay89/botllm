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
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
async def test_admin_panel_handler(mock_is_admin, mock_message):
    """Тестує вхід в адмін-панель."""
    mock_message.from_user.id = OWNER_ID
    mock_is_admin.return_value = True

    await admin_panel_handler(mock_message)

    mock_message.answer.assert_called_once()
    assert "Ви в адмін-панелі." in mock_message.answer.call_args[0]


@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
@patch("handlers.admin.aiofiles.open")
@patch("os.remove")
async def test_cache_info_handler_sends_file_owner(
    mock_remove, mock_aio_open, mock_cache, mock_is_admin, mock_message
):
    """Тестує, що cache_info_handler надсилає повний файл для власника."""
    mock_message.from_user.id = OWNER_ID
    mock_aio_open.return_value.__aenter__.return_value.write = AsyncMock()

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
    mock_aio_open.return_value.__aenter__.return_value.write.assert_awaited_once()
    file_content = mock_aio_open.return_value.__aenter__.return_value.write.await_args[0][0]
    assert "👑 **Адміністратори:**" in file_content
    assert "👥 **Користувачі:**" in file_content
    assert f"Користувач {ADMIN_ID}" in file_content
    assert f"Користувач {USER_ID}" in file_content


@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
@patch("handlers.admin.aiofiles.open")
@patch("os.remove")
async def test_cache_info_handler_sends_file_admin(
    mock_remove, mock_aio_open, mock_cache, mock_is_admin, mock_message
):
    """Тестує, що cache_info_handler надсилає відфільтрований файл для адміна."""
    mock_message.from_user.id = ADMIN_ID  # Запит від адміна
    mock_aio_open.return_value.__aenter__.return_value.write = AsyncMock()

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
    mock_aio_open.return_value.__aenter__.return_value.write.assert_awaited_once()
    file_content = mock_aio_open.return_value.__aenter__.return_value.write.await_args[0][0]
    assert f"Користувач {OWNER_ID}" not in file_content
    assert f"Користувач {ADMIN_ID}" not in file_content
    assert f"Користувач {USER_ID}" in file_content

@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
async def test_admin_filter(mock_is_admin, mock_message):
    """Тестує AdminFilter."""
    mock_message.from_user.id = ADMIN_ID
    mock_is_admin.return_value = True
    admin_filter = AdminFilter()
    assert await admin_filter(mock_message) is True

    mock_is_admin.return_value = False
    assert await admin_filter(mock_message) is False


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_owner_filter(mock_message):
    """Тестує OwnerFilter."""
    mock_message.from_user.id = OWNER_ID
    owner_filter = OwnerFilter()
    assert await owner_filter(mock_message) is True

    mock_message.from_user.id = ADMIN_ID
    assert await owner_filter(mock_message) is False


@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
@patch("handlers.admin.aiofiles.open")
@patch("os.remove")
async def test_cache_info_handler_empty_cache(
    mock_remove, mock_aio_open, mock_cache, mock_is_admin, mock_message
):
    """Тестує cache_info_handler з порожнім кешем."""
    mock_message.from_user.id = OWNER_ID
    mock_is_admin.return_value = True
    mock_aio_open.return_value.__aenter__.return_value.write = AsyncMock()

    mock_cache.settings_cache = {}
    mock_cache.models_cache = {}
    mock_cache.user_cache = {}

    await cache_info_handler(mock_message)

    mock_message.answer_document.assert_called_once()
    mock_aio_open.return_value.__aenter__.return_value.write.assert_awaited_once()
    file_content = mock_aio_open.return_value.__aenter__.return_value.write.await_args[0][0]
    assert "- Порожньо" in file_content

@pytest.mark.asyncio
@patch("handlers.admin.is_admin", new_callable=AsyncMock)
@patch("handlers.admin.cache")
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
@patch("handlers.admin.aiofiles.open")
@patch("os.remove")
async def test_cache_info_handler_with_data(
    mock_remove, mock_aio_open, mock_cache, mock_is_admin, mock_message
):
    """Тестує cache_info_handler з непустим кешем."""
    mock_message.from_user.id = OWNER_ID
    mock_is_admin.return_value = True
    mock_aio_open.return_value.__aenter__.return_value.write = AsyncMock()

    mock_cache.settings_cache = {"key": {"value": "value", "timestamp": time.time()}}
    mock_cache.models_cache = {"models": ["model1"], "timestamp": time.time()}
    mock_cache.user_cache = {}
    mock_cache.SETTINGS_CACHE_TTL = 3600
    mock_cache.MODELS_CACHE_TTL = 3600

    await cache_info_handler(mock_message)

    mock_message.answer_document.assert_called_once()
    mock_aio_open.return_value.__aenter__.return_value.write.assert_awaited_once()
    file_content = mock_aio_open.return_value.__aenter__.return_value.write.await_args[0][0]
    assert "value" in file_content
    assert "model1" in file_content


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_back_to_admin_panel_handler(mock_message, fsm_context):
    """Тестує повернення до адмін-панелі."""
    mock_message.from_user.id = OWNER_ID
    await fsm_context.set_state(AdminActions.waiting_for_admin_to_add)

    await back_to_admin_panel_handler(mock_message, fsm_context)

    mock_message.answer.assert_called_once()
    assert "Ви в адмін-панелі." in mock_message.answer.call_args[0]
    state = await fsm_context.get_state()
    assert state is None


@pytest.mark.asyncio
@patch("handlers.admin.get_text_model_name", new_callable=AsyncMock)
@patch("handlers.admin.get_available_models", new_callable=AsyncMock)
async def test_change_model_handler(mock_get_available_models, mock_get_text_model_name, mock_message):
    """Тестує change_model_handler."""
    mock_get_text_model_name.return_value = "models/gemini-pro"
    mock_get_available_models.return_value = ["models/gemini-pro", "models/gemini-flash"]

    await change_model_handler(mock_message)

    mock_message.answer.assert_called_once()
    assert "Поточна модель:" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("handlers.admin.get_text_model_name", new_callable=AsyncMock)
@patch("handlers.admin.get_available_models", new_callable=AsyncMock)
async def test_change_model_handler_no_models(mock_get_available_models, mock_get_text_model_name, mock_message):
    """Тестує change_model_handler, коли немає доступних моделей."""
    mock_get_available_models.return_value = []
    mock_get_text_model_name.return_value = "models/gemini-pro"

    await change_model_handler(mock_message)

    mock_message.answer.assert_called_once_with(
        "Список доступних моделей порожній. Спробуйте оновити його пізніше."
    )


@pytest.mark.asyncio
@patch("handlers.admin.set_text_model", new_callable=AsyncMock)
@patch("handlers.admin.get_available_models", new_callable=AsyncMock)
async def test_set_model_callback_handler(mock_get_available_models, mock_set_text_model, mock_callback_query):
    """Тестує set_model_callback_handler."""
    mock_set_text_model.return_value = True
    mock_get_available_models.return_value = ["models/gemini-pro", "models/gemini-flash"]
    mock_callback_query.data = "set_model:models/gemini-flash"

    await set_model_callback_handler(mock_callback_query)

    mock_callback_query.message.edit_text.assert_called_once()
    assert "✅ Модель змінено на" in mock_callback_query.message.edit_text.call_args[0][0]
    mock_callback_query.answer.assert_called_once_with("Збережено!")


@pytest.mark.asyncio
@patch("handlers.admin.set_text_model", new_callable=AsyncMock)
async def test_set_model_callback_handler_fail(mock_set_text_model, mock_callback_query):
    """Тестує set_model_callback_handler, коли не вдається змінити модель."""
    mock_set_text_model.return_value = False
    mock_callback_query.data = "set_model:models/gemini-flash"

    await set_model_callback_handler(mock_callback_query)

    mock_callback_query.answer.assert_called_once_with("Не вдалося змінити модель.", show_alert=True)

@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_manage_admins_handler(mock_message):
    """Тестує manage_admins_handler."""
    mock_message.from_user.id = OWNER_ID

    await manage_admins_handler(mock_message)

    mock_message.answer.assert_called_once()
    assert "Меню керування адміністраторами:" in mock_message.answer.call_args[0]

@pytest.mark.asyncio
async def test_manage_admins_handler_not_owner(mock_message):
    """Тестує manage_admins_handler, коли користувач не є власником."""
    mock_message.from_user.id = ADMIN_ID

    await manage_admins_handler(mock_message)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_add_admin_start_handler(mock_message, fsm_context):
    """Тестує add_admin_start_handler."""
    mock_message.from_user.id = OWNER_ID

    await add_admin_start_handler(mock_message, fsm_context)

    state = await fsm_context.get_state()
    assert state == AdminActions.waiting_for_admin_to_add
    mock_message.answer.assert_called_once()

@pytest.mark.asyncio
async def test_add_admin_start_handler_not_owner(mock_message, fsm_context):
    """Тестує add_admin_start_handler, коли користувач не є власником."""
    mock_message.from_user.id = ADMIN_ID

    await add_admin_start_handler(mock_message, fsm_context)

    state = await fsm_context.get_state()
    assert state is None
    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_remove_admin_start_handler(mock_message, fsm_context):
    """Тестує remove_admin_start_handler."""
    mock_message.from_user.id = OWNER_ID

    await remove_admin_start_handler(mock_message, fsm_context)

    state = await fsm_context.get_state()
    assert state == AdminActions.waiting_for_admin_to_remove
    mock_message.answer.assert_called_once()

@pytest.mark.asyncio
async def test_remove_admin_start_handler_not_owner(mock_message, fsm_context):
    """Тестує remove_admin_start_handler, коли користувач не є власником."""
    mock_message.from_user.id = ADMIN_ID

    await remove_admin_start_handler(mock_message, fsm_context)

    state = await fsm_context.get_state()
    assert state is None
    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
@patch("handlers.admin.list_admins", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_list_admins_handler(mock_list_admins, mock_message):
    """Тестує list_admins_handler."""
    mock_message.from_user.id = OWNER_ID
    mock_list_admins.return_value = [{"user_id": ADMIN_ID, "role": "admin"}]

    await list_admins_handler(mock_message)

    mock_message.answer.assert_called_once()
    assert f"<code>{ADMIN_ID}</code>" in mock_message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_list_admins_handler_not_owner(mock_message):
    """Тестує list_admins_handler, коли користувач не є власником."""
    mock_message.from_user.id = ADMIN_ID

    await list_admins_handler(mock_message)

    mock_message.answer.assert_not_called()


@pytest.mark.asyncio
@patch("handlers.admin.list_admins", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_list_admins_handler_empty(mock_list_admins, mock_message):
    """Тестує list_admins_handler з порожнім списком адмінів."""
    mock_message.from_user.id = OWNER_ID
    mock_list_admins.return_value = []

    await list_admins_handler(mock_message)

    mock_message.answer.assert_called_once_with("Список адмінів порожній.")


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_cancel_fsm_handler(mock_message, fsm_context):
    """Тестує cancel_fsm_handler."""
    mock_message.from_user.id = OWNER_ID
    await fsm_context.set_state(AdminActions.waiting_for_admin_to_add)

    await cancel_fsm_handler(mock_message, fsm_context)

    state = await fsm_context.get_state()
    assert state is None
    mock_message.answer.assert_called_once_with("Дію скасовано.", reply_markup=get_admin_menu(True))


@pytest.mark.asyncio
@patch("handlers.admin.add_admin", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_add_admin_handler_by_id(mock_add_admin, mock_message, fsm_context):
    """Тестує process_add_admin_handler з ID."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = str(USER_ID)
    mock_message.forward_from = None
    mock_add_admin.return_value = True

    await process_add_admin_handler(mock_message, fsm_context)

    mock_add_admin.assert_called_once_with(USER_ID)
    mock_message.answer.assert_called_once()
    assert f"<code>{USER_ID}</code>" in mock_message.answer.call_args[0][0]
    state = await fsm_context.get_state()
    assert state is None

@pytest.mark.asyncio
@patch("handlers.admin.add_admin", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_add_admin_handler_already_admin(mock_add_admin, mock_message, fsm_context):
    """Тестує process_add_admin_handler, коли користувач вже є адміном."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = str(ADMIN_ID)
    mock_message.forward_from = None
    mock_add_admin.return_value = False

    await process_add_admin_handler(mock_message, fsm_context)

    mock_add_admin.assert_called_once_with(ADMIN_ID)
    mock_message.answer.assert_called_once()
    assert "вже є адміном" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("handlers.admin.add_admin", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_add_admin_handler_forward(mock_add_admin, mock_message, fsm_context):
    """Тестує process_add_admin_handler з пересланим повідомленням."""
    mock_message.from_user.id = OWNER_ID
    mock_message.forward_from = MagicMock()
    mock_message.forward_from.id = USER_ID
    mock_add_admin.return_value = True

    await process_add_admin_handler(mock_message, fsm_context)

    mock_add_admin.assert_called_once_with(USER_ID)
    mock_message.answer.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_add_admin_handler_invalid(mock_message, fsm_context):
    """Тестує process_add_admin_handler з невірними даними."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = "invalid"
    mock_message.forward_from = None

    await process_add_admin_handler(mock_message, fsm_context)

    mock_message.answer.assert_called_once_with(
        "Невірний формат. Надішліть ID або перешліть повідомлення."
    )


@pytest.mark.asyncio
@patch("handlers.admin.remove_admin", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_remove_admin_handler(mock_remove_admin, mock_message, fsm_context):
    """Тестує process_remove_admin_handler."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = str(ADMIN_ID)
    mock_remove_admin.return_value = True

    await process_remove_admin_handler(mock_message, fsm_context)

    mock_remove_admin.assert_called_once_with(ADMIN_ID)
    mock_message.answer.assert_called_once()
    assert f"<code>{ADMIN_ID}</code>" in mock_message.answer.call_args[0][0]
    state = await fsm_context.get_state()
    assert state is None

@pytest.mark.asyncio
@patch("handlers.admin.remove_admin", new_callable=AsyncMock)
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_remove_admin_handler_not_admin(mock_remove_admin, mock_message, fsm_context):
    """Тестує process_remove_admin_handler, коли користувач не є адміном."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = str(USER_ID)
    mock_remove_admin.return_value = False

    await process_remove_admin_handler(mock_message, fsm_context)

    mock_remove_admin.assert_called_once_with(USER_ID)
    mock_message.answer.assert_called_once()
    assert "не знайдено серед адмінів" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
@patch("handlers.admin.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_process_remove_admin_handler_invalid(mock_message, fsm_context):
    """Тестує process_remove_admin_handler з невірними даними."""
    mock_message.from_user.id = OWNER_ID
    mock_message.text = "invalid"

    await process_remove_admin_handler(mock_message, fsm_context)

    mock_message.answer.assert_called_once_with("Невірний формат. Надішліть ID користувача.")
