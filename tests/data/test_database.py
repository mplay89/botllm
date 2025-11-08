import asyncio
import socket
from unittest.mock import AsyncMock, patch, call

import pytest

from bot.db.database import init_db

@pytest.mark.asyncio
@patch('bot.db.database.asyncio.sleep', new_callable=AsyncMock)
@patch('bot.db.database.get_db_connection')
async def test_init_db_retries_and_succeeds(mock_get_db_connection, mock_sleep):
    """Тестує, що init_db робить повторні спроби при помилці мережі і врешті-решт спрацьовує."""
    # Налаштовуємо мок, щоб він спочатку викликав помилку, а потім працював успішно
    mock_get_db_connection.side_effect = [
        socket.gaierror,  # Перша спроба
        socket.gaierror,  # Друга спроба
        AsyncMock()      # Третя спроба - успіх
    ]

    await init_db()

    # Перевіряємо, що було 3 спроби підключення
    assert mock_get_db_connection.call_count == 3
    # Перевіряємо, що були очікування між спробами
    mock_sleep.assert_has_calls([call(5), call(5)])

@pytest.mark.asyncio
@patch('bot.db.database.asyncio.sleep', new_callable=AsyncMock)
@patch('bot.db.database.get_db_connection')
async def test_init_db_fails_after_all_retries(mock_get_db_connection, mock_sleep):
    """Тестує, що init_db падає з помилкою після всіх невдалих спроб."""
    # Налаштовуємо мок, щоб він завжди викликав помилку
    mock_get_db_connection.side_effect = socket.gaierror

    # Перевіряємо, що функція врешті-решт викликає виняток
    with pytest.raises(socket.gaierror):
        await init_db()

    # Перевіряємо, що було 5 спроб підключення (за замовчуванням)
    assert mock_get_db_connection.call_count == 5
