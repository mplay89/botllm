from typing import List, Dict
from data.user_settings import get_user_role, update_user_role
from data.database import get_db_connection
from config.settings import settings

async def is_admin(user_id: int) -> bool:
    """Перевіряє, чи є користувач адміном або власником, на основі ролі в БД.
    """
    role = await get_user_role(user_id)
    return role in ['admin', 'owner']

async def add_admin(user_id: int) -> bool:
    """Надає користувачу права адміна."""
    # Власник не може бути розжалуваний або підвищений
    if user_id == settings.OWNER_ID:
        return False

    current_role = await get_user_role(user_id)
    if current_role != 'admin':
        await update_user_role(user_id, 'admin')
        return True
    return False # Вже був адміном

async def remove_admin(user_id: int) -> bool:
    """Забирає у користувача права адміна."""
    # Власник не може бути розжалуваний
    if user_id == settings.OWNER_ID:
        return False

    current_role = await get_user_role(user_id)
    if current_role == 'admin':
        await update_user_role(user_id, 'user')
        return True
    return False # Не був адміном

async def list_admins() -> List[Dict[str, int]]:
    """Повертає список всіх адмінів та власника з БД."""
    async with get_db_connection() as conn:
        rows = await conn.fetch("SELECT user_id, role FROM users WHERE role IN ('admin', 'owner')")
        return [dict(row) for row in rows]
