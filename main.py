import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError

from config.settings import settings
from data.database import init_db
from data.model_store import get_available_models
from data.config_store import get_text_model_name, set_text_model
from handlers import general, settings as settings_handler, admin
from services.gemini import refresh_available_models
from utils.logging_setup import setup_logging, get_logger


async def main() -> None:
    """Ініціалізує та запускає бота."""
    logger = get_logger(__name__)

    # Ініціалізуємо базу даних
    await init_db()
    
    # При старті оновлюємо список доступних моделей
    await refresh_available_models()

    # Перевіряємо та встановлюємо активну модель, щоб уникнути помилок
    available_models = await get_available_models()
    current_model = await get_text_model_name()
    if not current_model or current_model not in available_models:
        if available_models:
            logger.warning(f"Поточна модель '{current_model}' недійсна. Встановлюємо першу доступну: {available_models[0]}")
            await set_text_model(available_models[0])
        else:
            logger.error("Немає доступних моделей AI для встановлення.")

    logger.info("Запуск бота...")

    bot = Bot(token=settings.TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(settings_handler.router)
    dp.include_router(general.router) # Цей роутер має бути останнім, бо він ловить весь текст

    # Повідомлення власнику про запуск
    try:
        await bot.send_message(settings.OWNER_ID, "Бот успішно запущений!")
        logger.info(f"Надіслано повідомлення про запуск власнику (ID: {settings.OWNER_ID})")
    except TelegramForbiddenError:
        logger.warning(f"Не вдалося надіслати повідомлення власнику (ID: {settings.OWNER_ID}). Можливо, бот заблокований.")
    except Exception as e:
        logger.error(f"Помилка при відправці повідомлення власнику: {e}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот зупинений.")
