from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter

from config.settings import settings
from data.admin_store import is_admin, add_admin, remove_admin, list_admins
from data.config_store import get_text_model_name, set_text_model
from data.model_store import get_available_models
from keyboards.reply import get_admin_menu, get_admin_management_keyboard
from keyboards.inline import get_model_selection_keyboard
from utils.logging_setup import get_logger

# Створюємо роутер для адмін-команд
router = Router()
logger = get_logger(__name__)

# Фільтр для перевірки, чи є користувач адміном
class AdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return await is_admin(message.from_user.id)

# Визначаємо стани для FSM
class AdminActions(StatesGroup):
    waiting_for_admin_to_add = State()
    waiting_for_admin_to_remove = State()

# --- НАВІГАЦІЯ АДМІН-ПАНЕЛІ ---

@router.message(AdminFilter(), F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message):
    """Обробник кнопки 'Адмін-панель'."""
    logger.info(f"Адмін (ID: {message.from_user.id}) увійшов в адмін-панель.")
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer("Ви в адмін-панелі.", reply_markup=get_admin_menu(is_owner))

@router.message(AdminFilter(), F.text == "⬅️ Назад до адмін-панелі")
async def back_to_admin_panel_handler(message: Message, state: FSMContext):
    """Обробник для повернення до головного меню адмін-панелі."""
    logger.info(f"Адмін (ID: {message.from_user.id}) повернувся до головного меню адмін-панелі.")
    await state.clear() # Очищуємо стан FSM
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer("Ви в адмін-панелі.", reply_markup=get_admin_menu(is_owner))

# --- КЕРУВАННЯ МОДЕЛЛЮ AI ---

@router.message(AdminFilter(), F.text == "🤖 Змінити модель AI")
async def change_model_handler(message: Message):
    """
    Показує інлайн-клавіатуру для вибору моделі AI.
    """
    logger.info(f"Адмін (ID: {message.from_user.id}) ініціював зміну моделі AI.")
    
    current_model = await get_text_model_name()
    available_models = await get_available_models()
    
    if not available_models:
        await message.answer("Список доступних моделей порожній. Спробуйте оновити його пізніше.")
        return

    current_model_short = current_model.replace("models/", "")

    await message.answer(
        f"Поточна модель: <b>{current_model_short}</b>\n\nОберіть нову модель:",
        reply_markup=get_model_selection_keyboard(available_models, current_model)
    )

@router.callback_query(F.data.startswith("set_model:"))
async def set_model_callback_handler(callback: CallbackQuery):
    """
    Обробляє вибір нової моделі з інлайн-клавіатури.
    """
    model_name = callback.data.split(":")[1]
    
    if await set_text_model(model_name):
        logger.info(f"Адмін (ID: {callback.from_user.id}) змінив модель AI на {model_name}.")
        
        available_models = await get_available_models()
        current_model_short = model_name.replace("models/", "")
        
        await callback.message.edit_text(
            f"✅ Модель змінено на <b>{current_model_short}</b>\n\nОберіть нову модель:",
            reply_markup=get_model_selection_keyboard(available_models, model_name)
        )
        await callback.answer("Збережено!")
    else:
        await callback.answer("Не вдалося змінити модель.", show_alert=True)


# --- КЕРУВАННЯ АДМІНАМИ (для власника) ---

@router.message(AdminFilter(), F.text == "👥 Редагувати адмінів")
async def manage_admins_handler(message: Message):
    """Показує меню керування адмінами."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(f"Власник (ID: {message.from_user.id}) увійшов в меню керування адмінами.")
    await message.answer(
        "Меню керування адміністраторами:",
        reply_markup=get_admin_management_keyboard()
    )

@router.message(AdminFilter(), F.text == "➕ Додати адміна")
async def add_admin_start_handler(message: Message, state: FSMContext):
    """Запускає процес додавання нового адміна."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(f"Власник (ID: {message.from_user.id}) ініціював додавання адміна.")
    await state.set_state(AdminActions.waiting_for_admin_to_add)
    await message.answer(
        "Надішліть ID користувача або перешліть від нього повідомлення.\n"
        "Для скасування введіть /cancel."
    )

@router.message(AdminFilter(), F.text == "➖ Видалити адміна")
async def remove_admin_start_handler(message: Message, state: FSMContext):
    """Запускає процес видалення адміна."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(f"Власник (ID: {message.from_user.id}) ініціював видалення адміна.")
    await state.set_state(AdminActions.waiting_for_admin_to_remove)
    await message.answer(
        "Надішліть ID користувача, якого потрібно видалити.\n"
        "Для скасування введіть /cancel."
    )

@router.message(AdminFilter(), F.text == "📋 Список адмінів")
async def list_admins_handler(message: Message):
    """Показує список ID всіх адмінів."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(f"Власник (ID: {message.from_user.id}) запросив список адмінів.")
    admins = await list_admins()
    if not admins:
        await message.answer("Список адмінів порожній.")
        return
    
    admin_list_str = "\n".join([f"• <code>{admin['user_id']}</code> ({admin['role']})" for admin in admins])
    await message.answer(f"<b>Список адміністраторів:</b>\n{admin_list_str}")

# --- ОБРОБНИКИ СТАНІВ FSM ---

@router.message(Command("cancel"))
async def cancel_fsm_handler(message: Message, state: FSMContext):
    """Обробник команди /cancel для виходу зі стану FSM."""
    current_state = await state.get_state()
    if current_state is None:
        return
    
    logger.info(f"Адмін (ID: {message.from_user.id}) скасував поточну дію (стан: {current_state}).")
    await state.clear()
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer(
        "Дію скасовано.",
        reply_markup=get_admin_menu(is_owner)
    )

@router.message(AdminActions.waiting_for_admin_to_add)
async def process_add_admin_handler(message: Message, state: FSMContext):
    """Обробляє отриманий ID або переслане повідомлення для додавання адміна."""
    user_id_to_add = None
    owner_id = message.from_user.id
    
    if message.forward_from:
        user_id_to_add = message.forward_from.id
    elif message.text and message.text.isdigit():
        user_id_to_add = int(message.text)
    else:
        logger.warning(f"Власник (ID: {owner_id}) надав невірний формат для додавання адміна.")
        await message.answer("Невірний формат. Надішліть ID або перешліть повідомлення.")
        return

    if await add_admin(user_id_to_add):
        logger.info(f"Власник (ID: {owner_id}) додав нового адміна (ID: {user_id_to_add}).")
        await message.answer(f"✅ Користувачу з ID <code>{user_id_to_add}</code> надано права адміна.")
    else:
        logger.info(f"Власник (ID: {owner_id}) спробував додати існуючого адміна (ID: {user_id_to_add}).")
        await message.answer(f"ℹ️ Користувач з ID <code>{user_id_to_add}</code> вже є адміном або є власником.")
    
    await state.clear()

@router.message(AdminActions.waiting_for_admin_to_remove)
async def process_remove_admin_handler(message: Message, state: FSMContext):
    """Обробляє ID для видалення адміна."""
    owner_id = message.from_user.id
    if not message.text or not message.text.isdigit():
        logger.warning(f"Власник (ID: {owner_id}) надав невірний формат для видалення адміна.")
        await message.answer("Невірний формат. Надішліть ID користувача.")
        return
        
    user_id_to_remove = int(message.text)
    
    if await remove_admin(user_id_to_remove):
        logger.info(f"Власник (ID: {owner_id}) видалив адміна (ID: {user_id_to_remove}).")
        await message.answer(f"✅ У користувача з ID <code>{user_id_to_remove}</code> забрано права адміна.")
    else:
        logger.warning(f"Власник (ID: {owner_id}) спробував видалити неіснуючого адміна (ID: {user_id_to_remove}).")
        await message.answer(f"ℹ️ Користувача з ID <code>{user_id_to_remove}</code> не знайдено серед адмінів або це власник.")
        
    await state.clear()
