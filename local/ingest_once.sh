#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# ingest_once.sh
#
# Универсальный скрипт для:
#   • Локального запуска (в каталоге проекта)
#   • Запуска внутри Docker-контейнера (где рабочая папка /app)
#
# Логика:
#   1) Определяем, где находится .env.local:
#        • Если файл лежит рядом со скриптом — это локальный режим.
#        • Если файл лежит в /app/.env.local — это Docker-режим.
#   2) Загружаем переменные окружения из найденного .env.local (при локальном запуске)
#   3) Ищем requirements.txt:
#        • Сначала проверяем в каталоге, где лежит скрипт (локально) или /app (Docker).
#        • Если не найден — проверяем в поддиректории orchestrator.
#        • Если нет ни там, ни там — выходим с ошибкой.
#   4) Переходим в ту папку, где лежит requirements.txt.
#   5) Устанавливаем зависимости (pip install -r requirements.txt).
#   6) (Опционально) Запускаем ingest_data.py.
# ──────────────────────────────────────────────────────────────────────────────

set -e

# 1) Найдём путь до каталога скрипта
SCRIPT_DIR="$(cd "$(dirname "$0")" >/dev/null 2>&1 && pwd)"

# 2) Попытаемся загрузить .env.local (локальный или Docker)
#    Сначала проверим локальный .env.local рядом со скриптом
if [ -f "${SCRIPT_DIR}/.env.local" ]; then
    echo "🔄 Найден локальный .env.local в ${SCRIPT_DIR}"
    export $(grep -v '^#' "${SCRIPT_DIR}/.env.local" | xargs)
#    Заметим: при локальном запуске просто export переменные (подходит для большинства случаев).
elif [ -f "/app/.env.local" ]; then
    echo "🔄 Найден Docker-.env.local в /app/.env.local"
    export $(grep -v '^#' "/app/.env.local" | xargs)
else
    echo "⚠️  .env.local не найден ни в ${SCRIPT_DIR}, ни в /app/"
    # Но продолжаем, если переменные не критичны
fi

# 3) Определяем, где искать requirements.txt и устанавливать зависимости
#    Локально: SCRIPT_DIR/requirments.txt или SCRIPT_DIR/orchestrator/requirements.txt
#    В Docker:     /app/requirements.txt или /app/orchestrator/requirements.txt

if [ -f "${SCRIPT_DIR}/requirements.txt" ]; then
    echo "✅ Найден requirements.txt в ${SCRIPT_DIR}"
    TARGET_DIR="${SCRIPT_DIR}"
elif [ -f "${SCRIPT_DIR}/orchestrator/requirements.txt" ]; then
    echo "✅ Найден requirements.txt в ${SCRIPT_DIR}/orchestrator"
    TARGET_DIR="${SCRIPT_DIR}/orchestrator"
elif [ -f "/app/requirements.txt" ]; then
    echo "✅ Найден requirements.txt в /app"
    TARGET_DIR="/app"
elif [ -f "/app/orchestrator/requirements.txt" ]; then
    echo "✅ Найден requirements.txt в /app/orchestrator"
    TARGET_DIR="/app/orchestrator"
else
    echo "❌ requirements.txt не найден ни локально, ни в /app/"
    exit 1
fi

# 4) Переходим в папку с requirements.txt
cd "${TARGET_DIR}"

# 5) Устанавливаем зависимости
echo "📦 Установка зависимостей из ${TARGET_DIR}/requirements.txt..."
pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt
echo "✅ Зависимости установлены."

# 6) Запускаем ingest_data.py, если он есть и если вы хотите сразу инжестить

 echo "▶️ Запуск ingest_data.py"
 python "${SCRIPT_DIR}/ingest_data.py" --no-video --no-jira

echo "🎉 ingest_once.sh завершил работу."