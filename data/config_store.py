import logging
from typing import Optional

from data.database import get_db_connection
from data.model_store import get_available_models

logger = logging.getLogger(__name__)

CONFIG_KEY_TEXT_MODEL = "current_text_model"

# --- Універсальні функції ---

async def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Отримує значення налаштування за ключем з БД."""
    async with get_db_connection() as conn:
        value = await conn.fetchval("SELECT value FROM bot_config WHERE key = $1", key)
        return value if value is not None else default

async def set_setting(key: str, value: str):
    """Встановлює або оновлює значення налаштування в БД."""
    async with get_db_connection() as conn:
        # Використовуємо INSERT ... ON CONFLICT для атомарного оновлення або вставки
        await conn.execute("""
            INSERT INTO bot_config (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, key, value)

# --- Спеціалізовані функції для моделі ---

async def get_text_model_name() -> str:
    """Повертає поточне ім'я текстової моделі для API."""
    return await get_setting(CONFIG_KEY_TEXT_MODEL, default="")

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
