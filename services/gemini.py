import asyncio
import logging
import json
import time
from aiogram import Bot

from google import genai
from google.api_core import exceptions as google_exceptions
from config.settings import settings
from config import runtime_config
from data.user_settings import get_user_context, add_message_to_context
from data.config_store import get_api_text_model_name
from data.model_store import sync_models

logger = logging.getLogger(__name__)

# Ініціалізація клієнта Gemini API
try:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Помилка ініціалізації Gemini Client: {e}")
    client = None

# --- Допоміжна функція ---

async def _get_owner_contact(bot: Bot) -> str:
    """
    Допоміжна функція для отримання контакту власника у вигляді
    юзернейму або безпечного посилання.
    """
    try:
        owner = await bot.get_chat(settings.OWNER_ID)
        if owner.username:
            return f"@{owner.username}"
        # Створюємо посилання, яке відкриває чат з користувачем по ID
        return f"[{owner.full_name or 'адміністратора'}](tg://user?id={settings.OWNER_ID})"
    except Exception as e:
        logger.error(f"Не вдалося отримати інформацію про власника: {e}")
        # Резервний варіант без посилання
        return "адміністратора"

# --- Керування списком моделей ---

async def refresh_available_models():
    """
    Оновлює список доступних моделей з API та синхронізує його з базою даних.
    """
    if not client:
        logger.error("Клієнт Gemini не ініціалізовано. Оновлення моделей неможливе.")
        return
        
    logger.info("Оновлення списку доступних моделей Gemini (асинхронно)...")
    try:
        api_models = []
        MANDATORY_KEYWORD = "gemini-2.5"
        EXCLUDED_KEYWORDS = ["preview", "audio", "image", "embedding", "vision"]
        
        async for model in await client.aio.models.list():
            model_name_lower = model.name.lower()
            if (MANDATORY_KEYWORD in model_name_lower and 
                not any(excluded in model_name_lower for excluded in EXCLUDED_KEYWORDS)):
                api_models.append(model.name)
        
        await sync_models(api_models)
        logger.info(f"Синхронізовано {len(api_models)} моделей з API до БД.")
    except Exception as e:
        logger.error(f"Не вдалося отримати та синхронізувати список моделей від Gemini API: {e}")

# --- Сервіс Gemini ---

class GeminiService:
    """
    Клас для взаємодії з Gemini API.
    """
    def __init__(self, user_id: int, bot: Bot):
        self.user_id = user_id
        self.bot = bot

    async def _get_error_message(self, error_text: str) -> str:
        """Формує повідомлення про помилку для користувача."""
        owner_contact = await _get_owner_contact(self.bot)
        return f"{error_text}\n\nЯкщо проблема повторюється, зверніться до {owner_contact}."

    async def generate_text_response(self, prompt: str) -> str:
        """
        Надсилає запит до Gemini, використовуючи контекст з БД, та повертає текстову відповідь.
        Реалізовано таймаути та повторні спроби з експоненційною затримкою.
        """
        if not client:
            return await self._get_error_message("Помилка: Клієнт Gemini API не налаштовано.")

        model_name = get_api_text_model_name()
        
        if not model_name:
            owner_contact = await _get_owner_contact(self.bot)
            return f"Наразі не налаштовано жодної AI-моделі. Будь ласка, зверніться до {owner_contact}."

        # Отримуємо контекст з бази даних
        context = await get_user_context(self.user_id)
        
        # Обрізаємо контекст, якщо він занадто великий
        if len(context) > runtime_config.CONTEXT_MESSAGE_LIMIT:
            context = context[-runtime_config.CONTEXT_MESSAGE_LIMIT:]

        full_contents = context + [{'role': 'user', 'parts': [{'text': prompt}]}]

        for attempt in range(runtime_config.API_RETRY_ATTEMPTS):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.models.generate_content,
                        model=model_name,
                        contents=full_contents
                    ),
                    timeout=runtime_config.GEMINI_API_TIMEOUT
                )
                
                response_text = response.text
                
                # Зберігаємо запит та відповідь у контекст в БД
                await add_message_to_context(self.user_id, 'user', prompt)
                await add_message_to_context(self.user_id, 'model', response_text)
                
                return response_text
            except asyncio.TimeoutError:
                logger.warning(f"Таймаут Gemini API для користувача {self.user_id} (спроба {attempt + 1}/{runtime_config.API_RETRY_ATTEMPTS}).")
            except google_exceptions.ResourceExhausted as e:
                logger.warning(f"Вичерпано квоту Gemini API для користувача {self.user_id} (спроба {attempt + 1}/{runtime_config.API_RETRY_ATTEMPTS}): {e}")
            except google_exceptions.ServiceUnavailable as e:
                logger.warning(f"Сервіс Gemini API недоступний для користувача {self.user_id} (спроба {attempt + 1}/{runtime_config.API_RETRY_ATTEMPTS}): {e}")
            except Exception as e:
                if "NOT_FOUND" in str(e) or "is not found" in str(e):
                    logger.error(f"Помилка Gemini API: Модель '{model_name}' не знайдено. {e}")
                    await refresh_available_models()
                    return "Помилка: обрану модель не знайдено. Список моделей оновлено, спробуйте обрати іншу в адмін-панелі."
                logger.error(f"Невідома помилка Gemini API для користувача {self.user_id} (спроба {attempt + 1}/{runtime_config.API_RETRY_ATTEMPTS}): {e}", exc_info=True)
            
            if attempt < runtime_config.API_RETRY_ATTEMPTS - 1:
                delay = runtime_config.API_RETRY_BASE_DELAY * (2 ** attempt)
                logger.info(f"Повторна спроба через {delay:.2f} секунд...")
                await asyncio.sleep(delay)
        
        logger.error(f"Всі {runtime_config.API_RETRY_ATTEMPTS} спроб запиту до Gemini API для користувача {self.user_id} завершилися невдачею.")
        return await self._get_error_message("На жаль, сталася помилка під час генерації відповіді після кількох спроб.")