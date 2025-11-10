from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Завантажує та валідує налаштування програми зі змінних оточення."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TG_TOKEN: str
    GEMINI_API_KEY: str
    OWNER_ID: int
    DATABASE_URL: str

    # Ollama/Qwen Configuration
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct-q5_K_M"

    # Ollama Resource Limits (для Docker)
    OLLAMA_NUM_PARALLEL: int = 1
    OLLAMA_MAX_LOADED_MODELS: int = 1
    OLLAMA_MAX_QUEUE: int = 512
    OLLAMA_CPU_LIMIT: str = "4"
    OLLAMA_MEMORY_LIMIT: str = "8G"


settings = Settings()
