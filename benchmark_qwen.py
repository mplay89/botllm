"""Бенчмарк для діагностики продуктивності Qwen."""

import asyncio
import time
from bot.services.ollama_service import get_ollama_service


async def benchmark():
    """Виміряти реальну швидкість генерації."""
    service = get_ollama_service()

    test_prompt = "Напиши короткий привітальний текст (2-3 речення)."

    print("🔍 Діагностика Qwen 2.5 7B")
    print("=" * 50)

    # Тест 1: Простий запит з вимірюванням часу
    print("\n📊 Тест 1: Простий запит")
    start = time.time()

    response = await service.generate_response(
        prompt=test_prompt,
        temperature=0.7,
        max_tokens=100
    )

    elapsed = time.time() - start
    tokens = len(response.split())  # Приблизно
    tokens_per_sec = tokens / elapsed if elapsed > 0 else 0

    print(f"⏱️  Час: {elapsed:.2f} сек")
    print(f"📝 Відповідь: {response[:100]}...")
    print(f"🚀 Швидкість: ~{tokens_per_sec:.1f} токенів/сек")

    # Тест 2: Повторний запит (без cold start)
    print("\n📊 Тест 2: Повторний запит (warm)")
    start = time.time()

    response = await service.generate_response(
        prompt="Скажи 'Привіт!'",
        temperature=0.7,
        max_tokens=50
    )

    elapsed = time.time() - start
    print(f"⏱️  Час: {elapsed:.2f} сек")

    # Тест 3: Streaming (якщо швидше)
    print("\n📊 Тест 3: Streaming")
    start = time.time()
    chunks = 0

    async for chunk in service.generate_response_stream(
        prompt="Порахуй від 1 до 5",
        temperature=0.7,
        max_tokens=50
    ):
        chunks += 1

    elapsed = time.time() - start
    print(f"⏱️  Час: {elapsed:.2f} сек")
    print(f"📦 Chunks: {chunks}")

    print("\n" + "=" * 50)
    print("✅ Діагностика завершена")


if __name__ == "__main__":
    asyncio.run(benchmark())
