import asyncio
import logging
import sys

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.settings import settings

# Налаштовуємо логування для виводу тільки помилок
logging.basicConfig(level=logging.ERROR)

async def main():
    """
    Перевіряє стан бота, роблячи запит до Telegram API.
    Виходить з кодом 0, якщо бот здоровий, і з кодом 1, якщо є проблеми.
    """
    bot_token = settings.TG_TOKEN

    if not bot_token:
        # Це перевірка на випадок, якщо змінна в .env порожня
        logging.error("Помилка: Не вдалося завантажити TG_TOKEN з файлу налаштувань.")
        sys.exit(1)

    bot = Bot(token=bot_token)
    try:
        # Робимо простий запит до API, щоб перевірити токен та з'єднання
        await bot.get_me()
        sys.exit(0)
    except TelegramAPIError as e:
        logging.error(f"Помилка API Telegram під час перевірки стану: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Невідома помилка під час перевірки стану: {e}")
        sys.exit(1)
    finally:
        # Закриваємо сесію бота, щоб уникнути витоків
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
