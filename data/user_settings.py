import logging
from typing import Dict, Any, List, Optional
from aiogram.types import User
from data.database import get_db_connection
from config.settings import settings

logger = logging.getLogger(__name__)

# --- Керування користувачами та ролями ---

async def register_user_if_not_exists(tg_user: User):
    """Перевіряє, чи існує користувач у БД. Якщо ні, створює новий запис.
    Автоматично призначає роль 'owner', якщо ID співпадає з OWNER_ID.
    """
    async with get_db_connection() as conn:
        user_data = await conn.fetchrow("SELECT user_id, role FROM users WHERE user_id = $1", tg_user.id)

        if user_data is None:
            role = 'owner' if tg_user.id == settings.OWNER_ID else 'user'
            await conn.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, role) "
                "VALUES ($1, $2, $3, $4, $5)",
                tg_user.id, tg_user.username, tg_user.full_name, tg_user.last_name, role
            )
            logger.info(
                f"Новий користувач (ID: {tg_user.id}, Name: {tg_user.full_name}, "
                f"Role: {role}) зареєстрований у базі даних."
            )

        elif tg_user.id == settings.OWNER_ID and user_data['role'] != 'owner':
            await update_user_role(tg_user.id, 'owner')
            logger.info(f"Роль власника (ID: {tg_user.id}) відновлено.")


async def get_user_role(user_id: int) -> Optional[str]:
    """Повертає роль користувача з БД."""
    async with get_db_connection() as conn:
        return await conn.fetchval("SELECT role FROM users WHERE user_id = $1", user_id)

async def update_user_role(user_id: int, role: str):
    """Оновлює роль користувача в БД."""
    async with get_db_connection() as conn:
        await conn.execute("UPDATE users SET role = $1 WHERE user_id = $2", role, user_id)
        logger.info(f"Роль користувача (ID: {user_id}) змінено на '{role}'.")

# --- Налаштування TTS ---

async def get_user_tts_settings(user_id: int) -> Dict[str, Any]:
    """Отримує налаштування TTS (enabled, voice) для користувача з БД.
    """
    async with get_db_connection() as conn:
        row = await conn.fetchrow(
            "SELECT tts_enabled, tts_voice FROM users WHERE user_id = $1", user_id
        )
        if row:
            return {
                "tts_enabled": bool(row['tts_enabled']),
                "tts_voice": row['tts_voice'],
            }
    return {"tts_enabled": True, "tts_voice": "female"} # Значення за замовчуванням

async def update_user_tts_enabled(user_id: int, enabled: bool):
    """Оновлює статус TTS (увімкнено/вимкнено) для користувача."""
    async with get_db_connection() as conn:
        await conn.execute("UPDATE users SET tts_enabled = $1 WHERE user_id = $2", enabled, user_id)

async def update_user_tts_voice(user_id: int, voice: str):
    """Оновлює голос TTS для користувача."""
    async with get_db_connection() as conn:
        await conn.execute("UPDATE users SET tts_voice = $1 WHERE user_id = $2", voice, user_id)

# --- Контекст чату ---

async def get_user_context(user_id: int) -> List[Dict[str, Any]]:
    """Отримує історію чату (контекст) для користувача з БД.
    """
    context = []
    async with get_db_connection() as conn:
        rows = await conn.fetch(
            "SELECT role, content FROM chat_history WHERE user_id = $1 ORDER BY timestamp ASC",
            user_id
        )
        for row in rows:
            context.append({'role': row['role'], 'parts': [{'text': row['content']}]})
    return context

async def add_message_to_context(user_id: int, role: str, content: str):
    """Додає нове повідомлення до історії чату користувача.
    """
    async with get_db_connection() as conn:
        await conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content
        )

async def clear_user_context(user_id: int):
    """Очищує історію чату для користувача.
    """
    async with get_db_connection() as conn:
        await conn.execute("DELETE FROM chat_history WHERE user_id = $1", user_id)

