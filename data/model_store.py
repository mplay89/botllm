import logging
from typing import List
from data.database import get_db_connection

logger = logging.getLogger(__name__)

def _get_model_priority(model_name: str) -> int:
    """Розраховує пріоритет сортування для моделі."""
    name = model_name.lower()
    if 'flash-lite' in name:
        return 1
    if 'flash' in name and 'lite' not in name:
        return 2
    if 'pro' in name:
        return 3
    return 100 # Пріоритет за замовчуванням для інших моделей

async def sync_models(api_models: List[str]):
    """Синхронізує список моделей з API з базою даних.
    Якщо списки відрізняються, повністю перезаписує таблицю в БД.
    """
    async with get_db_connection() as conn:
        db_rows = await conn.fetch("SELECT model_name FROM ai_models ORDER BY model_name ASC")
        db_models = [row['model_name'] for row in db_rows]

        if set(db_models) == set(api_models):
            logger.info("Список моделей в БД актуальний. Оновлення не потрібне.")
            return

        logger.info("Списки моделей відрізняються. Повне оновлення таблиці ai_models...")

        async with conn.transaction():
            await conn.execute("DELETE FROM ai_models")
            for model_name in api_models:
                priority = _get_model_priority(model_name)
                await conn.execute(
                    "INSERT INTO ai_models (model_name, priority) VALUES ($1, $2)",
                    model_name, priority
                )

        logger.info(f"Таблицю ai_models повністю оновлено. Додано {len(api_models)} моделей.")

async def get_available_models() -> List[str]:
    """Повертає список активних моделей AI з бази даних, відсортований за пріоритетом.
    """
    async with get_db_connection() as conn:
        rows = await conn.fetch(
            "SELECT model_name FROM ai_models WHERE is_active = TRUE ORDER BY priority ASC, model_name ASC"
        )
        return [row['model_name'] for row in rows]
