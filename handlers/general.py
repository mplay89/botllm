"""Головний модуль обробки повідомлень та команд."""

from aiogram import Bot, F, Router
from aiogram.enums.chat_action import ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message

from data.user_settings import register_user_if_not_exists
from keyboards.reply import get_main_menu, get_settings_menu
from services.gemini import GeminiService
from utils.logging_setup import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обробляє команду /start."""
    await register_user_if_not_exists(message.from_user)

    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logger.info("Користувач %s (ID: %d) запустив бота.", user_name, user_id)

    await message.answer(
        f"Привіт, {user_name}!",
        reply_markup=await get_main_menu(user_id=user_id),
    )


@router.message(F.text == "⚙️ Налаштування")
async def settings_handler(message: Message) -> None:
    """Обробляє кнопку 'Налаштування'."""
    await register_user_if_not_exists(message.from_user)
    logger.info("Користувач (ID: %d) перейшов до налаштувань.", message.from_user.id)
    await message.answer("Меню налаштувань:", reply_markup=get_settings_menu())


@router.message(F.text == "⬅️ Назад до головного меню")
async def back_to_main_menu_handler(message: Message) -> None:
    """Обробляє кнопку 'Назад до головного меню'."""
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    logger.info("Користувач (ID: %d) повернувся до головного меню.", user_id)
    await message.answer(
        "Головне меню:", reply_markup=await get_main_menu(user_id=user_id)
    )


@router.message(F.text)
async def text_message_handler(message: Message, bot: Bot) -> None:
    """Обробляє всі текстові повідомлення."""
    await register_user_if_not_exists(message.from_user)

    user_id = message.from_user.id
    prompt = message.text

    logger.info(
        "Користувач %s (ID: %d) надіслав текстовий запит.",
        message.from_user.full_name,
        user_id,
    )

    try:
        await bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)
        gemini_service = GeminiService(user_id=user_id, bot=bot)
        response_text = await gemini_service.generate_text_response(prompt)

        await message.answer(response_text)
        logger.info("Надіслано відповідь від Gemini для користувача (ID: %d).", user_id)

    except Exception:
        logger.exception(
            "Помилка під час обробки текстового повідомлення для ID %d", user_id
        )
        await message.answer(
            "Виникла помилка під час обробки вашого запиту. Спробуйте пізніше."
        )
