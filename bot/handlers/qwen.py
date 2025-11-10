"""Мінімальний handler для тестування Qwen 2.5 7B."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.ollama_service import get_ollama_service
from bot.db.user_settings import register_user_if_not_exists
from bot.core.logging_setup import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(Command("qwen"))
async def qwen_handler(message: Message) -> None:
    """
    Тестування Qwen 2.5 7B.

    Використання: /qwen Привіт! Як справи?
    """
    # Реєстрація користувача
    await register_user_if_not_exists(message.from_user)

    # Отримати текст після команди
    text = message.text.replace("/qwen", "").strip()

    if not text:
        await message.answer(
            "🤖 Qwen 2.5 7B\n\n"
            "Використання: /qwen [текст]\n\n"
            "Приклад:\n"
            "/qwen Привіт! Розкажи про Україну"
        )
        return

    user_id = message.from_user.id
    logger.info("Користувач (ID: %d) відправив запит до Qwen: %s", user_id, text[:50])

    # Статус
    status_msg = await message.answer("⏳ Qwen генерує відповідь...")

    try:
        # Отримати сервіс
        service = get_ollama_service()

        # Перевірити доступність
        if not await service.check_health():
            await status_msg.edit_text(
                "❌ Ollama сервер недоступний!\n\n"
                "Перевір що контейнер запущений:\n"
                "`docker-compose ps ollama`"
            )
            return

        # Генерація
        response = await service.generate_response(
            prompt=text,
            temperature=0.7,
            max_tokens=500
        )

        # Відповідь
        result = f"🤖 **Qwen 2.5 7B:**\n\n{response}"
        await status_msg.edit_text(result, parse_mode="Markdown")

        logger.info("Qwen відповів користувачу (ID: %d)", user_id)

    except Exception as e:
        logger.exception("Помилка Qwen для користувача (ID: %d)", user_id)
        await status_msg.edit_text(
            f"❌ Помилка: {str(e)}\n\n"
            "Можливі причини:\n"
            "- Модель не завантажена\n"
            "- Ollama контейнер не запущений\n"
            "- Немає GPU"
        )
