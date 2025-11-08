"""Обробники для меню налаштувань."""

from aiogram import F, Router
from aiogram.types import Message

from bot.db.user_settings import (
    clear_user_context,
    register_user_if_not_exists,
    update_user_tts_enabled,
    update_user_tts_voice,
)
from bot.core.logging_setup import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(F.text.startswith("🗣️ Голос"))
async def change_voice_handler(message: Message) -> None:
    """Обробляє кнопки зміни голосу TTS."""
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id

    new_voice = "male" if message.text == "🗣️ Голос (Чоловічий)" else "female"
    await update_user_tts_voice(user_id, new_voice)

    logger.info("Користувач (ID: %d) змінив голос TTS на %s.", user_id, new_voice)
    display_voice = "чоловічий" if new_voice == "male" else "жіночий"
    await message.answer(f"Голос змінено на {display_voice}.")


@router.message(F.text.startswith(("✅ Увімкнути TTS", "❌ Вимкнути TTS")))
async def toggle_tts_handler(message: Message) -> None:
    """Обробляє кнопки увімкнення/вимкнення TTS."""
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id

    new_status = message.text == "✅ Увімкнути TTS"
    await update_user_tts_enabled(user_id, new_status)

    status_text = "увімкнув" if new_status else "вимкнув"
    logger.info("Користувач (ID: %d) %s TTS.", user_id, status_text)
    display_status = "увімкнено" if new_status else "вимкнено"
    await message.answer(f"TTS {display_status}.")


@router.message(F.text == "🗑️ Очистити контекст")
async def clear_context_handler(message: Message) -> None:
    """Обробляє кнопку очищення контексту."""
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id

    await clear_user_context(user_id)

    logger.info("Користувач (ID: %d) очистив історію контексту.", user_id)
    await message.answer("Історію контексту очищено.")
