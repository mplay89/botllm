# Unit Tests

Цей каталог містить unit-тести для Telegram бота.

## Структура

```
tests/
├── conftest.py              # Pytest fixtures та конфігурація
├── data/                    # Тести для data layer
│   ├── test_user_settings.py
│   ├── test_config_store.py
│   └── test_model_store.py
└── services/               # Тести для сервісів
    └── test_gemini.py
```

## Установка залежностей

```bash
pip install -r requirements-dev.txt
```

## Запуск тестів

### Запустити всі тести
```bash
pytest
```

### Запустити тести з verbose output
```bash
pytest -v
```

### Запустити конкретний файл
```bash
pytest tests/data/test_user_settings.py
```

### Запустити конкретний тест
```bash
pytest tests/data/test_user_settings.py::TestUserRegistration::test_register_new_user
```

### Запустити тести з coverage звітом
```bash
pytest --cov=. --cov-report=html
```

### Запустити тільки швидкі тести (пропустити slow)
```bash
pytest -m "not slow"
```

## Coverage звіт

Після запуску тестів з опцією `--cov-report=html`, відкрийте:
```
htmlcov/index.html
```

## Написання нових тестів

1. Створіть файл з префіксом `test_`
2. Назви тест-функцій починайте з `test_`
3. Використовуйте `@pytest.mark.asyncio` для async тестів
4. Використовуйте fixtures з `conftest.py` для мокінгу

### Приклад async тесту:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_example():
    mock_conn = AsyncMock()

    with patch('module.get_db_connection') as mock_get_conn:
        mock_get_conn.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_conn.return_value.__aexit__ = AsyncMock()

        result = await your_function()

        assert result == expected_value
```

## CI/CD Integration

Тести можна інтегрувати в CI/CD pipeline:

### GitHub Actions приклад:
```yaml
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Best Practices

1. **Ізоляція** - кожен тест має бути незалежним
2. **Мокінг** - мокайте зовнішні залежності (БД, API)
3. **Чіткі назви** - назви тестів мають описувати що тестується
4. **AAA паттерн** - Arrange, Act, Assert
5. **Один assert** - один тест перевіряє одну річ (якщо можливо)
