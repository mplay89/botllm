# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ukrainian language AI Telegram bot using **Gemini API** (text/chat), **Vosk** (ASR), and **EdgeTTS** (TTS). Built with **aiogram 3.x** and **PostgreSQL**, designed for Docker deployment.

**Critical Language Requirement:** All bot responses, system messages, and TTS output MUST be in **Ukrainian**. This is non-negotiable.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run bot locally (requires .env file with TG_TOKEN, GEMINI_API_KEY, OWNER_ID, DATABASE_URL)
python main.py
```

### Docker Development
```bash
# Build and run with docker-compose (recommended for development)
docker-compose up --build

# Run with bind-mount for live code updates (no rebuild needed)
docker-compose up

# Rebuild only when dependencies change
docker-compose build
```

### Database Setup
The bot uses PostgreSQL. Connection string in `.env`:
```
DATABASE_URL=postgresql://user:password@host/db?sslmode=require&channel_binding=require
```

Database tables are auto-created on first run via `data/database.py:init_db()`.

## Architecture Overview

### Core Flow
1. **main.py** - Entry point. Initializes DB, refreshes Gemini models, starts aiogram dispatcher
2. **Routers** - Handler order matters! `admin.router` → `settings_handler.router` → `general.router` (catches all text last)
3. **Database-First** - All user data, context, memory, settings stored in PostgreSQL (no JSON files)
4. **Async Everything** - All I/O operations use `async/await` or `asyncio.to_thread` for blocking calls

### Key Components

**Configuration:**
- `config/settings.py` - Loads `.env` secrets via pydantic-settings
- `config/runtime_config.py` - Non-sensitive, frequently edited params (CONTEXT_MESSAGE_LIMIT, TOKEN_LIMIT_IN/OUT, API_RETRY_ATTEMPTS, etc.)

**Database Layer (`data/`):**
- `database.py` - Connection pool and schema initialization
- `user_settings.py` - User registration, roles, TTS settings, context management
- `config_store.py` - Bot global config (key-value store)
- `model_store.py` - AI model management
- `admin_store.py` - Admin-related queries

**Services:**
- `services/gemini.py` - `GeminiService` class with retry logic, exponential backoff, timeout handling. Uses `client.models.generate_content()` with context from DB.
- Audio services (Vosk, EdgeTTS, FFmpeg) - Placeholders, not fully implemented yet

**Handlers (`handlers/`):**
- `general.py` - `/start`, settings button, text messages → Gemini
- `settings.py` - Settings menu navigation
- `admin.py` - Admin panel (owner/admin only)

**Keyboards (`keyboards/`):**
- `reply.py` - Reply keyboards for main menu, settings
- `inline.py` - Inline keyboards for reminders, admin actions, TTS/memory management

### Database Schema (PostgreSQL)
- `users` - user_id (PK), username, role (owner/admin/user), tts_enabled, tts_voice
- `chat_history` - Conversation context (user_id, role, content, timestamp)
- `long_term_memory` - Persistent memory (user_id, memory_key, memory_value)
- `ai_models` - Available Gemini models (model_name, is_active, priority)
- `bot_config` - Key-value config store
- `reminders` - User reminders (not fully implemented)
- `usage_stats` - API usage tracking (request_type, timestamp)

### Context Management
- Context stored in `chat_history` table
- Trimmed to `CONTEXT_MESSAGE_LIMIT` (config/runtime_config.py) before Gemini API calls
- Format: `[{'role': 'user|model', 'parts': [{'text': '...'}]}]`

### Gemini API Integration
- **Model Selection:** Only `gemini-2.5*` models (excluding preview/audio/image/embedding/vision)
- **Retry Logic:** 3 attempts with exponential backoff (1s, 2s, 4s)
- **Timeout:** 60s per request
- **Error Handling:** Resource exhaustion, service unavailable, model not found → auto-refresh model list

## Critical Patterns

### Logging
- Log **every action, error, operation** with metadata (user_id, request type, success/failure)
- **NEVER log user message content** (privacy)
- Log format: `logger.info(f"User {user_name} (ID: {user_id}) performed action")`

### Keyboard Rules
- **Reply keyboards** - Main menu, settings, general navigation
- **Inline keyboards** - ONLY for: reminders, admin panel sections, TTS settings, memory management confirmations

### Admin Panel Structure
- **Owner-only:** Broadcast messages, full user management
- **Admins:** Statistics, user search, limited moderation
- Role hierarchy: owner > admin > user

### Status Messages (UX Pattern - Not Yet Implemented)
Dynamic two-line status messages that edit in place:
- Line 1: Always "**Очікуйте...**"
- Line 2: Sequential progress updates (3-4 stages)
- Delete status message after final response sent

Examples:
- Text request: "Генерація відповіді." → "Відповідь отримана. Формування повідомлення.."
- Voice input: "Розпізнавання повідомлення." → "Розпізнано. Генерація відповіді." → "Відповідь отримана. Формування повідомлення."

## Known Limitations / TODOs
- Image generation service not implemented
- Vosk ASR not integrated (imports exist but no handlers)
- EdgeTTS not integrated (imports exist but no handlers)
- Reminder system (table exists, no handlers)
- Status message updates not implemented
- Docker healthcheck not added

## Testing
No test suite currently exists. Manual testing via Telegram client.

## Environment Variables
Required in `.env`:
```
TG_TOKEN=<telegram_bot_token>
GEMINI_API_KEY=<google_gemini_api_key>
OWNER_ID=<telegram_user_id>
DATABASE_URL=postgresql://user:password@host/db?sslmode=require&channel_binding=require
```
