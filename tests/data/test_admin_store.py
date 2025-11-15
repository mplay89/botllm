from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.db.admin_store import (
    add_admin,
    is_admin,
    list_admins,
    remove_admin,
)

OWNER_ID = 12345
ADMIN_ID = 67890
USER_ID = 54321


@pytest.mark.asyncio
@patch("bot.db.admin_store.get_user_role", new_callable=AsyncMock)
async def test_is_admin(mock_get_user_role):
    """Тестує is_admin."""
    mock_get_user_role.return_value = "admin"
    assert await is_admin(ADMIN_ID) is True

    mock_get_user_role.return_value = "owner"
    assert await is_admin(OWNER_ID) is True

    mock_get_user_role.return_value = "user"
    assert await is_admin(USER_ID) is False


@pytest.mark.asyncio
@patch("bot.db.admin_store.update_user_role", new_callable=AsyncMock)
@patch("bot.db.admin_store.get_user_role", new_callable=AsyncMock)
@patch("bot.db.admin_store.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_add_admin(mock_get_user_role, mock_update_user_role):
    """Тестує add_admin."""
    # Add a regular user as admin
    mock_get_user_role.return_value = "user"
    assert await add_admin(USER_ID) is True
    mock_update_user_role.assert_called_once_with(USER_ID, "admin")

    # Try to add an existing admin
    mock_get_user_role.return_value = "admin"
    assert await add_admin(ADMIN_ID) is False

    # Try to add the owner
    assert await add_admin(OWNER_ID) is False


@pytest.mark.asyncio
@patch("bot.db.admin_store.update_user_role", new_callable=AsyncMock)
@patch("bot.db.admin_store.get_user_role", new_callable=AsyncMock)
@patch("bot.db.admin_store.settings", MagicMock(OWNER_ID=OWNER_ID))
async def test_remove_admin(mock_get_user_role, mock_update_user_role):
    """Тестує remove_admin."""
    # Remove an admin
    mock_get_user_role.return_value = "admin"
    assert await remove_admin(ADMIN_ID) is True
    mock_update_user_role.assert_called_once_with(ADMIN_ID, "user")

    # Try to remove a regular user
    mock_get_user_role.return_value = "user"
    assert await remove_admin(USER_ID) is False

    # Try to remove the owner
    assert await remove_admin(OWNER_ID) is False


@pytest.mark.asyncio
@patch("bot.db.admin_store.get_db_connection")
async def test_list_admins(mock_get_db_connection):
    """Тестує list_admins."""
    mock_conn = MagicMock()
    mock_conn.fetch = AsyncMock(return_value=[
        {"user_id": OWNER_ID, "role": "owner"},
        {"user_id": ADMIN_ID, "role": "admin"},
    ])
    mock_get_db_connection.return_value.__aenter__.return_value = mock_conn

    admins = await list_admins()

    assert len(admins) == 2
    assert {"user_id": OWNER_ID, "role": "owner"} in admins
    assert {"user_id": ADMIN_ID, "role": "admin"} in admins
