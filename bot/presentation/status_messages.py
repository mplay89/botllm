"""
Утиліти для динамічних статус-повідомлень.

Статус-повідомлення складається з двох рядків:
- Рядок 1: Завжди "**Очікуйте...**"
- Рядок 2: Етап обробки (динамічний)
"""

from aiogram.types import Message
from bot.core.logging_setup import get_logger

logger = get_logger(__name__)


async def send_status(message: Message, stage: str) -> Message:
    """
    Відправляє початкове статус-повідомлення.

    Args:
        message: Вхідне повідомлення користувача
        stage: Опис поточного етапу (наприклад, "Генерація відповіді.")

    Returns:
        Message: Об'єкт відправленого статус-повідомлення
    """
    status_text = f"**Очікуйте...**\n{stage}"
    status_msg = await message.answer(status_text)
    logger.debug("Відправлено статус-повідомлення для користувача ID: %d", message.from_user.id)
    return status_msg


async def update_status(status_msg: Message, stage: str) -> None:
    """
    Оновлює другий рядок статус-повідомлення.

    Args:
        status_msg: Об'єкт статус-повідомлення (повернутий send_status())
        stage: Новий опис етапу
    """
    status_text = f"**Очікуйте...**\n{stage}"
    try:
        await status_msg.edit_text(status_text)
        logger.debug("Оновлено статус-повідомлення: %s", stage)
    except Exception:
        logger.exception("Помилка при оновленні статус-повідомлення")


async def delete_status(status_msg: Message) -> None:
    """
    Видаляє статус-повідомлення.

    Args:
        status_msg: Об'єкт статус-повідомлення (повернутий send_status())
    """
    try:
        await status_msg.delete()
        logger.debug("Видалено статус-повідомлення")
    except Exception:
        logger.exception("Помилка при видаленні статус-повідомлення")
