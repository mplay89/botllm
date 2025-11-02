"""Модуль для створення reply-клавіатур."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from data.admin_store import is_admin


async def get_main_menu(user_id: int | None = None) -> ReplyKeyboardMarkup:
    """
    Повертає клавіатуру головного меню.

    Додає кнопку адмін-панелі, якщо користувач є адміном.
    """
    keyboard = [
        [KeyboardButton(text="⚙️ Налаштування")],
    ]

    if user_id and await is_admin(user_id):
        # Вставляємо кнопку адмін-панелі на початок
        keyboard.insert(0, [KeyboardButton(text="👑 Адмін-панель")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_settings_menu() -> ReplyKeyboardMarkup:
    """Повертає клавіатуру меню налаштувань."""
    keyboard = [
        [
            KeyboardButton(text="🗣️ Голос (Чоловічий)"),
            KeyboardButton(text="🗣️ Голос (Жіночий)"),
        ],
        [
            KeyboardButton(text="✅ Увімкнути TTS"),
            KeyboardButton(text="❌ Вимкнути TTS"),
        ],
        [KeyboardButton(text="🗑️ Очистити контекст")],
        [KeyboardButton(text="⬅️ Назад до головного меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_menu(is_owner: bool) -> ReplyKeyboardMarkup:
    """Повертає клавіатуру адмін-панелі."""
    keyboard = [
        [
            KeyboardButton(text="🤖 Змінити модель AI"),
            KeyboardButton(text="ℹ️ Інфо про кеш"),
        ],
        [KeyboardButton(text="⬅️ Назад до головного меню")],
    ]
    if is_owner:
        # Вставляємо кнопку "Редагувати адмінів" на другу позицію для власника
        keyboard.insert(1, [KeyboardButton(text="👥 Редагувати адмінів")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_management_keyboard() -> ReplyKeyboardMarkup:
    """Повертає клавіатуру для керування адмінами."""
    keyboard = [
        [
            KeyboardButton(text="➕ Додати адміна"),
            KeyboardButton(text="➖ Видалити адміна"),
        ],
        [KeyboardButton(text="📋 Список адмінів")],
        [KeyboardButton(text="⬅️ Назад до адмін-панелі")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

