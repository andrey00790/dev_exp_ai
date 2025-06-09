AGENTS.md — Руководство для Codex по проекту AI Assistant MVP

🎯 Назначение

Codex используется как инженер-ассистент для реализации AI Assistant MVP. Он работает итеративно по задачам, генерируя код, тесты и документацию.

📂 Архитектура проекта и структура каталогов

Основной каталог: ai_assistant/

├── app/                  # FastAPI entrypoint
│   ├── main.py
│   └── api/v1/           # API endpoints
├── services/             # Use-cases, orchestration
├── llm/                  # LLM subsystem
│   └── llm_plugins/
├── vectorstore/          # Qdrant adapters
├── database/             # SQLAlchemy, migrations
├── models/               # Pydantic schemas
├── core/cron/            # bootstrap, retrain logic
├── gui/                  # Chainlit/Streamlit GUI
├── tests/                # unit/, integration/, e2e/
├── datasets/, docs/, helm/, scripts/
├── Makefile, docker-compose.yaml

Файлы, создаваемые Codex, должны следовать этой структуре.

🧱 Правила кодирования

Python 3.11+

PEP8 + type hints + flake8 совместимость

Именование: snake_case для файлов/функций, PascalCase для классов

Принципы архитектуры: SOLID, hexagonal

Описание логики и запуска — в README.md

🧪 Правила тестирования

Используется pytest, опционально pytest-cov

Команды: pytest -v, pytest --maxfail=1 --disable-warnings -q

Минимальное покрытие: 80%

Все внешние источники (GitLab, Confluence) мокируются

Скрипты в core/cron покрываются unit/integration-тестами

🚀 Итерационный процесс

Каждая задача оформляется в виде Iteration Canvas с:

Целью и контекстом

Prompt (запрос на генерацию)

Ожидаемыми артефактами (модули, тесты, README)

Критериями приёмки (в том числе test coverage)

Codex:

Генерирует файлы с заголовками # FILE: <путь>

Выполняет make up, pytest, make healthcheck

Возвращает diff + patch + логи тестов

Готовит README.md

🔄 PR и ревью

Названия PR: [feature|fix] <что сделано>

В теле: summary, как протестировано, покрытие, потенциальные риски

Проверка на наличие утечек .env и секретов — обязательно

Все PR проходят ревью (Codex или инженер)

🔒 Безопасность

Используем .env.local (в .gitignore) для секретов

Шаблон .env.example обязателен и поддерживается

Никакие реальные токены/логины не должны попадать в код/PR

Предпочтительно использовать pre-commit для проверки секретов

Codex должен следовать данному документу при каждой итерации.



🧠 Codex-Ready Development Plan for AI Assistant MVP

This plan structures your AI Assistant MVP project to work effectively with OpenAI Codex through iterative, test-driven, and architecture-conscious development. Each iteration will be encoded via task prompts (Iteration Canvases) and executed fully in Codex web interface.

1. 🌟 Mission & Scope

AI Assistant MVP Goals:

Speed up architecture design and review

Auto-generate standardized documents (SRS, NFR, Use Cases, RFC, ADR, diagrams)

Cover discovery → delivery → support → feedback → re-train cycle

Work offline with privacy & reproducibility

Maintain complete project history and state resumability

2. 👥 Roles Supported

Developer (web, mobile, backend)

System Analyst / Business Analyst

Architect (System/Business)

DevOps / SRE

QA Engineer / SDET

Admin / Security Engineer

Tech Support

Assistant must respond and produce materials relevant to each role’s context.

3. ⚖️ Operating & Deployment Constraints

Local Deployment Standards:

All secrets in .env.local (ignored by Git)

.env.example must reflect all required keys

Offline mode via local URLs for Qdrant, LLM, PlantUML, etc.

Docker Compose setup included for all infra

Required services:

Qdrant

PostgreSQL

Local LLM via Olama or equivalent

FastAPI service with OpenAPI and test endpoints

System Requirements:

OS: macOS 15.5+ or Linux

Python 3.11+

Docker Desktop 4.4+, Docker Compose

Helm 3.8+ for K8s (prod deploy)

CPU-only support (no GPU), RAM ≥24GB, Disk ≥30GB

4. ✅ Codex Workflow Structure

4.1 Resume Prompt

Stored in resume_prompt.txt, always included in Codex prompt:

You are Codex assistant for AI Assistant MVP.
Follow AGENTS.md instructions.
Every task is defined by an Iteration Canvas (goal, prompt, criteria).
Generate: working code + tests + README.
Run: pytest + make up + make healthcheck.
Return: patch + diff + test summary.

When generating files, use structure and locations from the project layout below.
Use headings `# FILE: path/to/file.py` for each file.
Output only code, no extra commentary.

4.2 AGENTS.md (in project root)

Includes:

Module structure and naming

Coding style and type hints

Expected CLI commands

Testing & coverage rules (80%+)

Pull request format

CI steps

Instructions for secure handling of .env files

4.3 Iteration Canvas Template (each task)

## Итерация: <название>
**Цель:**
**Связь с MVP:**
**GPT Prompt:**
**Ожидаемые артефакты:**
- `*.py`
- `tests/*.py`
- `README.md`
**Расположение файлов:**
- `app/api/v1/*.py`
- `services/*.py`
- `llm/`
- `vectorstore/`
- `core/cron/*.py`
- `database/`, `models/`
- `tests/unit/`, `tests/integration/`
**Критерии приёмки:**
- Все тесты проходят через `pytest`
- Покрытие тестами ≥ 80%
- Endpoint `/health` возвращает 200 (если применимо)
**Зависимости:**
- `.env.example`, существующие модули

5. 🔁 Рекомендуемый порядок итераций

bootstrap_init — scaffold проекта, docker-compose, Makefile, .env, healthcheck API

infra_up — проверка доступности сервисов, pytest, smoke-тесты

llm_loader_base — подключение OpenAI & Olama плагинов, настройка модели

semantic_indexing — загрузка из GitLab/Confluence, индексация в Qdrant

feedback_loop — API оценки, сохранение, база данных, интерфейс

search_eval_suite — генерация тестов для precision/recall

gui_chainlit_start — GUI (Chainlit/Streamlit) для поиска и обратной связи

📚 Кодирование и архитектура

Python 3.11+, PEP‑8, type hints обязательны

Решения документируются кратко в README

Следовать принципам SOLID и hexagonal architecture

Именование: snake_case для файлов/функций, PascalCase для классов

Диаграммы (PlantUML/C4/UML) оформляются в markdown или .puml, .json

Критерии приёмки по кодированию:

Читаемый, модульный код без дублирования

Соответствие PEP8 и архитектурному стилю проекта

Разделение бизнес-логики и API-интерфейсов

Файлы не превышают разумного объёма (>300 строк делятся)

Все зависимости явно указаны в requirements.txt

🔪 Тестирование

Используем pytest, опционально pytest-cov

Команды запуска: pytest -v и pytest --maxfail=1 --disable-warnings -q

Требование: покрытие ≥ 80% для каждого модуля

Моки обязательны для всех внешних API (Confluence, GitLab, и пр.)

Модули в core/cron/* покрываются unit или integration тестами

Критерии приёмки по тестированию:

Полное покрытие тестами добавленных функций

Автоматическая проверка через CI

Покрытие кодом > 80% в отчёте coverage

Все тесты проходят стабильно, без flaky-тестов

Отдельные fixtures и mocks для каждого внешнего источника

📦 Артефакты

Каждая итерация возвращает:

Diff модифицированных/новых файлов

Код + тесты

README.md с инструкциями

Логи make test и make healthcheck

(по возможности) отчёт покрытия или badge

🔐 Безопасность и доступ

Все переменные окружения выносятся в .env.example, а реальные значения — в .env.local (в .gitignore)

Никогда не публиковать реальные токены, логины и пароли в публичных PR

Проверка на наличие секретов в коде и PR — предпочтительно через линтер или pre-commit

Все код-ревью проходят через Codex или ревью с инженером

🤍 Финальные критерии готовности MVP

Все ключевые фичи покрыты из test plan

1000 запросов проходят стресс‑тест с ≥90% успешностью

Полная воспроизводимость через make bootstrap на новом окружении

Выходные данные импортируются в Confluence/Jira/Docs

Дообучение LLM по фидбэку происходит корректно

