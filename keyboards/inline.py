from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_model_selection_keyboard(models: list[str], current_model: str) -> InlineKeyboardMarkup:
    """
    Створює динамічну інлайн-клавіатуру для вибору моделі AI.
    
    Args:
        models: Список доступних імен моделей.
        current_model: Поточна активна модель.
    """
    builder = InlineKeyboardBuilder()
    for model_name in models:
        text = model_name.replace("models/", "") # Робимо назву коротшою
        if model_name == current_model:
            text = f"✅ {text}"
        
        builder.button(text=text, callback_data=f"set_model:{model_name}")
    
    # Розміщуємо по 1 кнопці в ряд для кращої читабельності
    builder.adjust(1)
    return builder.as_markup()
