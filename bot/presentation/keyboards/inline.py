"""Модуль для створення інлайн-клавіатур."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_model_selection_keyboard(
    models: list[str], current_model: str
) -> InlineKeyboardMarkup:
    """
    Створює динамічну інлайн-клавіатуру для вибору моделі AI.

    Args:
        models: Список доступних імен моделей.
        current_model: Поточна активна модель.

    Returns:
        Інлайн-клавіатура для вибору моделі.
    """
    builder = InlineKeyboardBuilder()
    for model_name in models:
        text = model_name.replace("models/", "")
        if model_name == current_model:
            text = f"✅ {text}"

        builder.button(text=text, callback_data=f"set_model:{model_name}")

    builder.adjust(1)
    return builder.as_markup()
