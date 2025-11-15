import logging
import time
from typing import Optional

from bot.db.database import get_db_connection
from bot.db.model_store import get_available_models
from bot.db import cache

logger = logging.getLogger(__name__)

CONFIG_KEY_TEXT_MODEL = "current_text_model"

# --- Універсальні функції ---

async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Отримує значення налаштування за ключем з БД з кешуванням."""
    cached = cache.settings_cache.get(key)
    if cached and (time.time() - cached['timestamp']) < cache.SETTINGS_CACHE_TTL:
        return cached['value']

    async with get_db_connection() as conn:
        value = await conn.fetchval("SELECT value FROM bot_config WHERE key = $1", key)
        if value is not None:
            cache.settings_cache[key] = {'timestamp': time.time(), 'value': value}
        return value if value is not None else default

async def set_setting(key: str, value: str):
    """Встановлює або оновлює значення налаштування в БД та інвалідує кеш."""
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO bot_config (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, key, value)
    cache.invalidate_settings_cache(key)

# --- Спеціалізовані функції для моделі ---

async def get_text_model_name() -> str:
    """Повертає поточне ім'я текстової моделі для API."""
    model_name = await get_setting(CONFIG_KEY_TEXT_MODEL, default="")
    return model_name or ""

async def set_text_model(model_name: str) -> bool:
    """Встановлює нову текстову модель за її повним іменем."""
    available_models = await get_available_models()
    if model_name in available_models:
        await set_setting(CONFIG_KEY_TEXT_MODEL, model_name)
        logger.info(f"Глобальну модель змінено на: {model_name}")
        return True
    logger.warning(f"Спроба встановити недоступну модель: {model_name}")
    return False

# Це аліас для ясності
get_api_text_model_name = get_text_model_name
