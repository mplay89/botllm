import asyncpg
import logging
from contextlib import asynccontextmanager

from config.settings import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_db_connection():
    """Надає контекстний менеджер для отримання з'єднання з пулу до БД."""
    conn = None
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error(f"Помилка підключення до бази даних: {e}")
        raise
    finally:
        if conn:
            await conn.close()

async def init_db():
    """
    Ініціалізує базу даних та створює таблиці, якщо вони не існують.
    """
    try:
        async with get_db_connection() as conn:
            # Таблиця для налаштувань користувачів
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    tts_enabled BOOLEAN DEFAULT TRUE,
                    tts_voice TEXT DEFAULT 'female',
                    role TEXT DEFAULT 'user'
                )
            """)

            # Таблиця для доступних моделей AI
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_models (
                    id SERIAL PRIMARY KEY,
                    model_name TEXT NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    priority INTEGER DEFAULT 100
                )
            """)

            # Таблиця для глобальних налаштувань бота (ключ-значення)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Таблиця для нагадувань (плейсхолдер)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    reminder_text TEXT NOT NULL,
                    reminder_time TIMESTAMPTZ NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

            # Таблиця для історії чату (контексту)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Таблиця для довготривалої пам'яті
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS long_term_memory (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    memory_key TEXT NOT NULL,
                    memory_value TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # Таблиця для статистики використання
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    request_type TEXT NOT NULL, -- 'text', 'voice_in', 'voice_out', 'image'
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                )
            """)

        logger.info("Базу даних PostgreSQL успішно ініціалізовано.")
    except Exception as e:
        logger.error(f"Помилка під час ініціалізації бази даних PostgreSQL: {e}")
        raise
