import logging
from typing import AsyncGenerator, Optional

import ollama

from bot.config.settings import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Сервіс для роботи з Ollama (Qwen 2.5 7B)."""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        """
        Ініціалізація сервісу Ollama.

        Args:
            host: URL Ollama сервера (за замовчуванням з settings)
            model: Назва моделі для використання (за замовчуванням з settings)
        """
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        self.client = ollama.AsyncClient(host=self.host)
        logger.info(f"Ініціалізовано Ollama клієнт: {self.host}, модель: {self.model}")

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Генерує відповідь від моделі.
        Автоматично завантажує модель при першому виклику (lazy loading).

        Args:
            prompt: Запит користувача
            system_prompt: Системний промпт (опціонально)
            temperature: Температура генерації (0.0-1.0)
            max_tokens: Максимальна кількість токенів

        Returns:
            Згенерована відповідь
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            # Ollama автоматично завантажить модель якщо її немає
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Помилка генерації відповіді Ollama: {e}")
            raise

    async def generate_response_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """
        Генерує відповідь від моделі зі стрімінгом.

        Args:
            prompt: Запит користувача
            system_prompt: Системний промпт (опціонально)
            temperature: Температура генерації (0.0-1.0)
            max_tokens: Максимальна кількість токенів

        Yields:
            Частини згенерованої відповіді
        """
        try:
            messages = []

            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            stream = await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            async for chunk in stream:
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]

        except Exception as e:
            logger.error(f"Помилка стрімінгу Ollama: {e}")
            raise

    async def generate_with_context(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Генерує відповідь з контекстом розмови.

        Args:
            messages: Список повідомлень у форматі [{"role": "user/assistant", "content": "..."}]
            temperature: Температура генерації
            max_tokens: Максимальна кількість токенів

        Returns:
            Згенерована відповідь
        """
        try:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Помилка генерації з контекстом Ollama: {e}")
            raise

    async def check_health(self) -> bool:
        """
        Перевіряє доступність Ollama сервера.

        Returns:
            True якщо сервер доступний, False інакше
        """
        try:
            await self.client.list()
            return True
        except Exception as e:
            logger.error(f"Ollama сервер недоступний: {e}")
            return False


# Глобальний екземпляр сервісу
ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Повертає глобальний екземпляр OllamaService."""
    global ollama_service

    if ollama_service is None:
        ollama_service = OllamaService()

    return ollama_service
