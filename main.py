"""Головний файл для запуску Telegram-бота."""

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError

from config.settings import settings
from data.config_store import get_text_model_name, set_text_model
from data.database import init_db
from data.model_store import get_available_models
from handlers import admin, general
from handlers import settings as settings_handler
from services.gemini import refresh_available_models
from utils.logging_setup import get_logger, setup_logging

logger = get_logger(__name__)


async def _check_and_set_model() -> None:
    """Перевіряє та встановлює активну модель AI під час старту."""
    available_models = await get_available_models()
    current_model = await get_text_model_name()
    if not current_model or current_model not in available_models:
        if available_models:
            logger.warning(
                "Поточна модель '%s' недійсна. Встановлюємо першу доступну: %s",
                current_model,
                available_models[0],
            )
            await set_text_model(available_models[0])
        else:
            logger.error("Немає доступних моделей AI для встановлення.")


async def main() -> None:
    """Ініціалізує та запускає бота."""
    await init_db()
    await refresh_available_models()
    await _check_and_set_model()

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
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинений.")
