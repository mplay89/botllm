[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=mplay89_botllm&metric=alert_status&token=b5aefd416f7ac1d4c24d4b9c451812257cc5660b)](https://sonarcloud.io/summary/new_code?id=mplay89_botllm)
START
 
perevirka


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

### Пояснення параметрів:

- **OLLAMA_NUM_PARALLEL** - кількість одночасних запитів (1-4)
- **OLLAMA_MAX_LOADED_MODELS** - максимум моделей в RAM
- **OLLAMA_CPU_LIMIT** - ліміт CPU cores
- **OLLAMA_MEMORY_LIMIT** - максимум RAM для Ollama