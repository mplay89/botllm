from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Завантажує та валідує налаштування програми зі змінних оточення."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    TG_TOKEN: str
    GEMINI_API_KEY: str
    OWNER_ID: int
    DATABASE_URL: str


settings = Settings()
