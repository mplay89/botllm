"""
Unit tests for data.user_settings module.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import User

# Очищення кешу перед кожним тестом
@pytest.fixture(autouse=True)
def reset_cache():
    from data import cache
    cache.user_cache = {}

from data.user_settings import (
    register_user_if_not_exists,
    get_user_role,
    update_user_role,
    get_user_tts_settings,
    update_user_tts_enabled,
    update_user_tts_voice,
    get_user_context,
    add_message_to_context,
    clear_user_context
)


@pytest.mark.asyncio
class TestUserRegistration:
    """Tests for user registration and role management."""

    async def test_register_new_user(self, mock_settings):
        """Test registering a new user."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.id = 987654321
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"
        mock_user.last_name = "User"

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            await register_user_if_not_exists(mock_user)

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "INSERT INTO users" in call_args[0]
            assert call_args[1] == 987654321
            assert call_args[5] == "user"  # role should be 'user'

    async def test_register_owner(self, mock_settings):
        """Test registering owner gets 'owner' role."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.id = 123456789  # Same as mock_settings.OWNER_ID
        mock_user.username = "owner"
        mock_user.full_name = "Owner"
        mock_user.last_name = "User"

        with patch('data.user_settings.settings') as patched_settings:
            patched_settings.OWNER_ID = 123456789

            with patch('data.user_settings.get_db_connection') as mock_get_conn:
                mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

                await register_user_if_not_exists(mock_user)

                call_args = mock_conn.execute.call_args[0]
                assert call_args[5] == "owner"  # role should be 'owner'

    async def test_existing_user_not_reregistered(self, mock_settings):
        """Test that existing users are not re-registered."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={'user_id': 123, 'role': 'user'})
        mock_conn.execute = AsyncMock()

        mock_user = MagicMock(spec=User)
        mock_user.id = 123
        mock_user.username = "existing"

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            await register_user_if_not_exists(mock_user)

            mock_conn.execute.assert_not_called()


@pytest.mark.asyncio
class TestUserRoles:
    """Tests for user role operations."""

    async def test_get_user_role(self):
        """Test retrieving user role."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="admin")

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            role = await get_user_role(123)

            assert role == "admin"
            mock_conn.fetchval.assert_called_once()

    async def test_update_user_role(self):
        """Test updating user role."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            await update_user_role(123, "admin")

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "UPDATE users SET role" in call_args[0]
            assert call_args[1] == "admin"
            assert call_args[2] == 123

    async def test_get_user_role_caching(self):
        """Test that user roles are cached."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value="admin")

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            # First call should hit DB
            role1 = await get_user_role(123)
            assert role1 == "admin"
            mock_conn.fetchval.assert_called_once()

            # Second call should use cache
            role2 = await get_user_role(123)
            assert role2 == "admin"
            mock_conn.fetchval.assert_called_once() # Not called again

            # Cache should be invalidated after update
            await update_user_role(123, "user")
            mock_conn.fetchval.reset_mock()
            mock_conn.fetchval.return_value = "user"

            role3 = await get_user_role(123)
            assert role3 == "user"
            mock_conn.fetchval.assert_called_once()


@pytest.mark.asyncio
class TestTTSSettings:
    """Tests for TTS settings."""

    async def test_get_user_tts_settings(self):
        """Test retrieving TTS settings."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={
            'tts_enabled': True,
            'tts_voice': 'male'
        })

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            settings = await get_user_tts_settings(123)

            assert settings['tts_enabled'] is True
            assert settings['tts_voice'] == 'male'

    async def test_get_user_tts_settings_defaults(self):
        """Test default TTS settings when user not found."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            settings = await get_user_tts_settings(123)

            assert settings['tts_enabled'] is True
            assert settings['tts_voice'] == 'female'

    async def test_get_user_tts_settings_caching(self):
        """Test that TTS settings are cached."""
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={'tts_enabled': False, 'tts_voice': 'test_voice'})

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)

            # First call
            s1 = await get_user_tts_settings(123)
            assert s1['tts_enabled'] is False
            mock_conn.fetchrow.assert_called_once()

            # Second call from cache
            s2 = await get_user_tts_settings(123)
            assert s2['tts_enabled'] is False
            mock_conn.fetchrow.assert_called_once()

            # Invalidate and check again
            await update_user_tts_enabled(123, True)
            mock_conn.fetchrow.reset_mock()
            mock_conn.fetchrow.return_value = {'tts_enabled': True, 'tts_voice': 'test_voice'}

            s3 = await get_user_tts_settings(123)
            assert s3['tts_enabled'] is True
            mock_conn.fetchrow.assert_called_once()


@pytest.mark.asyncio
class TestChatContext:
    """Tests for chat context management."""

    async def test_get_user_context(self):
        """Test retrieving user context."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {'role': 'user', 'content': 'Hello'},
            {'role': 'model', 'content': 'Hi there!'}
        ])

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            context = await get_user_context(123)

            assert len(context) == 2
            assert context[0]['role'] == 'user'
            assert context[0]['parts'][0]['text'] == 'Hello'
            assert context[1]['role'] == 'model'

    async def test_add_message_to_context(self):
        """Test adding message to context."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            await add_message_to_context(123, 'user', 'Test message')

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "INSERT INTO chat_history" in call_args[0]
            assert call_args[1] == 123
            assert call_args[2] == 'user'
            assert call_args[3] == 'Test message'

    async def test_clear_user_context(self):
        """Test clearing user context."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()

        with patch('data.user_settings.get_db_connection') as mock_get_conn:
            mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_get_conn.return_value.__aexit__ = AsyncMock()

            await clear_user_context(123)

            mock_conn.execute.assert_called_once()
            call_args = mock_conn.execute.call_args[0]
            assert "DELETE FROM chat_history" in call_args[0]
            assert call_args[1] == 123

