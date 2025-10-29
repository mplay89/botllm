from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums.chat_action import ChatAction

from data.user_settings import register_user_if_not_exists
from keyboards.reply import get_main_menu, get_settings_menu
from services.gemini import GeminiService
from utils.logging_setup import get_logger

router = Router()
logger = get_logger(__name__)


@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обробник команди /start.
    Вітає користувача, реєструє його в БД та відображає головне меню.
    """
    await register_user_if_not_exists(message.from_user)
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    logger.info(f"Користувач {user_name} (ID: {user_id}) запустив бота.")
    
    await message.answer(
        f"Привіт, {user_name}!",
        reply_markup=await get_main_menu(user_id=user_id)
    )


@router.message(F.text == "⚙️ Налаштування")
async def settings_handler(message: Message) -> None:
    """
    Обробник кнопки 'Налаштування'.
    Відображає меню налаштувань.
    """
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    logger.info(f"Користувач (ID: {user_id}) перейшов до налаштувань.")
    await message.answer("Меню налаштувань:", reply_markup=get_settings_menu())


@router.message(F.text == "⬅️ Назад до головного меню")
async def back_to_main_menu_handler(message: Message) -> None:
    """
    Обробник кнопки 'Назад до головного меню'.
    Повертає користувача до головного меню.
    """
    await register_user_if_not_exists(message.from_user)
    user_id = message.from_user.id
    logger.info(f"Користувач (ID: {user_id}) повернувся до головного меню.")
    await message.answer(
        "Головне меню:", reply_markup=await get_main_menu(user_id=user_id)
    )


@router.message(F.text)
async def text_message_handler(message: Message, bot: Bot) -> None:
    """
    Обробник для всіх текстових повідомлень.
    Надсилає текст до Gemini для генерації відповіді.
    """
    await register_user_if_not_exists(message.from_user)
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    prompt = message.text

    logger.info(f"Користувач {user_name} (ID: {user_id}) надіслав текстовий запит.")

    try:
        # Показуємо статус "друкує..."
        await bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

        gemini_service = GeminiService(user_id=user_id, bot=bot)
        
        response_text = await gemini_service.generate_text_response(prompt)
        
        await message.answer(response_text)
        logger.info(f"Надіслано відповідь від Gemini для користувача (ID: {user_id}).")

    except Exception as e:
        logger.error(f"Помилка під час обробки текстового повідомлення для ID {user_id}: {e}", exc_info=True)
        await message.answer("Виникла помилка під час обробки вашого запиту. Спробуйте пізніше.")
