"""Головний файл для запуску Telegram-бота."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

from config.settings import settings
from data.cache import warm_up_caches
from data.database import init_db
from handlers import admin, general
from handlers import settings as settings_handler
from services.gemini import refresh_available_models
from utils.logging_setup import get_logger, setup_logging

logger = get_logger(__name__)


async def main() -> None:
    """Ініціалізує та запускає бота."""
    await init_db()
    await refresh_available_models()  # Спочатку оновлюємо список моделей з API
    await warm_up_caches()  # Потім прогріваємо кеш

    logger.info("Запуск бота...")

    bot = Bot(
        token=settings.TG_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(settings_handler.router)
    dp.include_router(general.router)  # Цей роутер має бути останнім

    # Повідомлення власнику про запуск
    try:
        await bot.send_message(settings.OWNER_ID, "Бот успішно запущений!")
        logger.info(
            "Надіслано повідомлення про запуск власнику (ID: %d)", settings.OWNER_ID
        )
    except TelegramForbiddenError:
        logger.warning(
            "Не вдалося надіслати повідомлення власнику (ID: %d). "
            "Можливо, бот заблокований.",
            settings.OWNER_ID,
        )
    except Exception:
        logger.exception("Помилка при відправці повідомлення власнику")

    await dp.start_polling(bot)


if __name__ == "__main__":
    setup_logging()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info("Бот зупинений.")
        raise e
