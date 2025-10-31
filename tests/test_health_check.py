import asyncio
import sys
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.exceptions import TelegramAPIError

# Додаємо шлях до health_check.py, щоб можна було його імпортувати
sys.path.append('.')

from health_check import main as health_check_main

@pytest.mark.asyncio
@patch('health_check.os.getenv')
@patch('health_check.Bot')
async def test_health_check_success(mock_bot, mock_getenv):
    """Тестує випадок, коли перевірка стану проходить успішно."""
    # Налаштовуємо моки
    mock_getenv.return_value = 'fake_token'
    mock_bot_instance = mock_bot.return_value
    mock_bot_instance.get_me = AsyncMock()
    mock_bot_instance.session.close = AsyncMock()

    # Використовуємо pytest.raises для перевірки виклику sys.exit(0)
    with pytest.raises(SystemExit) as e:
        await health_check_main()
    
    # Перевіряємо, що код виходу 0 (успіх)
    assert e.type == SystemExit
    assert e.value.code == 0

    # Перевіряємо, що get_me було викликано
    mock_bot_instance.get_me.assert_awaited_once()
    # Перевіряємо, що сесія була закрита
    mock_bot_instance.session.close.assert_awaited_once()

@pytest.mark.asyncio
@patch('health_check.os.getenv')
@patch('health_check.Bot')
async def test_health_check_api_error(mock_bot, mock_getenv):
    """Тестує випадок, коли Telegram API повертає помилку."""
    # Налаштовуємо моки
    mock_getenv.return_value = 'fake_token'
    mock_bot_instance = mock_bot.return_value
    mock_bot_instance.get_me = AsyncMock(side_effect=TelegramAPIError(method='getMe', message='Error'))
    mock_bot_instance.session.close = AsyncMock()

    # Перевіряємо, що скрипт завершується з кодом 1
    with pytest.raises(SystemExit) as e:
        await health_check_main()
    
    assert e.type == SystemExit
    assert e.value.code == 1

    # Перевіряємо, що get_me було викликано
    mock_bot_instance.get_me.assert_awaited_once()
    # Перевіряємо, що сесія була закрита
    mock_bot_instance.session.close.assert_awaited_once()

@pytest.mark.asyncio
@patch('health_check.os.getenv')
async def test_health_check_no_token(mock_getenv):
    """Тестує випадок, коли токен бота не знайдено."""
    # Налаштовуємо мок, щоб він повертав None
    mock_getenv.return_value = None

    # Перевіряємо, що скрипт завершується з кодом 1
    with pytest.raises(SystemExit) as e:
        await health_check_main()
    
    assert e.type == SystemExit
    assert e.value.code == 1
