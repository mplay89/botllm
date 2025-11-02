"""
Централізований модуль для керування кешем в пам'яті.
"""
import logging
import time
from typing import Dict, Any, Optional

from data.database import get_db_connection

logger = logging.getLogger(__name__)

# --- Змінні кешу ---

# Кеш для загальних налаштувань (ключ -> значення)
settings_cache: Dict[str, Any] = {}
SETTINGS_CACHE_TTL = 60  # 1 хвилина

# Кеш для списку моделей
models_cache: Optional[Dict[str, Any]] = None
MODELS_CACHE_TTL = 300  # 5 хвилин

# Кеш для налаштувань користувачів (user_id -> dict)
user_cache: Dict[int, Dict[str, Any]] = {}
USER_CACHE_TTL = 120  # 2 хвилини


# --- Приватні функції для прогріву ---

async def _warm_up_models_cache():
    """Завантажує в кеш список доступних моделей."""
    from data.model_store import get_available_models
    await get_available_models()
    logger.info("Кеш моделей прогріто.")

async def _warm_up_settings_cache():
    """Завантажує в кеш основні налаштування."""
    from data.config_store import get_text_model_name
    await get_text_model_name()
    logger.info("Кеш налаштувань прогріто.")

async def _warm_up_users_cache():
    """Завантажує в кеш дані всіх існуючих користувачів."""
    from data.user_settings import get_user_role, get_user_tts_settings
    async with get_db_connection() as conn:
        user_ids = await conn.fetch("SELECT user_id FROM users")
        if user_ids:
            for record in user_ids:
                user_id = record['user_id']
                await get_user_role(user_id)
                await get_user_tts_settings(user_id)
            logger.info(f"Прогріто кеш для {len(user_ids)} користувачів.")
        else:
            logger.info("Користувачі для прогріву кешу не знайдені.")


# --- Публічна функція для прогріву ---

async def warm_up_caches():
    """
    Завантажує всі основні дані в кеш при старті бота.
    """
    logger.info("Прогрівання кешу...")
    await _warm_up_models_cache()
    await _warm_up_settings_cache()
    await _warm_up_users_cache()
    logger.info("Прогрівання кешу завершено.")


# --- Функції для інвалідації кешу ---

def invalidate_settings_cache(key: Optional[str] = None):
    """Інвалідує весь кеш налаштувань або за конкретним ключем."""
    global settings_cache
    if key is None:
        settings_cache = {}
    elif key in settings_cache:
        del settings_cache[key]

def invalidate_models_cache():
    """Інвалідує кеш списку моделей."""
    global models_cache
    models_cache = None

def invalidate_user_cache(user_id: int, key: Optional[str] = None):
    """Інвалідує кеш для конкретного користувача або за ключем."""
    if user_id in user_cache:
        if key and key in user_cache[user_id]:
            del user_cache[user_id][key]
        elif key is None:
            del user_cache[user_id]
