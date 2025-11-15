"""
Утиліти для роботи з повідомленнями Telegram.
"""

from aiogram.types import Message
from bot.core.logging_setup import get_logger

logger = get_logger(__name__)

# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096


async def send_long_message(message: Message, text: str) -> None:
    """
    Відправляє довге повідомлення, розбиваючи його на частини якщо потрібно.

    Args:
        message: Об'єкт вхідного повідомлення
        text: Текст для відправки
    """
    if len(text) <= MAX_MESSAGE_LENGTH:
        await message.answer(text)
        return

    # Розбиваємо на частини
    parts = []
    while text:
        if len(text) <= MAX_MESSAGE_LENGTH:
            parts.append(text)
            break

        # Шукаємо останній перенос рядка перед лімітом
        split_pos = text.rfind('\n', 0, MAX_MESSAGE_LENGTH)

        # Якщо не знайшли перенос рядка, шукаємо пробіл
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, MAX_MESSAGE_LENGTH)

        # Якщо і пробіл не знайшли, просто ріжемо по ліміту
        if split_pos == -1:
            split_pos = MAX_MESSAGE_LENGTH

        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    # Відправляємо частини
    logger.info("Розбито довге повідомлення на %d частин", len(parts))
    for i, part in enumerate(parts, 1):
        await message.answer(part)
        logger.debug("Відправлено частину %d/%d", i, len(parts))
