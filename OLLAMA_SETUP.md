# Налаштування Qwen 2.5 7B з Ollama

## Системні вимоги ✅

**Ваша конфігурація підходить ідеально!**

- ✅ RTX 3070 (8GB VRAM)
- ✅ 24GB RAM
- ✅ Windows 10/11

### Що потрібно встановити:

1. **Docker Desktop** з WSL2
2. **NVIDIA Container Toolkit** для GPU підтримки
3. **CUDA драйвери** (версія 11.8+)

---

## ⚡ Найшвидший старт (Lazy Loading)

```bash
# 1. Запустити (старт за ~5 секунд!)
docker-compose up -d

# 2. Модель завантажиться автоматично при ПЕРШОМУ запиті
# Перший раз: ~10 хв (завантаження моделі)
# Всі наступні рази: миттєво ⚡
```

**Як це працює:**
- Ollama сервер стартує **миттєво**
- При першому виклику агента → модель завантажується автоматично
- Volume зберігає модель → наступні запуски миттєві

---

## Повне налаштування 🚀

### 1. Встановлення NVIDIA Container Toolkit

```powershell
# У PowerShell з правами адміністратора
wsl --install
wsl --set-default-version 2
```

В WSL терміналі:
```bash
# Додати NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Встановити nvidia-container-toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 2. Перевірка GPU в Docker

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Повинен показати вашу RTX 3070!

### 3. Запуск Ollama з Qwen 2.5 7B

```bash
# Збірка контейнерів
docker-compose build

# Запуск (автоматично завантажить модель ~4.7GB)
docker-compose up -d

# Перегляд логів завантаження моделі
docker-compose logs -f ollama
```

Перший запуск займе **5-10 хвилин** (завантаження моделі).

### 4. Перевірка роботи

```bash
# Перевірка що Ollama працює
curl http://localhost:11434/api/tags

# Тестовий запит до моделі
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5:7b-instruct-q5_K_M",
  "prompt": "Привіт! Як справи?"
}'
```

---

## Використання в боті 🤖

### Простий приклад:

```python
from bot.services.ollama_service import get_ollama_service

# Отримати сервіс
service = get_ollama_service()

# Генерувати відповідь
response = await service.generate_response(
    prompt="Напиши функцію для сортування списку",
    system_prompt="Ти Python експерт",
    temperature=0.5
)

print(response)
```

### З стрімінгом:

```python
async for chunk in service.generate_response_stream(
    prompt="Розкажи про мульті-агентні системи"
):
    print(chunk, end="", flush=True)
```

### З контекстом розмови:

```python
conversation = [
    {"role": "user", "content": "Привіт!"},
    {"role": "assistant", "content": "Привіт! Чим можу допомогти?"},
    {"role": "user", "content": "Що таке Docker?"}
]

response = await service.generate_with_context(conversation)
```

**Більше прикладів:** `examples/ollama_usage_example.py`

---

## Налаштування ресурсів для різних ПК 💻

### Конфігурація в `.env`:

```env
# Для потужних ПК (RTX 3070+, 16GB+ RAM)
OLLAMA_MODEL=qwen2.5:7b-instruct-q5_K_M
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_CPU_LIMIT=4
OLLAMA_MEMORY_LIMIT=8G

# Для середніх ПК (GTX 1660, 8-16GB RAM)
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_CPU_LIMIT=2
OLLAMA_MEMORY_LIMIT=6G

# Для слабких ПК (без GPU, 8GB RAM)
OLLAMA_MODEL=qwen2.5:3b-instruct-q4_K_M
OLLAMA_NUM_PARALLEL=1
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_CPU_LIMIT=2
OLLAMA_MEMORY_LIMIT=4G
```

### Пояснення параметрів:

- **OLLAMA_NUM_PARALLEL** - кількість одночасних запитів (1-4)
- **OLLAMA_MAX_LOADED_MODELS** - максимум моделей в RAM
- **OLLAMA_CPU_LIMIT** - ліміт CPU cores
- **OLLAMA_MEMORY_LIMIT** - максимум RAM для Ollama

### ⚠️ ВАЖЛИВО: Після зміни конфігурації

```bash
# Зупинити і пересоздати контейнери з новими env змінними
docker-compose down
docker-compose up -d --force-recreate

# АБО коротше (пересоздає автоматично)
docker-compose up -d --force-recreate

# Якщо змінювали Dockerfile (рідко потрібно)
docker-compose up -d --build --force-recreate
```

**Пояснення:**
- `docker-compose up --build` - перебудовує image, але **НЕ** підхоплює нові env змінні
- `--force-recreate` - **ОБОВ'ЯЗКОВО** для застосування змін з `.env`
- Модель НЕ перезавантажується заново (зберігається в volume `ollama_data`)

---

## Продуктивність на RTX 3070 ⚡

| Модель | VRAM | RAM | Швидкість | Якість |
|--------|------|-----|-----------|--------|
| **qwen2.5:7b-instruct-q5_K_M** ⭐ | 5.5 GB | 6 GB | ~40-50 tok/s | Відмінна |
| qwen2.5:7b-instruct-q4_K_M | 4.5 GB | 5 GB | ~50-60 tok/s | Дуже добра |
| qwen2.5:7b-instruct-q8_0 | 7 GB | 8 GB | ~30-40 tok/s | Найкраща |
| qwen2.5:3b-instruct-q4_K_M | 2 GB | 3 GB | ~70-80 tok/s | Добра |

**Рекомендована:** `q5_K_M` - оптимальний баланс!

---

## Конфігурація

### Змінити модель:

Відредагуйте `docker-compose.yml`:

```yaml
command: >
  sh -c "ollama serve &
         sleep 5 &&
         ollama pull qwen2.5:7b-instruct-q4_K_M &&  # Змінити тут
         wait"
```

### Налаштування сервісу:

У `bot/services/ollama_service.py`:

```python
ollama_service = OllamaService(
    host="http://ollama:11434",
    model="qwen2.5:7b-instruct-q5_K_M"  # Змінити модель
)
```

---

## Корисні команди 🛠️

```bash
# Переглянути логи
docker-compose logs -f ollama

# Перезапустити сервіс
docker-compose restart ollama

# Зупинити все
docker-compose down

# Видалити і пересоздать (з видаленням моделі)
docker-compose down -v
docker-compose up -d

# Перевірити використання GPU
docker exec ollama-qwen nvidia-smi

# Список завантажених моделей
docker exec ollama-qwen ollama list

# Інтерактивна консоль
docker exec -it ollama-qwen ollama run qwen2.5:7b-instruct-q5_K_M
```

---

## Оптимізація для мульті-агентів 🎯

### Рекомендована архітектура:

```python
# Координатор (Qwen)
coordinator = OllamaService(model="qwen2.5:7b-instruct-q5_K_M")

# Агенти можуть використовувати той самий сервіс
class CodeAgent:
    def __init__(self):
        self.llm = get_ollama_service()
        self.system_prompt = "Ти експерт з програмування"

class TestAgent:
    def __init__(self):
        self.llm = get_ollama_service()
        self.system_prompt = "Ти експерт з тестування"
```

### Frameworks для мульті-агентів:

1. **AutoGen** (Microsoft)
   ```bash
   pip install pyautogen
   ```

2. **LangGraph** (LangChain)
   ```bash
   pip install langgraph
   ```

3. **CrewAI**
   ```bash
   pip install crewai
   ```

---

## Troubleshooting 🔧

### Помилка "GPU not found"

```bash
# Перевірити CUDA драйвери
nvidia-smi

# Перезапустити Docker
sudo systemctl restart docker
```

### Модель завантажується повільно

Це нормально при першому запуску (~4.7GB). Наступні запуски миттєві.

### Out of Memory

Використайте меншу квантизацію:
- q5_K_M → q4_K_M (економія ~1GB)

### Ollama сервіс не стартує

```bash
# Переглянути детальні логи
docker-compose logs ollama

# Перевірити порт
netstat -an | grep 11434
```

---

## Альтернативні моделі 🔄

Можна легко переключитися на інші моделі:

```bash
# У контейнері
docker exec ollama-qwen ollama pull llama3.1:8b
docker exec ollama-qwen ollama pull mistral:7b
docker exec ollama-qwen ollama pull codellama:7b
```

Потім змінити в коді:
```python
service = OllamaService(model="llama3.1:8b")
```

---

## Моніторинг 📊

### Використання ресурсів:

```bash
# Реальний час
docker stats ollama-qwen

# GPU використання
watch -n 1 nvidia-smi
```

### Benchmarking:

```bash
# Запустити приклади
docker-compose run --rm bot python examples/ollama_usage_example.py
```

---

## Питання? 💬

- [Ollama GitHub](https://github.com/ollama/ollama)
- [Qwen 2.5 Documentation](https://qwenlm.github.io/blog/qwen2.5/)
- [Hugging Face - Qwen2.5](https://huggingface.co/Qwen)

---

**Готово до роботи!** 🎉

Запускай: `docker-compose up -d`
