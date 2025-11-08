"""
Pytest configuration and shared fixtures for tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_connection():
    """Mock database connection for testing."""
    mock_conn = AsyncMock()

    # Mock common database operations
    mock_conn.execute = AsyncMock()
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetchval = AsyncMock(return_value=None)
    mock_conn.transaction = MagicMock()

    return mock_conn


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('bot.config.settings.settings') as mock:
        mock.TG_TOKEN = "test_token"
        mock.GEMINI_API_KEY = "test_api_key"
        mock.OWNER_ID = 123456789
        mock.DATABASE_URL = "postgresql://test:test@localhost/test"
        yield mock


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client for testing."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Test response from Gemini"

    mock_client.models.generate_content = MagicMock(return_value=mock_response)
    mock_client.aio.models.list = AsyncMock(return_value=iter([]))

    return mock_client
