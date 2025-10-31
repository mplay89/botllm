import asyncio
import logging
from typing import Any, Optional

from aiogram import Bot
from google.api_core import exceptions as google_exceptions
from google import genai

from config import runtime_config
from config.settings import settings
from data.config_store import get_api_text_model_name
from data.model_store import sync_models
from data.user_settings import add_message_to_context, get_user_context

logger = logging.getLogger(__name__)

# Ініціалізація клієнта Gemini API
try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception:
    logger.exception("Помилка ініціалізації Gemini Client")
    client = None


async def _get_owner_contact(bot: Bot) -> str:
    """Допоміжна функція для отримання контакту власника.

    Returns:
        Контакт власника у вигляді юзернейму або безпечного посилання.
    """
    try:
        owner = await bot.get_chat(settings.OWNER_ID)
        if owner.username:
            return f"@{owner.username}"
        # Створюємо посилання, яке відкриває чат з користувачем по ID
        return (
            f"[{owner.full_name or 'адміністратора'}]"
            f"(tg://user?id={settings.OWNER_ID})"
        )
    except Exception:
        logger.exception("Не вдалося отримати інформацію про власника")
        # Резервний варіант без посилання
        return "адміністратора"


async def refresh_available_models() -> None:
    """Оновлює список моделей з API та синхронізує його з БД."""
    if not client:
        logger.error(
            "Клієнт Gemini не ініціалізовано. Оновлення моделей неможливе."
        )
        return

    logger.info("Оновлення списку доступних моделей Gemini...")
    try:
        api_models = []
        mandatory_keyword = "gemini-2.5"
        excluded_keywords = ["preview", "audio", "image", "embedding", "vision"]

        for model in client.models.list():
            model_name_lower = model.name.lower()
            if mandatory_keyword in model_name_lower and not any(
                excluded in model_name_lower for excluded in excluded_keywords
            ):
                api_models.append(model.name)

        await sync_models(api_models)
        logger.info("Синхронізовано %d моделей з API до БД.", len(api_models))
    except Exception:
        logger.exception(
            "Не вдалося отримати та синхронізувати список моделей від Gemini API"
        )


class GeminiService:
    """Клас для взаємодії з Gemini API."""

    def __init__(self, user_id: int, bot: Bot) -> None:
        """Ініціалізація сервісу."""
        self.user_id = user_id
        self.bot = bot

    async def _get_error_message(self, error_text: str) -> str:
        """Формує повідомлення про помилку для користувача."""
        owner_contact = await _get_owner_contact(self.bot)
        return (
            f"{error_text}\n\nЯкщо проблема повторюється, "
            f"зверніться до {owner_contact}."
        )

    async def _handle_api_error(self, error: Exception, attempt: int, model_name: str) -> Optional[str]:
        """Обробляє помилки API та повертає повідомлення для користувача."""
        if isinstance(error, asyncio.TimeoutError):
            logger.warning(
                "Таймаут Gemini API для користувача %d (спроба %d/%d).",
                self.user_id,
                attempt + 1,
                runtime_config.API_RETRY_ATTEMPTS,
            )
        elif "NOT_FOUND" in str(error) or "is not found" in str(error):
            logger.exception("Помилка Gemini API: Модель '%s' не знайдено.", model_name)
            await refresh_available_models()
            return "Помилка: обрану модель не знайдено. Оновлено список, спробуйте знову."
        else:
            logger.exception(
                "Невідома помилка Gemini API для користувача %d (спроба %d/%d): %s",
                self.user_id,
                attempt + 1,
                runtime_config.API_RETRY_ATTEMPTS,
                error
            )
        return None

    async def generate_text_response(self, prompt: str) -> str:
        """Надсилає запит до Gemini та повертає текстову відповідь."""
        if not client:
            owner_contact = await _get_owner_contact(self.bot)
            return (
                "Наразі бот не налаштований для роботи з AI-моделями. "
                f"Будь ласка, зверніться до {owner_contact}."
            )

        model_name = await get_api_text_model_name()
        if not model_name:
            return await self._get_error_message("Не вдалося отримати назву моделі для генерації відповіді.")

        context = await get_user_context(self.user_id)
        if len(context) > runtime_config.CONTEXT_MESSAGE_LIMIT:
            context = context[-runtime_config.CONTEXT_MESSAGE_LIMIT :]

        full_contents: list[dict[str, Any]] = [*context, {"role": "user", "parts": [{"text": prompt}]}]

        for attempt in range(runtime_config.API_RETRY_ATTEMPTS):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content, model=model_name, contents=full_contents
                    ),
                    timeout=runtime_config.GEMINI_API_TIMEOUT,
                )
                response_text = response.text
                await add_message_to_context(self.user_id, "user", prompt)
                await add_message_to_context(self.user_id, "model", response_text)
                return response_text
            except Exception as e:
                error_message = await self._handle_api_error(e, attempt, model_name)
                if error_message:
                    return error_message

                if attempt < runtime_config.API_RETRY_ATTEMPTS - 1:
                    delay = runtime_config.API_RETRY_BASE_DELAY * (2**attempt)
                    logger.info("Повторна спроба через %.2f секунд...", delay)
                    await asyncio.sleep(delay)

        logger.error(
            "Всі %d спроб запиту до Gemini API для користувача %d завершилися невдачею.",
            runtime_config.API_RETRY_ATTEMPTS,
            self.user_id,
        )
        return await self._get_error_message(
            "На жаль, сталася помилка під час генерації відповіді після кількох спроб."
        )
