# 🤖 Гайд по створенню AI-агентів для Telegram ботів

Покроковий план розробки мультиагентних систем на базі Ollama + Qwen 2.5 7B

---

## 📋 Зміст

1. [Фаза 1: Базова інфраструктура](#фаза-1-базова-інфраструктура)
2. [Фаза 2: Агентна архітектура](#фаза-2-агентна-архітектура)
3. [Фаза 3: Tools/Інструменти](#фаза-3-toolsінструменти)
4. [Фаза 4: Мультиагентні системи](#фаза-4-мультиагентні-системи)
5. [Фаза 5: Пам'ять і контекст](#фаза-5-память-і-контекст)
6. [Фаза 6: Telegram інтеграція](#фаза-6-telegram-інтеграція)
7. [Фаза 7: Frameworks](#фаза-7-frameworks)
8. [Фаза 8: Моніторинг](#фаза-8-моніторинг-і-оптимізація)
9. [План реалізації](#-рекомендований-порядок-реалізації)

---

## Фаза 1: Базова інфраструктура

### Що вже є ✅

```
bot/
├── services/
│   ├── ollama_service.py    # LLM сервіс (Qwen 2.5 7B)
│   └── gemini.py            # Альтернативний LLM
├── handlers/
│   ├── qwen.py              # Простий запит/відповідь
│   ├── admin.py
│   └── general.py
├── db/
│   ├── database.py          # asyncpg
│   └── user_settings.py
└── config/
    └── settings.py
```

### Архітектура поточного стану

```
User → Telegram → Handler → OllamaService → Qwen 2.5 → Response
                                ↓
                           PostgreSQL
```

**Обмеження:**
- Немає спеціалізації (один промпт для всього)
- Відсутня пам'ять між сесіями
- Немає інструментів (tools)
- Один агент = один запит

---

## Фаза 2: Агентна архітектура

### 2.1. Базовий клас Agent

**Створити:** `bot/agents/base_agent.py`

```python
"""Базові класи для AI-агентів."""

import logging
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from bot.services.ollama_service import OllamaService, get_ollama_service

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Базовий клас для всіх агентів."""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm_service: Optional[OllamaService] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Ініціалізація агента.
        
        Args:
            name: Ім'я агента
            system_prompt: Системний промпт (роль агента)
            llm_service: LLM сервіс (за замовчуванням Ollama)
            temperature: Температура генерації
            max_tokens: Максимальна кількість токенів
        """
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm_service or get_ollama_service()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.memory: List[Dict[str, str]] = []  # Історія розмови
        
        logger.info(f"Ініціалізовано агента: {name}")
    
    async def think(self, user_input: str) -> str:
        """
        Обробка запиту з контекстом пам'яті.
        
        Args:
            user_input: Запит користувача
            
        Returns:
            Відповідь агента
        """
        try:
            # Додати запит до пам'яті
            self.memory.append({"role": "user", "content": user_input})
            
            # Підготувати повідомлення з системним промптом
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.memory)
            
            # Генерація відповіді
            response = await self.llm.generate_with_context(
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Додати відповідь до пам'яті
            self.memory.append({"role": "assistant", "content": response})
            
            # Обмежити розмір пам'яті (останні 10 повідомлень)
            if len(self.memory) > 20:
                self.memory = self.memory[-20:]
            
            logger.info(f"Агент {self.name} відповів")
            return response
            
        except Exception as e:
            logger.error(f"Помилка агента {self.name}: {e}")
            raise
    
    async def think_stream(self, user_input: str):
        """Генерація відповіді зі стрімінгом."""
        self.memory.append({"role": "user", "content": user_input})
        
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory)
        
        full_response = ""
        async for chunk in self.llm.generate_response_stream(
            prompt=user_input,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        ):
            full_response += chunk
            yield chunk
        
        self.memory.append({"role": "assistant", "content": full_response})
    
    def clear_memory(self):
        """Очистити пам'ять агента."""
        self.memory.clear()
        logger.info(f"Пам'ять агента {self.name} очищено")
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Повертає список можливостей агента."""
        pass
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name={self.name})>"
```

### 2.2. Спеціалізовані агенти

**Створити:** `bot/agents/specialized_agents.py`

```python
"""Спеціалізовані агенти для різних задач."""

from typing import List
from bot.agents.base_agent import BaseAgent


class CodeAgent(BaseAgent):
    """Агент для генерації та аналізу коду."""
    
    def __init__(self):
        super().__init__(
            name="CodeExpert",
            system_prompt=(
                "Ти експерт Python програміст з 10+ років досвіду.\n"
                "Генеруй чистий, читабельний код з докстрінгами.\n"
                "Слідуй PEP 8 та best practices.\n"
                "Додавай коментарі де потрібно.\n"
                "Якщо код має помилки - виправ їх та поясни."
            ),
            temperature=0.3  # Нижча температура для точності
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Генерація Python коду",
            "Рефакторинг",
            "Пошук багів",
            "Написання тестів",
            "Code review"
        ]


class TranslatorAgent(BaseAgent):
    """Агент для перекладу текстів."""
    
    def __init__(self):
        super().__init__(
            name="Translator",
            system_prompt=(
                "Ти професійний перекладач UA ↔ EN.\n"
                "Перекладай точно, зберігаючи тон та контекст.\n"
                "Якщо мова не вказана - визнач автоматично.\n"
                "Для технічних термінів надавай оригінал у дужках."
            ),
            temperature=0.5
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Переклад UA → EN",
            "Переклад EN → UA",
            "Автовизначення мови",
            "Технічні переклади"
        ]


class ResearcherAgent(BaseAgent):
    """Агент для пошуку та аналізу інформації."""
    
    def __init__(self):
        super().__init__(
            name="Researcher",
            system_prompt=(
                "Ти дослідник та аналітик.\n"
                "Шукай точну, перевірену інформацію.\n"
                "Структуруй відповіді: факти, джерела, висновки.\n"
                "Якщо не впевнений - скажи про це.\n"
                "Уникай домислів та припущень."
            ),
            temperature=0.4
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Пошук інформації",
            "Аналіз даних",
            "Структурування знань",
            "Fact-checking"
        ]


class WriterAgent(BaseAgent):
    """Агент для написання текстів."""
    
    def __init__(self):
        super().__init__(
            name="Writer",
            system_prompt=(
                "Ти креативний письменник.\n"
                "Пишеш захоплюючі тексти різних стилів.\n"
                "Адаптуєш тон до аудиторії.\n"
                "Структуруєш текст логічно: вступ, основна частина, висновок."
            ),
            temperature=0.8  # Вища температура для креативності
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Написання статей",
            "Копірайтинг",
            "Storytelling",
            "Редагування текстів"
        ]


class TestAgent(BaseAgent):
    """Агент для написання тестів."""
    
    def __init__(self):
        super().__init__(
            name="TestExpert",
            system_prompt=(
                "Ти експерт з тестування ПЗ.\n"
                "Пишеш unit-тести використовуючи pytest.\n"
                "Покриваєш edge cases та помилки.\n"
                "Використовуй fixtures, mocks, parametrize.\n"
                "Тести мають бути чіткими та зрозумілими."
            ),
            temperature=0.2
        )
    
    def get_capabilities(self) -> List[str]:
        return [
            "Unit тести (pytest)",
            "Integration тести",
            "Test coverage аналіз",
            "TDD підхід"
        ]
```

### 2.3. Координатор агентів (Orchestrator)

**Створити:** `bot/agents/orchestrator.py`

```python
"""Координатор для управління кількома агентами."""

import logging
from typing import Dict, Optional
from bot.agents.specialized_agents import (
    CodeAgent,
    TranslatorAgent,
    ResearcherAgent,
    WriterAgent,
    TestAgent
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Координує роботу кількох агентів."""
    
    def __init__(self):
        """Ініціалізація всіх доступних агентів."""
        self.agents: Dict[str, BaseAgent] = {
            "code": CodeAgent(),
            "translate": TranslatorAgent(),
            "research": ResearcherAgent(),
            "writer": WriterAgent(),
            "test": TestAgent()
        }
        
        logger.info(f"Ініціалізовано {len(self.agents)} агентів")
    
    async def classify_task(self, user_input: str) -> str:
        """
        Визначає який агент найкраще підходить для задачі.
        
        Args:
            user_input: Запит користувача
            
        Returns:
            Ключ агента (code/translate/research/writer/test)
        """
        # Простий класифікатор на основі ключових слів
        user_input_lower = user_input.lower()
        
        # Код
        if any(kw in user_input_lower for kw in [
            "код", "code", "функц", "function", "клас", "class",
            "скрипт", "script", "програм", "python", "debug"
        ]):
            return "code"
        
        # Тести
        if any(kw in user_input_lower for kw in [
            "тест", "test", "pytest", "unittest", "mock"
        ]):
            return "test"
        
        # Переклад
        if any(kw in user_input_lower for kw in [
            "переклад", "translate", "англійськ", "english", "ukrainian"
        ]):
            return "translate"
        
        # Дослідження
        if any(kw in user_input_lower for kw in [
            "що таке", "what is", "інформац", "information",
            "пошук", "search", "дослід", "research"
        ]):
            return "research"
        
        # Письмо
        if any(kw in user_input_lower for kw in [
            "напиши стать", "write article", "текст", "text",
            "історі", "story", "копірайт"
        ]):
            return "writer"
        
        # За замовчуванням - дослідник
        return "research"
    
    async def route(self, user_input: str, agent_type: Optional[str] = None) -> str:
        """
        Маршрутизує запит до відповідного агента.
        
        Args:
            user_input: Запит користувача
            agent_type: Тип агента (опціонально, визначається автоматично)
            
        Returns:
            Відповідь агента
        """
        try:
            # Визначити агента якщо не вказано
            if agent_type is None:
                agent_type = await self.classify_task(user_input)
            
            # Отримати агента
            agent = self.agents.get(agent_type)
            if agent is None:
                logger.warning(f"Невідомий тип агента: {agent_type}")
                agent = self.agents["research"]  # Fallback
            
            logger.info(f"Маршрутизація до агента: {agent.name}")
            
            # Виконати запит
            response = await agent.think(user_input)
            return response
            
        except Exception as e:
            logger.error(f"Помилка маршрутизації: {e}")
            raise
    
    async def route_stream(self, user_input: str, agent_type: Optional[str] = None):
        """Маршрутизація зі стрімінгом."""
        if agent_type is None:
            agent_type = await self.classify_task(user_input)
        
        agent = self.agents.get(agent_type, self.agents["research"])
        logger.info(f"Маршрутизація (stream) до агента: {agent.name}")
        
        async for chunk in agent.think_stream(user_input):
            yield chunk
    
    def get_agent(self, agent_type: str):
        """Отримати конкретного агента."""
        return self.agents.get(agent_type)
    
    def list_agents(self) -> Dict[str, list]:
        """Список всіх агентів та їх можливостей."""
        return {
            name: agent.get_capabilities()
            for name, agent in self.agents.items()
        }


# Глобальний екземпляр
_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Повертає глобальний екземпляр orchestrator."""
    global _orchestrator
    
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    
    return _orchestrator
```

---

## Фаза 3: Tools/Інструменти

### 3.1. Базовий клас Tool

**Створити:** `bot/agents/tools/base_tool.py`

```python
"""Базові класи для інструментів агентів."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Базовий клас для інструментів."""
    
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Виконує інструмент.
        
        Args:
            **kwargs: Параметри інструменту
            
        Returns:
            Результат виконання
        """
        pass
    
    def to_function_schema(self) -> Dict[str, Any]:
        """
        Конвертує інструмент у формат function calling.
        
        Returns:
            Schema для LLM
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }
    
    def __repr__(self):
        return f"<Tool(name={self.name})>"
```

### 3.2. Конкретні інструменти

**Створити:** `bot/agents/tools/web_tools.py`

```python
"""Інструменти для роботи з веб."""

from typing import List, Dict, Any
import aiohttp
import logging

from bot.agents.tools.base_tool import Tool

logger = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """Пошук інформації в інтернеті."""
    
    name = "web_search"
    description = "Шукає інформацію в інтернеті за запитом"
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Пошуковий запит"
            },
            "max_results": {
                "type": "integer",
                "description": "Максимальна кількість результатів",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    async def execute(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Шукає в інтернеті через DuckDuckGo API.
        
        Args:
            query: Пошуковий запит
            max_results: Кількість результатів
            
        Returns:
            Список результатів з title, snippet, url
        """
        try:
            # DuckDuckGo Instant Answer API (безкоштовний)
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    data = await response.json()
            
            results = []
            
            # AbstractText
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data["AbstractText"],
                    "url": data.get("AbstractURL", "")
                })
            
            # Related Topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if "Text" in topic:
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", "")
                    })
            
            logger.info(f"Web search: {query}, знайдено {len(results)} результатів")
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Помилка web search: {e}")
            return []


class FetchUrlTool(Tool):
    """Завантажує контент з URL."""
    
    name = "fetch_url"
    description = "Завантажує текстовий контент з веб-сторінки"
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "URL сторінки"
            }
        },
        "required": ["url"]
    }
    
    async def execute(self, url: str) -> str:
        """Завантажує HTML з URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    content = await response.text()
            
            logger.info(f"Завантажено URL: {url}")
            return content[:5000]  # Перші 5000 символів
            
        except Exception as e:
            logger.error(f"Помилка fetch_url: {e}")
            return f"Помилка завантаження: {e}"
```

**Створити:** `bot/agents/tools/code_tools.py`

```python
"""Інструменти для роботи з кодом."""

import subprocess
import asyncio
import tempfile
import os
from typing import Dict, Any

from bot.agents.tools.base_tool import Tool
import logging

logger = logging.getLogger(__name__)


class CodeExecutorTool(Tool):
    """Виконує Python код у безпечному середовищі."""
    
    name = "execute_python"
    description = "Виконує Python код та повертає результат"
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python код для виконання"
            },
            "timeout": {
                "type": "integer",
                "description": "Таймаут у секундах",
                "default": 5
            }
        },
        "required": ["code"]
    }
    
    async def execute(self, code: str, timeout: int = 5) -> Dict[str, Any]:
        """
        Виконує Python код у subprocess.
        
        Args:
            code: Python код
            timeout: Максимальний час виконання
            
        Returns:
            Dict з output, error, exit_code
        """
        try:
            # Створити тимчасовий файл
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Виконати код
                process = await asyncio.create_subprocess_exec(
                    'python3', temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                result = {
                    "output": stdout.decode('utf-8'),
                    "error": stderr.decode('utf-8'),
                    "exit_code": process.returncode,
                    "success": process.returncode == 0
                }
                
                logger.info(f"Виконано код, exit_code={result['exit_code']}")
                return result
                
            finally:
                # Видалити тимчасовий файл
                os.unlink(temp_file)
                
        except asyncio.TimeoutError:
            logger.warning(f"Таймаут виконання коду ({timeout}s)")
            return {
                "output": "",
                "error": f"Timeout: виконання перевищило {timeout} секунд",
                "exit_code": -1,
                "success": False
            }
        except Exception as e:
            logger.error(f"Помилка виконання коду: {e}")
            return {
                "output": "",
                "error": str(e),
                "exit_code": -1,
                "success": False
            }


class CodeValidatorTool(Tool):
    """Перевіряє Python код на синтаксичні помилки."""
    
    name = "validate_python"
    description = "Перевіряє синтаксис Python коду"
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python код для перевірки"
            }
        },
        "required": ["code"]
    }
    
    async def execute(self, code: str) -> Dict[str, Any]:
        """Перевіряє синтаксис через compile()."""
        try:
            compile(code, '<string>', 'exec')
            return {
                "valid": True,
                "error": None
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax Error на рядку {e.lineno}: {e.msg}"
            }
```

### 3.3. Tool Manager

**Створити:** `bot/agents/tools/tool_manager.py`

```python
"""Менеджер інструментів для агентів."""

from typing import Dict, List, Any, Optional
import logging

from bot.agents.tools.base_tool import Tool
from bot.agents.tools.web_tools import WebSearchTool, FetchUrlTool
from bot.agents.tools.code_tools import CodeExecutorTool, CodeValidatorTool

logger = logging.getLogger(__name__)


class ToolManager:
    """Управляє доступними інструментами."""
    
    def __init__(self):
        """Ініціалізація всіх інструментів."""
        self.tools: Dict[str, Tool] = {
            "web_search": WebSearchTool(),
            "fetch_url": FetchUrlTool(),
            "execute_python": CodeExecutorTool(),
            "validate_python": CodeValidatorTool()
        }
        
        logger.info(f"Ініціалізовано {len(self.tools)} інструментів")
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Отримати інструмент за назвою."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Список всіх інструментів у форматі function schema."""
        return [tool.to_function_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """
        Виконати інструмент.
        
        Args:
            name: Назва інструменту
            **kwargs: Параметри
            
        Returns:
            Результат виконання
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Інструмент '{name}' не знайдено")
        
        logger.info(f"Виконання інструменту: {name}")
        return await tool.execute(**kwargs)


# Глобальний екземпляр
_tool_manager: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """Повертає глобальний екземпляр ToolManager."""
    global _tool_manager
    
    if _tool_manager is None:
        _tool_manager = ToolManager()
    
    return _tool_manager
```

---

## Фаза 4: Мультиагентні системи

### 4.1. Колаборативна робота агентів

**Створити:** `bot/agents/multi_agent_system.py`

```python
"""Система для співпраці кількох агентів."""

import logging
from typing import List, Dict, Any

from bot.agents.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """Координує співпрацю кількох агентів для складних задач."""
    
    def __init__(self):
        self.orchestrator = get_orchestrator()
    
    async def plan_and_execute(self, task: str) -> str:
        """
        Планує та виконує складну задачу через кілька агентів.
        
        Паттерн: Planner → Executor → Critic → (Refine) → Result
        
        Args:
            task: Опис задачі
            
        Returns:
            Фінальний результат
        """
        logger.info(f"MultiAgent: розв'язання задачі...")
        
        # 1. PLANNER: Розбити задачу на кроки
        planner_prompt = (
            f"Розбий цю задачу на послідовні кроки:\n{task}\n\n"
            "Відповідь у форматі:\n"
            "1. [тип агента] - опис кроку\n"
            "2. [тип агента] - опис кроку\n"
            "..."
        )
        
        plan = await self.orchestrator.route(planner_prompt, "research")
        logger.info(f"План створено:\n{plan}")
        
        # 2. EXECUTOR: Виконати кроки (спрощена версія)
        execution_prompt = f"Виконай цю задачу:\n{task}"
        result = await self.orchestrator.route(execution_prompt)
        
        # 3. CRITIC: Перевірити результат
        critic_prompt = (
            f"Перевір цей результат на якість:\n\n"
            f"Задача: {task}\n\n"
            f"Результат:\n{result}\n\n"
            "Оцінка (добре/потребує покращень/погано) та коментарі:"
        )
        
        review = await self.orchestrator.route(critic_prompt, "research")
        logger.info(f"Оцінка: {review[:200]}")
        
        # 4. Якщо потрібно - рефайн (спрощено, просто повертаємо результат)
        return f"**Результат:**\n{result}\n\n**Оцінка:**\n{review}"
    
    async def debate(self, topic: str, agents: List[str]) -> Dict[str, str]:
        """
        Дебати між агентами на тему.
        
        Args:
            topic: Тема дебатів
            agents: Список типів агентів для участі
            
        Returns:
            Dict з аргументами кожного агента
        """
        results = {}
        
        for agent_type in agents:
            agent = self.orchestrator.get_agent(agent_type)
            if agent:
                prompt = f"Твоя думка щодо: {topic}"
                response = await agent.think(prompt)
                results[agent.name] = response
        
        return results


# Глобальний екземпляр
_multi_agent_system: MultiAgentSystem = None


def get_multi_agent_system() -> MultiAgentSystem:
    """Повертає глобальний екземпляр MultiAgentSystem."""
    global _multi_agent_system
    
    if _multi_agent_system is None:
        _multi_agent_system = MultiAgentSystem()
    
    return _multi_agent_system
```

---

## Фаза 5: Пам'ять і контекст

### 5.1. Short-term Memory

**Створити:** `bot/agents/memory/short_term.py`

```python
"""Short-term пам'ять для агентів."""

from collections import deque
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Зберігає історію поточної розмови."""
    
    def __init__(self, max_messages: int = 20):
        """
        Args:
            max_messages: Максимальна кількість повідомлень
        """
        self.messages = deque(maxlen=max_messages)
        self.max_messages = max_messages
    
    def add(self, role: str, content: str):
        """Додати повідомлення."""
        self.messages.append({
            "role": role,
            "content": content
        })
        logger.debug(f"Додано повідомлення ({role}): {content[:50]}...")
    
    def get_context(self, last_n: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Отримати контекст розмови.
        
        Args:
            last_n: Останні N повідомлень (None = всі)
            
        Returns:
            Список повідомлень
        """
        if last_n is None:
            return list(self.messages)
        return list(self.messages)[-last_n:]
    
    def clear(self):
        """Очистити пам'ять."""
        self.messages.clear()
        logger.info("Пам'ять очищено")
    
    def __len__(self):
        return len(self.messages)
```

### 5.2. Long-term Memory (БД)

**Створити SQL міграція:** `bot/db/migrations/add_agent_memory.sql`

```sql
-- Таблиця для довготривалої пам'яті агентів
CREATE TABLE IF NOT EXISTS agent_memories (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    agent_name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- Для векторного пошуку (потребує pgvector)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_agent (user_id, agent_name),
    INDEX idx_created_at (created_at)
);

-- Індекс для векторного пошуку (якщо є pgvector)
-- CREATE INDEX ON agent_memories USING ivfflat (embedding vector_cosine_ops);
```

**Створити:** `bot/agents/memory/long_term.py`

```python
"""Long-term пам'ять з БД."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from bot.db.database import get_db_pool

logger = logging.getLogger(__name__)


class LongTermMemory:
    """Зберігає пам'ять агентів у БД."""
    
    async def store(
        self,
        user_id: int,
        agent_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Зберегти спогад у БД.
        
        Args:
            user_id: ID користувача
            agent_name: Ім'я агента
            content: Контент спогаду
            metadata: Додаткові дані
        """
        pool = get_db_pool()
        
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO agent_memories (user_id, agent_name, content, metadata)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, agent_name, content, metadata or {}
            )
        
        logger.info(f"Збережено спогад: {agent_name} для user {user_id}")
    
    async def get_recent(
        self,
        user_id: int,
        agent_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Отримати останні спогади.
        
        Args:
            user_id: ID користувача
            agent_name: Ім'я агента (опціонально)
            limit: Кількість спогадів
            
        Returns:
            Список спогадів
        """
        pool = get_db_pool()
        
        async with pool.acquire() as conn:
            if agent_name:
                rows = await conn.fetch(
                    """
                    SELECT * FROM agent_memories
                    WHERE user_id = $1 AND agent_name = $2
                    ORDER BY created_at DESC
                    LIMIT $3
                    """,
                    user_id, agent_name, limit
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT * FROM agent_memories
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    user_id, limit
                )
        
        return [dict(row) for row in rows]
    
    async def search(
        self,
        user_id: int,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Пошук спогадів (простий текстовий пошук).
        
        Для векторного пошуку потрібно додати pgvector та embeddings.
        """
        pool = get_db_pool()
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM agent_memories
                WHERE user_id = $1 AND content ILIKE $2
                ORDER BY created_at DESC
                LIMIT $3
                """,
                user_id, f"%{query}%", limit
            )
        
        return [dict(row) for row in rows]
```

---

## Фаза 6: Telegram інтеграція

### 6.1. Handler з агентами

**Створити:** `bot/handlers/agent_handler.py`

```python
"""Handler для роботи з AI агентами."""

import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.agents.orchestrator import get_orchestrator
from bot.agents.multi_agent_system import get_multi_agent_system
from bot.db.user_settings import register_user_if_not_exists

router = Router()
logger = logging.getLogger(__name__)


class AgentStates(StatesGroup):
    """Стани для роботи з агентами."""
    chatting = State()
    selecting_agent = State()


@router.message(Command("agent"))
async def agent_start(message: Message, state: FSMContext):
    """Початок роботи з агентом."""
    await register_user_if_not_exists(message.from_user)
    
    orchestrator = get_orchestrator()
    agents_info = orchestrator.list_agents()
    
    # Клавіатура вибору агента
    keyboard = []
    for agent_name in agents_info.keys():
        keyboard.append([
            InlineKeyboardButton(
                text=f"🤖 {agent_name.title()}",
                callback_data=f"agent:{agent_name}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🎯 Авто (визначити)", callback_data="agent:auto")
    ])
    
    await message.answer(
        "🤖 **Вибери агента:**\n\n"
        "• **Code** - генерація коду\n"
        "• **Translate** - переклад текстів\n"
        "• **Research** - пошук інформації\n"
        "• **Writer** - написання текстів\n"
        "• **Test** - написання тестів\n"
        "• **Авто** - визначить автоматично",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    await state.set_state(AgentStates.selecting_agent)


@router.callback_query(F.data.startswith("agent:"))
async def agent_selected(callback: CallbackQuery, state: FSMContext):
    """Вибрано агента."""
    agent_type = callback.data.split(":")[1]
    
    await state.update_data(agent_type=agent_type if agent_type != "auto" else None)
    await state.set_state(AgentStates.chatting)
    
    await callback.message.edit_text(
        f"✅ Агент вибрано: **{agent_type.title()}**\n\n"
        "Тепер надішли своє повідомлення.\n"
        "Використай /stop щоб завершити розмову.",
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(AgentStates.chatting)
async def agent_chat(message: Message, state: FSMContext):
    """Розмова з агентом."""
    data = await state.get_data()
    agent_type = data.get("agent_type")
    
    status = await message.answer("🤔 Думаю...")
    
    try:
        orchestrator = get_orchestrator()
        
        # Streaming відповідь
        response = ""
        last_update = 0
        
        async for chunk in orchestrator.route_stream(message.text, agent_type):
            response += chunk
            
            # Оновлювати кожні 50 символів
            if len(response) - last_update > 50:
                await status.edit_text(f"🤖 {response}...")
                last_update = len(response)
        
        # Фінальна відповідь
        await status.edit_text(f"🤖 {response}")
        
        logger.info(f"Агент відповів користувачу {message.from_user.id}")
        
    except Exception as e:
        logger.exception(f"Помилка агента: {e}")
        await status.edit_text(f"❌ Помилка: {str(e)}")


@router.message(Command("stop"))
async def agent_stop(message: Message, state: FSMContext):
    """Завершити розмову з агентом."""
    await state.clear()
    await message.answer("✅ Розмову завершено.")


@router.message(Command("agents"))
async def list_agents(message: Message):
    """Список доступних агентів."""
    orchestrator = get_orchestrator()
    agents = orchestrator.list_agents()
    
    text = "🤖 **Доступні агенти:**\n\n"
    
    for name, capabilities in agents.items():
        text += f"**{name.title()}:**\n"
        for cap in capabilities:
            text += f"  • {cap}\n"
        text += "\n"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("multiagent"))
async def multi_agent_task(message: Message):
    """Складна задача через кілька агентів."""
    await register_user_if_not_exists(message.from_user)
    
    task = message.text.replace("/multiagent", "").strip()
    
    if not task:
        await message.answer(
            "🎯 **Multi-Agent System**\n\n"
            "Використання: /multiagent [задача]\n\n"
            "Приклад:\n"
            "/multiagent Напиши Python функцію для сортування + тести"
        )
        return
    
    status = await message.answer("🔄 Запуск мульти-агентної системи...")
    
    try:
        mas = get_multi_agent_system()
        result = await mas.plan_and_execute(task)
        
        await status.edit_text(f"✅ **Результат:**\n\n{result}", parse_mode="Markdown")
        
    except Exception as e:
        logger.exception("Помилка multi-agent")
        await status.edit_text(f"❌ Помилка: {str(e)}")
```

---

## Фаза 7: Frameworks

### 7.1. LangGraph Integration

**Додати залежності:** `requirements.txt`

```
langgraph>=0.0.30
langchain>=0.1.0
langchain-community
```

**Створити:** `bot/agents/frameworks/langgraph_example.py`

```python
"""Приклад використання LangGraph для workflow агентів."""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

from bot.agents.orchestrator import get_orchestrator


class AgentState(TypedDict):
    """Стан мульти-агентного workflow."""
    task: str
    plan: str
    code: str
    tests: str
    review: str
    iterations: Annotated[int, operator.add]


async def planner_node(state: AgentState) -> AgentState:
    """Вузол планування."""
    orchestrator = get_orchestrator()
    
    prompt = f"Створи план для задачі: {state['task']}"
    plan = await orchestrator.route(prompt, "research")
    
    return {"plan": plan, "iterations": 1}


async def coder_node(state: AgentState) -> AgentState:
    """Вузол генерації коду."""
    orchestrator = get_orchestrator()
    
    prompt = f"Напиши код згідно плану:\n{state['plan']}\n\nЗадача: {state['task']}"
    code = await orchestrator.route(prompt, "code")
    
    return {"code": code}


async def tester_node(state: AgentState) -> AgentState:
    """Вузол написання тестів."""
    orchestrator = get_orchestrator()
    
    prompt = f"Напиши тести для цього коду:\n```python\n{state['code']}\n```"
    tests = await orchestrator.route(prompt, "test")
    
    return {"tests": tests}


async def reviewer_node(state: AgentState) -> AgentState:
    """Вузол review коду."""
    orchestrator = get_orchestrator()
    
    prompt = (
        f"Code review:\n"
        f"Код:\n{state['code']}\n\n"
        f"Тести:\n{state['tests']}\n\n"
        "Оцінка: добре/потребує виправлень"
    )
    review = await orchestrator.route(prompt, "code")
    
    return {"review": review}


def should_retry(state: AgentState) -> str:
    """Визначає чи потрібно повторити."""
    if "потребує виправлень" in state["review"].lower() and state["iterations"] < 3:
        return "coder"
    return "end"


def create_coding_workflow() -> StateGraph:
    """
    Створює workflow для генерації коду.
    
    Flow: Planner → Coder → Tester → Reviewer → (retry if needed)
    """
    workflow = StateGraph(AgentState)
    
    # Додати вузли
    workflow.add_node("planner", planner_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("tester", tester_node)
    workflow.add_node("reviewer", reviewer_node)
    
    # Визначити граф
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "tester")
    workflow.add_edge("tester", "reviewer")
    
    # Умовний перехід
    workflow.add_conditional_edges(
        "reviewer",
        should_retry,
        {
            "coder": "coder",
            "end": END
        }
    )
    
    return workflow.compile()


async def run_coding_task(task: str) -> dict:
    """Виконати задачу через LangGraph."""
    workflow = create_coding_workflow()
    
    initial_state = {
        "task": task,
        "plan": "",
        "code": "",
        "tests": "",
        "review": "",
        "iterations": 0
    }
    
    result = await workflow.ainvoke(initial_state)
    return result
```

### 7.2. AutoGen Integration

**Створити:** `bot/agents/frameworks/autogen_example.py`

```python
"""Приклад використання AutoGen для мульти-агентних діалогів."""

# Примітка: AutoGen потребує OpenAI API або сумісний endpoint
# Для Ollama треба налаштувати custom LLM

from typing import List, Dict

# Це концептуальний приклад, потрібна адаптація для Ollama

async def create_autogen_agents():
    """
    Створює AutoGen агентів для Ollama.
    
    Примітка: Потрібна custom конфігурація для Ollama endpoint.
    """
    
    # Конфігурація для Ollama
    config_list = [{
        "model": "qwen2.5:7b-instruct-q5_K_M",
        "base_url": "http://localhost:11434/v1",  # Ollama OpenAI-compatible endpoint
        "api_key": "ollama"  # Dummy key
    }]
    
    # Приклад агентів (потребує autogen >= 0.2.0)
    """
    from autogen import AssistantAgent, UserProxyAgent
    
    coder = AssistantAgent(
        name="Coder",
        system_message="Ти експерт Python програміст",
        llm_config={"config_list": config_list}
    )
    
    tester = AssistantAgent(
        name="Tester",
        system_message="Ти експерт з тестування",
        llm_config={"config_list": config_list}
    )
    
    user_proxy = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config={"use_docker": False}
    )
    
    # Групова розмова
    from autogen import GroupChat, GroupChatManager
    
    group_chat = GroupChat(
        agents=[user_proxy, coder, tester],
        messages=[],
        max_round=10
    )
    
    manager = GroupChatManager(groupchat=group_chat)
    
    return user_proxy, manager
    """
    
    pass


# Для повної інтеграції див:
# https://microsoft.github.io/autogen/docs/Use-Cases/agent_chat
```

---

## Фаза 8: Моніторинг і оптимізація

### 8.1. Метрики агентів

**Створити SQL:** `bot/db/migrations/add_agent_metrics.sql`

```sql
CREATE TABLE IF NOT EXISTS agent_metrics (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    user_id BIGINT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    latency_ms INTEGER NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_agent_time (agent_name, created_at),
    INDEX idx_user (user_id)
);
```

**Створити:** `bot/agents/metrics.py`

```python
"""Метрики для моніторингу агентів."""

import logging
import time
from typing import Optional
from contextlib import asynccontextmanager

from bot.db.database import get_db_pool

logger = logging.getLogger(__name__)


class AgentMetrics:
    """Збір метрик роботи агентів."""
    
    @staticmethod
    async def log_request(
        agent_name: str,
        user_id: int,
        latency_ms: int,
        tokens_used: int = 0,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Логує запит до агента."""
        try:
            pool = get_db_pool()
            
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agent_metrics 
                    (agent_name, user_id, tokens_used, latency_ms, success, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    agent_name, user_id, tokens_used, latency_ms, success, error_message
                )
            
        except Exception as e:
            logger.error(f"Помилка збереження метрик: {e}")
    
    @staticmethod
    async def get_agent_stats(agent_name: str, days: int = 7) -> dict:
        """Статистика агента за період."""
        pool = get_db_pool()
        
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_requests,
                    AVG(latency_ms) as avg_latency,
                    SUM(tokens_used) as total_tokens,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) * 100 as success_rate
                FROM agent_metrics
                WHERE agent_name = $1 
                AND created_at > NOW() - INTERVAL '%s days'
                """,
                agent_name, days
            )
        
        return dict(row) if row else {}
    
    @staticmethod
    @asynccontextmanager
    async def track_request(agent_name: str, user_id: int):
        """Context manager для автоматичного трекінгу."""
        start_time = time.time()
        error = None
        
        try:
            yield
        except Exception as e:
            error = str(e)
            raise
        finally:
            latency_ms = int((time.time() - start_time) * 1000)
            
            await AgentMetrics.log_request(
                agent_name=agent_name,
                user_id=user_id,
                latency_ms=latency_ms,
                success=error is None,
                error_message=error
            )


# Використання:
# async with AgentMetrics.track_request("code_agent", user_id):
#     result = await agent.think(prompt)
```

---

## 🎯 Рекомендований порядок реалізації

### **Тиждень 1: Базові агенти**
- [ ] Створити `bot/agents/base_agent.py`
- [ ] Створити `bot/agents/specialized_agents.py` (5 агентів)
- [ ] Створити `bot/agents/orchestrator.py`
- [ ] Тести базових агентів

### **Тиждень 2: Tools система**
- [ ] Створити `bot/agents/tools/base_tool.py`
- [ ] Створити `bot/agents/tools/web_tools.py`
- [ ] Створити `bot/agents/tools/code_tools.py`
- [ ] Створити `bot/agents/tools/tool_manager.py`
- [ ] Інтегрувати tools в агентів

### **Тиждень 3: Пам'ять**
- [ ] Створити `bot/agents/memory/short_term.py`
- [ ] Міграція БД для agent_memories
- [ ] Створити `bot/agents/memory/long_term.py`
- [ ] Інтегрувати пам'ять в базових агентів

### **Тиждень 4: Мульті-агентні системи**
- [ ] Створити `bot/agents/multi_agent_system.py`
- [ ] Реалізувати plan_and_execute
- [ ] Реалізувати debate між агентами
- [ ] Тести мульті-агентних сценаріїв

### **Тиждень 5: Telegram інтеграція**
- [ ] Створити `bot/handlers/agent_handler.py`
- [ ] FSM для вибору агента
- [ ] Streaming відповіді в Telegram
- [ ] Команди: /agent, /agents, /multiagent, /stop

### **Тиждень 6: Frameworks (опціонально)**
- [ ] LangGraph integration (`bot/agents/frameworks/langgraph_example.py`)
- [ ] AutoGen exploration (якщо потрібно)
- [ ] Документація workflows

### **Тиждень 7: Моніторинг**
- [ ] Міграція БД для agent_metrics
- [ ] Створити `bot/agents/metrics.py`
- [ ] Інтегрувати трекінг в усі агенти
- [ ] Dashboard для метрик (опціонально)

### **Тиждень 8: Оптимізація та тести**
- [ ] Unit тести для всіх компонентів
- [ ] Integration тести
- [ ] Benchmarking продуктивності
- [ ] Документація

---

## 📚 Ресурси та посилання

### Frameworks
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **AutoGen**: https://microsoft.github.io/autogen/
- **CrewAI**: https://docs.crewai.com/

### AI Agents patterns
- **ReAct**: https://arxiv.org/abs/2210.03629
- **Chain-of-Thought**: https://arxiv.org/abs/2201.11903
- **Tree of Thoughts**: https://arxiv.org/abs/2305.10601

### Ollama
- **Ollama Python SDK**: https://github.com/ollama/ollama-python
- **Qwen 2.5**: https://qwenlm.github.io/blog/qwen2.5/

### Tools
- **Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools/

---

## 💡 Best Practices

1. **Спеціалізація агентів**: Кожен агент має чітку роль та system prompt
2. **Композиція**: Складні задачі = кілька простих агентів
3. **Пам'ять**: Short-term для контексту, long-term для персоналізації
4. **Tools**: Агенти мають доступ до інструментів (web search, code execution)
5. **Моніторинг**: Завжди логувати метрики (latency, tokens, success rate)
6. **Testing**: Unit + integration тести для кожного агента
7. **Error handling**: Graceful degradation при помилках LLM

---

## 🚀 Початок роботи

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Запустити Ollama
docker-compose up -d ollama

# 3. Створити структуру
mkdir -p bot/agents/{tools,memory,frameworks}

# 4. Почати з базових агентів
python -c "from bot.agents.orchestrator import get_orchestrator; print(get_orchestrator())"

# 5. Запустити бота
python -m bot.app
```

---

**Успішної розробки AI-агентів! 🤖**
