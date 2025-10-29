from aiogram import F, Router
from aiogram.types import Message

from data.user_settings import (
    update_user_tts_voice,
    update_user_tts_enabled,
    clear_user_context,
    register_user_if_not_exists
)
from utils.logging_setup import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(F.text.startswith("🗣️ Голос"))
async def change_voice_handler(message: Message):
    """
    Обробник для кнопок зміни голосу TTS.
    """
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    
    new_voice = "male" if message.text == "🗣️ Голос (Чоловічий)" else "female"
    await update_user_tts_voice(user_id, new_voice)

    logger.info(f"Користувач (ID: {user_id}) змінив голос TTS на {new_voice}.")
    await message.answer(f"Голос змінено на {'чоловічий' if new_voice == 'male' else 'жіночий'}.")


@router.message(F.text.startswith(("✅ Увімкнути TTS", "❌ Вимкнути TTS")))
async def toggle_tts_handler(message: Message):
    """
    Обробник для кнопок увімкнення/вимкнення TTS.
    """
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    
    new_status = message.text == "✅ Увімкнути TTS"
    await update_user_tts_enabled(user_id, new_status)

    status_text = "увімкнув" if new_status else "вимкнув"
    logger.info(f"Користувач (ID: {user_id}) {status_text} TTS.")
    await message.answer(f"TTS {'увімкнено' if new_status else 'вимкнено'}.")


@router.message(F.text == "🗑️ Очистити контекст")
async def clear_context_handler(message: Message):
    """
    Обробник для кнопки очищення контексту.
    """
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    
    await clear_user_context(user_id)

    logger.info(f"Користувач (ID: {user_id}) очистив історію контексту.")
    await message.answer("Історію контексту очищено.")
