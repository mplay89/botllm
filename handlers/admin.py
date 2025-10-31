import time
from aiogram import F, Router
from aiogram.filters import Command, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from config.settings import settings
from data.admin_store import add_admin, is_admin, list_admins, remove_admin
from data.config_store import get_text_model_name, set_text_model
from data.model_store import get_available_models
from keyboards.inline import get_model_selection_keyboard
from keyboards.reply import get_admin_management_keyboard, get_admin_menu
from utils.logging_setup import get_logger

# Імпортуємо кеші для моніторингу
from data import cache

router = Router()
logger = get_logger(__name__)


class AdminFilter(Filter):
    """Фільтр для перевірки, чи є користувач адміном."""

    async def __call__(self, message: Message) -> bool:
        """Перевіряє права доступу користувача."""
        return await is_admin(message.from_user.id)


class OwnerFilter(Filter):
    """Фільтр для перевірки, чи є користувач власником."""

    async def __call__(self, message: Message) -> bool:
        """Перевіряє, чи є користувач власником бота."""
        return message.from_user.id == settings.OWNER_ID


class AdminActions(StatesGroup):
    """Стани для FSM адмін-панелі."""

    waiting_for_admin_to_add = State()
    waiting_for_admin_to_remove = State()


# --- ІНФОРМАЦІЯ ПРО СИСТЕМУ (для власника) ---

@router.message(OwnerFilter(), Command("cache_info"))
async def cache_info_handler(message: Message) -> None:
    """Показує поточний стан кешу."""
    logger.info("Власник (ID: %d) запросив інформацію про кеш.", message.from_user.id)

    now = time.time()
    info_parts = ["<b>ℹ️ Поточний стан кешу:</b>"]

    # 1. Кеш налаштувань
    info_parts.append("\n<b>Кеш налаштувань (settings_cache):</b>")
    if cache.settings_cache:
        for key, data in cache.settings_cache.items():
            ttl = round(data['timestamp'] + cache.SETTINGS_CACHE_TTL - now)
            info_parts.append(f"- <code>{key}</code>: {data['value']} (залишилось {ttl} сек)")
    else:
        info_parts.append("- <em>Порожньо</em>")

    # 2. Кеш моделей
    info_parts.append("\n<b>Кеш моделей (models_cache):</b>")
    if cache.models_cache:
        ttl = round(cache.models_cache['timestamp'] + cache.MODELS_CACHE_TTL - now)
        models = cache.models_cache['models']
        info_parts.append(f"- <code>models</code>: {models} (залишилось {ttl} сек)")
    else:
        info_parts.append("- <em>Порожньо</em>")

    # 3. Кеш користувачів
    info_parts.append("\n<b>Кеш користувачів (user_cache):</b>")
    if cache.user_cache:
        for user_id, user_data in cache.user_cache.items():
            info_parts.append(f"\n- <b>Користувач <code>{user_id}</code>:</b>")
            for key, data in user_data.items():
                ttl = round(data['timestamp'] + cache.USER_CACHE_TTL - now)
                info_parts.append(f"  - <code>{key}</code>: {data['value']} (залишилось {ttl} сек)")
    else:
        info_parts.append("- <em>Порожньо</em>")

    await message.answer("\n".join(info_parts))


# --- НАВІГАЦІЯ АДМІН-ПАНЕЛІ ---


@router.message(AdminFilter(), F.text == "👑 Адмін-панель")
async def admin_panel_handler(message: Message) -> None:
    """Обробляє кнопку 'Адмін-панель'."""
    logger.info("Адмін (ID: %d) увійшов в адмін-панель.", message.from_user.id)
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer("Ви в адмін-панелі.", reply_markup=get_admin_menu(is_owner))


@router.message(AdminFilter(), F.text == "⬅️ Назад до адмін-панелі")
async def back_to_admin_panel_handler(message: Message, state: FSMContext) -> None:
    """Повертає до головного меню адмін-панелі."""
    logger.info(
        "Адмін (ID: %d) повернувся до головного меню адмін-панелі.",
        message.from_user.id,
    )
    await state.clear()  # Очищуємо стан FSM
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer("Ви в адмін-панелі.", reply_markup=get_admin_menu(is_owner))


# --- КЕРУВАННЯ МОДЕЛЛЮ AI ---


@router.message(AdminFilter(), F.text == "🤖 Змінити модель AI")
async def change_model_handler(message: Message) -> None:
    """Показує інлайн-клавіатуру для вибору моделі AI."""
    logger.info("Адмін (ID: %d) ініціював зміну моделі AI.", message.from_user.id)

    current_model = await get_text_model_name()
    available_models = await get_available_models()

    if not available_models:
        await message.answer(
            "Список доступних моделей порожній. Спробуйте оновити його пізніше."
        )
        return

    current_model_short = current_model.replace("models/", "")

    await message.answer(
        f"Поточна модель: <b>{current_model_short}</b>\n\nОберіть нову модель:",
        reply_markup=get_model_selection_keyboard(available_models, current_model),
    )


@router.callback_query(F.data.startswith("set_model:"))
async def set_model_callback_handler(callback: CallbackQuery) -> None:
    """Обробляє вибір нової моделі з інлайн-клавіатури."""
    model_name = callback.data.split(":")[1]

    if await set_text_model(model_name):
        logger.info(
            "Адмін (ID: %d) змінив модель AI на %s.",
            callback.from_user.id,
            model_name,
        )

        available_models = await get_available_models()
        current_model_short = model_name.replace("models/", "")

        await callback.message.edit_text(
            f"✅ Модель змінено на <b>{current_model_short}</b>\n\nОберіть нову модель:",
            reply_markup=get_model_selection_keyboard(
                available_models, model_name
            ),
        )
        await callback.answer("Збережено!")
    else:
        await callback.answer("Не вдалося змінити модель.", show_alert=True)


# --- КЕРУВАННЯ АДМІНАМИ (для власника) ---


@router.message(OwnerFilter(), F.text == "👥 Редагувати адмінів")
async def manage_admins_handler(message: Message) -> None:
    """Показує меню керування адмінами."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(
        "Власник (ID: %d) увійшов в меню керування адмінами.", message.from_user.id
    )
    await message.answer(
        "Меню керування адміністраторами:",
        reply_markup=get_admin_management_keyboard(),
    )


@router.message(OwnerFilter(), F.text == "➕ Додати адміна")
async def add_admin_start_handler(message: Message, state: FSMContext) -> None:
    """Запускає процес додавання нового адміна."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(
        "Власник (ID: %d) ініціював додавання адміна.", message.from_user.id
    )
    await state.set_state(AdminActions.waiting_for_admin_to_add)
    await message.answer(
        "Надішліть ID користувача або перешліть від нього повідомлення.\n"
        "Для скасування введіть /cancel."
    )


@router.message(OwnerFilter(), F.text == "➖ Видалити адміна")
async def remove_admin_start_handler(message: Message, state: FSMContext) -> None:
    """Запускає процес видалення адміна."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info(
        "Власник (ID: %d) ініціював видалення адміна.", message.from_user.id
    )
    await state.set_state(AdminActions.waiting_for_admin_to_remove)
    await message.answer(
        "Надішліть ID користувача, якого потрібно видалити.\n"
        "Для скасування введіть /cancel."
    )


@router.message(OwnerFilter(), F.text == "📋 Список адмінів")
async def list_admins_handler(message: Message) -> None:
    """Показує список ID всіх адмінів."""
    if message.from_user.id != settings.OWNER_ID:
        return
    logger.info("Власник (ID: %d) запросив список адмінів.", message.from_user.id)
    admins = await list_admins()
    if not admins:
        await message.answer("Список адмінів порожній.")
        return

    admin_list_str = "\n".join(
        [f"• <code>{admin['user_id']}</code> ({admin['role']})" for admin in admins]
    )
    await message.answer(f"<b>Список адміністраторів:</b>\n{admin_list_str}")


# --- ОБРОБНИКИ СТАНІВ FSM ---


@router.message(Command("cancel"))
async def cancel_fsm_handler(message: Message, state: FSMContext) -> None:
    """Обробляє команду /cancel для виходу зі стану FSM."""
    current_state = await state.get_state()
    if current_state is None:
        return

    logger.info(
        "Адмін (ID: %d) скасував поточну дію (стан: %s).",
        message.from_user.id,
        current_state,
    )
    await state.clear()
    is_owner = message.from_user.id == settings.OWNER_ID
    await message.answer("Дію скасовано.", reply_markup=get_admin_menu(is_owner))


@router.message(AdminActions.waiting_for_admin_to_add)
async def process_add_admin_handler(message: Message, state: FSMContext) -> None:
    """Обробляє ID або переслане повідомлення для додавання адміна."""
    user_id_to_add = None
    owner_id = message.from_user.id

    if message.forward_from:
        user_id_to_add = message.forward_from.id
    elif message.text and message.text.isdigit():
        user_id_to_add = int(message.text)
    else:
        logger.warning(
            "Власник (ID: %d) надав невірний формат для додавання адміна.", owner_id
        )
        await message.answer(
            "Невірний формат. Надішліть ID або перешліть повідомлення."
        )
        return

    if await add_admin(user_id_to_add):
        logger.info(
            "Власник (ID: %d) додав нового адміна (ID: %d).",
            owner_id,
            user_id_to_add,
        )
        await message.answer(
            f"✅ Користувачу з ID <code>{user_id_to_add}</code> надано права адміна."
        )
    else:
        logger.info(
            "Власник (ID: %d) спробував додати існуючого адміна (ID: %d).",
            owner_id,
            user_id_to_add,
        )
        await message.answer(
            f"ℹ️ Користувач з ID <code>{user_id_to_add}</code> вже є адміном або є власником."
        )

    await state.clear()


@router.message(AdminActions.waiting_for_admin_to_remove)
async def process_remove_admin_handler(message: Message, state: FSMContext) -> None:
    """Обробляє ID для видалення адміна."""
    owner_id = message.from_user.id
    if not message.text or not message.text.isdigit():
        logger.warning(
            "Власник (ID: %d) надав невірний формат для видалення адміна.", owner_id
        )
        await message.answer("Невірний формат. Надішліть ID користувача.")
        return

    user_id_to_remove = int(message.text)

    if await remove_admin(user_id_to_remove):
        logger.info(
            "Власник (ID: %d) видалив адміна (ID: %d).",
            owner_id,
            user_id_to_remove,
        )
        await message.answer(
            f"✅ У користувача з ID <code>{user_id_to_remove}</code> забрано права адміна."
        )
    else:
        logger.warning(
            "Власник (ID: %d) спробував видалити неіснуючого адміна (ID: %d).",
            owner_id,
            user_id_to_remove,
        )
        await message.answer(
            f"ℹ️ Користувача з ID <code>{user_id_to_remove}</code> не знайдено серед адмінів або це власник."
        )

    await state.clear()