#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ingest_data.py

Скрипт для импорта данных из Confluence, Jira, GitLab и видео в Qdrant.

Версия финальная:
  - Загрузка переменных окружения из .env.local (python-dotenv + find_dotenv)
  - Использование html.parser вместо lxml
  - Преобразование SHA-1-строки в валидный UUID-5 для id точек
  - Оптимизированный импорт проектов из GitLab:
      * iterator=True для ленивой загрузки
      * simple=True для минимального JSON (включая default_branch и path_with_namespace)
      * per_page=100 для уменьшения числа запросов
  - Пересоздание коллекции через collection_exists + create_collection
  - Параллельный импорт из Confluence с ретраями (urllib3 Retry + ThreadPoolExecutor)
  - Логирование ключевых этапов и ENV
"""

import os
import re
import argparse
import hashlib
import textwrap
import tempfile
import subprocess
import json
import logging
import sys
import uuid
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup  # html.parser встроен в Python
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, http
from atlassian import Jira
import gitlab

# Импорт модуля bootstrap ingestion
try:
    from ingest_bootstrap import ingest_bootstrap_materials
except ImportError as e:
    logger.warning(f"Модуль ingest_bootstrap недоступен: {e}")
    ingest_bootstrap_materials = None

# ──────────────────────────────────────────────────────────────────────────────
# 0. Загрузка переменных окружения из .env.local
# ──────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv, find_dotenv  # pip install python-dotenv

dotenv_path = find_dotenv(".env.local", raise_error_if_not_found=False)
if dotenv_path:
    load_dotenv(dotenv_path)
    print(f"✅ Loaded .env.local from: {dotenv_path}")
else:
    print("⚠️  .env.local не найден. Продолжаем без загрузки.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ingest_data")

logger.info(f"QDRANT_URL     = {os.getenv('QDRANT_URL')}")
logger.info(f"PLANTUML_URL   = {os.getenv('PLANTUML_URL')}")
logger.info(f"MODEL_URL      = {os.getenv('MODEL_URL')}")
logger.info(f"CONFLUENCE_URL = {os.getenv('CONFLUENCE_URL')}")
logger.info(f"JIRA_URL       = {os.getenv('JIRA_URL')}")

# ──────────────────────────────────────────────────────────────────────────────
# 1. Инициализация клиента Qdrant
# ──────────────────────────────────────────────────────────────────────────────
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
# Указываем prefer_grpc=False, чтобы работать только по HTTP
Q = QdrantClient(url=qdrant_url, prefer_grpc=False)
COL = "docs"


ENC = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
wrap = lambda s, n=1500: textwrap.wrap(s, n, break_long_words=False, break_on_hyphens=False)

NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

def sha_str(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()

def sha_uuid(s: str) -> str:
    return str(uuid.uuid5(NAMESPACE, s))


# ──────────────────────────────────────────────────────────────────────────────
# 2. Функция для создания сессии с ретраями
# ──────────────────────────────────────────────────────────────────────────────
def create_retry_session(
    total_retries: int = 5,
    backoff_factor: float = 1.0,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
    allowed_methods: tuple[str, ...] = ("HEAD", "GET", "OPTIONS")
) -> requests.Session:
    """
    Возвращает requests.Session с настроенной стратегией ретраев:
    - total_retries: общее число попыток (включая первую)
    - backoff_factor: множитель для экспоненциальной задержки (в секундах)
    - status_forcelist: HTTP-статусы, при которых делать ретрай
    - allowed_methods: HTTP-методы, для которых разрешены ретраи
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=total_retries,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        backoff_factor=backoff_factor,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# ──────────────────────────────────────────────────────────────────────────────
# 3. Параллельный импорт всех страниц Confluence
# ──────────────────────────────────────────────────────────────────────────────
def ingest_conf_all_batch(
    limit: int = 10000,
    max_workers: int = 5,
    space_batch_size: int = 200,
):
    """
    Пакетный (batch) импорт из Confluence по всем пространствам:
    1) Пагинация при получении списка всех space_key
    2) Для каждого space делаем первичный запрос, чтобы узнать totalSize и вычислить стартовые оффсеты
    3) Собираем задачи (space_key, start) для всех страниц всех пространств
    4) Параллельно загружаем все страницы из всех пространств через один ThreadPoolExecutor
    5) Обрабатываем и возвращаем записи
    """
    base = os.getenv("CONFLUENCE_URL")
    token = os.getenv("CONFLUENCE_BEARER_TOKEN")
    if not base or not token:
        logger.warning("CONFLUENCE_URL или CONFLUENCE_BEARER_TOKEN не заданы → пропуск Confluence")
        return

    headers = {"Authorization": f"Bearer {token}"}
    session = create_retry_session()

    # 1) Пагинация при получении всех пространств
    space_keys = []
    start = 0
    while True:
        try:
            r_space = session.get(
                f"{base}/rest/api/space",
                params={"limit": space_batch_size, "start": start},
                headers=headers,
                timeout=30
            )
            r_space.raise_for_status()
            data = r_space.json()
            results = data.get("results", [])
            if not results:
                break

            for sp in results:
                key = sp.get("key")
                if key:
                    space_keys.append(key)

            # Если вернулось меньше, чем batch_size, это последняя страница
            if len(results) < space_batch_size:
                break

            start += space_batch_size
        except Exception as e:
            logger.error(f"[Confluence] Ошибка при получении списка spaces (start={start}): {e}")
            return

    if not space_keys:
        logger.info("[Confluence] Не найдено ни одного пространства → завершение")
        return

    logger.info(f"[Confluence] Будем импортировать следующие spaces: {space_keys}")

    # 2) Для каждого space узнаем totalSize и генерируем список стартовых оффсетов
    tasks = []  # список кортежей (space_key, start)
    for sk in space_keys:
        try:
            init_resp = session.get(
                f"{base}/rest/api/content",
                params={"spaceKey": sk, "limit": limit, "start": 0, "expand": "body.storage"},
                headers=headers,
                timeout=30
            )
            init_resp.raise_for_status()
            init_json = init_resp.json()
            total_size = init_json.get("totalSize") or init_json.get("size")
            if total_size is None:
                raise ValueError("totalSize не найден")
            total = int(total_size)
            num_pages = math.ceil(total / limit)
            start_values = [i * limit for i in range(num_pages)]
            logger.info(f"[Confluence] spaceKey={sk}: всего записей={total}, страниц={num_pages}")
            for start_val in start_values:
                tasks.append((sk, start_val))
        except Exception as e:
            logger.error(f"[Confluence] Ошибка при инициализации spaceKey={sk}: {e}")
            continue

    if not tasks:
        logger.info("[Confluence] Нет задач для загрузки страниц → завершение")
        return

    logger.info(f"[Confluence] Всего задач для загрузки страниц: {len(tasks)} (макс {max_workers} потоков одновременно)")

    # 3) Функция для загрузки одной страницы для заданного space
    def fetch_page(args: tuple[str, int]) -> tuple[str, list[dict]]:
        sk, start_val = args
        try:
            resp = session.get(
                f"{base}/rest/api/content",
                params={"spaceKey": sk, "limit": limit, "start": start_val, "expand": "body.storage"},
                headers=headers,
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            logger.info(f"[Confluence] spaceKey={sk} start={start_val}: {len(results)} записей")
            return sk, results
        except Exception as e:
            logger.warning(f"[Confluence] Ошибка загрузки spaceKey={sk} start={start_val}: {e}")
            return sk, []

    # 4) Параллельная загрузка всех страниц
    all_results_by_space: dict[str, list[dict]] = {sk: [] for sk in space_keys}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(fetch_page, task): task for task in tasks}
        for future in as_completed(future_to_task):
            sk, page_results = future.result()
            if page_results:
                all_results_by_space.setdefault(sk, []).extend(page_results)

    # 5) Итерация по загруженным записям и возврат результатов
    for sk, records in all_results_by_space.items():
        logger.info(f"[Confluence] spaceKey={sk}: всего загружено записей={len(records)}")
        for rec in records:
            try:
                page_id = rec.get("id")
                title = rec.get("title", "")
                body_html = rec["body"]["storage"]["value"]
                soup = BeautifulSoup(body_html, "html.parser")
                text_content = soup.get_text(" ", strip=True)
                url = f"{base}/pages/{page_id}"
                for ch in wrap(text_content):
                    sha_hex = sha_str(url + ch[:40])
                    uid = sha_uuid(sha_hex)
                    payload = {"src": "conf", "space": sk, "url": url, "text": ch}
                    yield uid, ch, payload
            except Exception as e:
                logger.error(f"[Confluence] Ошибка при обработке id={rec.get('id')} spaceKey={sk}: {e}")
                continue

    logger.info("[Confluence] Импорт завершён")


# ──────────────────────────────────────────────────────────────────────────────
# 4. Импорт из Jira
# ──────────────────────────────────────────────────────────────────────────────
def ingest_jira(cfg):
    if not os.getenv("JIRA_URL") or not os.getenv("JIRA_USERNAME") or not os.getenv("JIRA_PASSWORD"):
        logger.warning("JIRA_URL/JIRA_USERNAME/JIRA_PASSWORD не заданы → пропуск Jira")
        return

    jira = Jira(os.getenv("JIRA_URL"), os.getenv("JIRA_USERNAME"), os.getenv("JIRA_PASSWORD"))
    for proj, jql in cfg.items():
        logger.info(f"[Jira] Импорт проекта {proj} по JQL: {jql}")
        try:
            issues = jira.jql(jql).get("issues", [])
        except Exception as e:
            logger.error(f"[Jira] Ошибка JQL для проекта {proj}: {e}")
            continue
        for iss in issues:
            try:
                summary = iss["fields"].get("summary") or ""
                description = iss["fields"].get("description") or ""
                body = summary + "\n" + description
                url = f"{os.getenv('JIRA_URL')}/browse/{iss['key']}"
                for ch in wrap(body):
                    sha_hex = sha_str(url + ch[:40])
                    uid = sha_uuid(sha_hex)
                    payload = {"src": "jira", "project": proj, "url": url, "text": ch}
                    yield uid, ch, payload
            except Exception as e:
                logger.error(f"[Jira] Ошибка при обработке issue {iss.get('key')} в проекте {proj}: {e}")
                continue
    logger.info("[Jira] Импорт завершён")


# ──────────────────────────────────────────────────────────────────────────────
# 5. Импорт из GitLab (оптимизировано)
# ──────────────────────────────────────────────────────────────────────────────
def git_clients_all():
    out = {}
    for k, v in os.environ.items():
        m = re.match(r"GITLAB_(\d+)_ALIAS", k)
        if m:
            suf = m.group(1)
            alias = v
            url = os.getenv(f"GITLAB_{suf}_URL")
            token = os.getenv(f"GITLAB_{suf}_TOKEN")
            if url and token:
                try:
                    gl = gitlab.Gitlab(url, private_token=token)
                    gl.auth()
                    out[alias] = gl
                except Exception as e:
                    logger.error(f"[GitLab] Ошибка аутентификации [{alias}]: {e}")
    return out

def ingest_git_all():
    clients = git_clients_all()
    if not clients:
        logger.warning("[GitLab] Нет настроенных клиентов → пропуск GitLab")
        return

    for alias, gl in clients.items():
        logger.info(f"[GitLab] Импорт проектов [{alias}]")
        projects = gl.projects.list(
            iterator=True,
            membership=True,
            simple=True,
            per_page=100
        )
        for prj in projects:
            try:
                project = gl.projects.get(prj.id, lazy=True)
            except Exception as e:
                logger.error(f"[GitLab] Не удалось получить проект ID={prj.id}: {e}")
                continue

            used_ref = prj.default_branch or "main"
            logger.info(f"[GitLab] Проект={prj.path_with_namespace}, default_branch={used_ref}")
            try:
                tree_iterator = project.repository_tree(
                    ref=used_ref,
                    recursive=True,
                    iterator=True,
                    per_page=100
                )
            except gitlab.exceptions.GitlabGetError as e:
                if e.response_code == 404:
                    logger.warning(f"[GitLab] 404 Tree Not Found для проект ID={prj.id}, ref={used_ref} → пропуск")
                else:
                    logger.error(f"[GitLab] Ошибка при получении tree для проект ID={prj.id}: {e}")
                continue

            for node in tree_iterator:
                if node["type"] == "blob" and re.search(r"\.(py|go|php|js|ts)$", node["path"]):
                    try:
                        file_obj = project.files.get(
                            file_path=node["path"],
                            ref=used_ref
                        )
                        code = file_obj.decode().decode()
                    except gitlab.exceptions.GitlabGetError as e:
                        if e.response_code == 404:
                            logger.warning(f"[GitLab] File not found {node['path']} in project ID={prj.id}")
                        else:
                            logger.error(f"[GitLab] Ошибка при получении файла {node['path']} в проект ID={prj.id}: {e}")
                        continue

                    url = (
                        f"{gl.url}/{prj.path_with_namespace}"
                        f"/-/blob/{used_ref}/{node['path']}"
                    )
                    for ch in wrap(code):
                        sha_hex = sha_str(f"{alias}:{prj.path_with_namespace}:{node['path']}:{ch[:40]}")
                        uid = sha_uuid(sha_hex)
                        payload = {
                            "src":   "git",
                            "alias": alias,
                            "repo":  prj.path_with_namespace,
                            "path":  node["path"],
                            "url":   url,
                            "text":  ch
                        }
                        yield uid, ch, payload

    logger.info("[GitLab] Импорт завершён")


# ──────────────────────────────────────────────────────────────────────────────
# 6. Импорт из видео (WhisperX)
# ──────────────────────────────────────────────────────────────────────────────
def ingest_video(urls):
    if not urls:
        return

    logger.info(f"[Video] Импорт видео: {urls}")
    for url in urls:
        with tempfile.NamedTemporaryFile(suffix=".mp3") as wav:
            subprocess.run(
                ["ffmpeg", "-y", "-i", url, "-vn", "-ac", "1", "-ar", "16000", wav.name],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            try:
                txt = subprocess.check_output(
                    ["whisperx", wav.name, "--model", "small", "--output", "json"]
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"[Video] WhisperX ошибка для {url}: {e}")
                continue
            data = json.loads(txt)
            segments = data.get("segments", [])
            full_text = " ".join(seg.get("text", "") for seg in segments)
            for ch in wrap(full_text):
                sha_hex = sha_str(url + ch[:40])
                uid = sha_uuid(sha_hex)
                payload = {"src": "video", "url": url, "text": ch}
                yield uid, ch, payload
    logger.info("[Video] Импорт завершён")


# ──────────────────────────────────────────────────────────────────────────────
# 7. Upsert в Qdrant с UUID-5
# ──────────────────────────────────────────────────────────────────────────────
def upsert(batch):
    if not batch:
        return
    texts = [b[1] for b in batch]
    emb_vectors = ENC.encode(texts).tolist()
    points = []
    for (uid_str, _, payload), vec in zip(batch, emb_vectors):
        valid_uuid = sha_uuid(uid_str)
        point = http.models.PointStruct(
            id=valid_uuid,
            vector=vec,
            payload=payload
        )
        points.append(point)
    Q.upsert(COL, points)


# ──────────────────────────────────────────────────────────────────────────────
# 8. Пересоздание коллекции Qdrant
# ──────────────────────────────────────────────────────────────────────────────
def recreate():
    try:
        Q.delete_collection(COL)
        logger.info(f"Коллекция \"{COL}\" удалена")
    except Exception as e:
        logger.info(f"Коллекция \"{COL}\" не существовала или ошибка удаления: {e}")
    
    Q.create_collection(
        collection_name=COL,
        vectors_config=http.models.VectorParams(
            size=ENC.get_sentence_embedding_dimension(),
            distance="Cosine"
        )
    )
    logger.info(f"Коллекция Qdrant \"{COL}\" создана заново")


# ──────────────────────────────────────────────────────────────────────────────
# 9. Главная функция
# ──────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Ingest data from Bootstrap/Confluence/Jira/GitLab/Video")
    parser.add_argument("--no-bootstrap", action="store_true", help="Отключить импорт из Bootstrap материалов")
    parser.add_argument("--no-confluence", action="store_true", help="Отключить импорт из Confluence")
    parser.add_argument("--no-jira", action="store_true", help="Отключить импорт из Jira")
    parser.add_argument("--no-gitlab", action="store_true", help="Отключить импорт из GitLab")
    parser.add_argument("--no-video", action="store_true", help="Отключить импорт из видео")
    parser.add_argument("--bootstrap-dir", default="bootstrap", help="Путь к папке с bootstrap материалами")
    parser.add_argument("--jira", help="Пример: DEV:\"project = DEV\",OPS:\"project = OPS\"")
    parser.add_argument("--videos", help="Список URL видео через запятую")
    parser.add_argument("--confluence-spaces", help="Список ключей пространств Confluence через запятую (если не указан — перебрать все)")
    parser.add_argument("--confluence-workers", type=int, default=5, help="Число потоков для параллельного импорта из Confluence")
    args = parser.parse_args()

    recreate()

    batch = []
    BATCH_LIMIT = 64

    # 9.0 Импорт из Bootstrap материалов (новый источник)
    if not args.no_bootstrap and ingest_bootstrap_materials:
        logger.info("[Bootstrap] Начинаем импорт bootstrap материалов...")
        try:
            for rec in ingest_bootstrap_materials(args.bootstrap_dir):
                batch.append(rec)
                if len(batch) >= BATCH_LIMIT:
                    upsert(batch)
                    batch = []
            if batch:
                upsert(batch)
                batch = []
        except Exception as e:
            logger.error(f"[Bootstrap] Ошибка при импорте bootstrap материалов: {e}")
    elif not args.no_bootstrap:
        logger.warning("[Bootstrap] Модуль ingest_bootstrap недоступен, пропускаем bootstrap материалы")

    # 9.1 Импорт из Confluence (параллельно)
    if not args.no_confluence:
        # Собираем ключи пространств, если переданы
        if args.confluence_spaces:
            space_keys = args.confluence_spaces.split(",")
        else:
            space_keys = [None]  # None означает "пробежаться по всем"
        for sk in space_keys:
            for rec in ingest_conf_all_batch(limit=10000, max_workers=args.confluence_workers):
                batch.append(rec)
                if len(batch) >= BATCH_LIMIT:
                    upsert(batch)
                    batch = []
        if batch:
            upsert(batch)
            batch = []

    # 9.2 Импорт из Jira
    if not args.no_jira and args.jira:
        jira_cfg = dict(pair.split(":", 1) for pair in args.jira.split(","))
        for rec in ingest_jira(jira_cfg):
            batch.append(rec)
            if len(batch) >= BATCH_LIMIT:
                upsert(batch)
                batch = []
        if batch:
            upsert(batch)
            batch = []

    # 9.3 Импорт из GitLab
    if not args.no_gitlab:
        for rec in ingest_git_all():
            batch.append(rec)
            if len(batch) >= BATCH_LIMIT:
                upsert(batch)
                batch = []
        if batch:
            upsert(batch)
            batch = []

    # 9.4 Импорт из видео
    if not args.no_video and args.videos:
        video_urls = args.videos.split(",")
        for rec in ingest_video(video_urls):
            batch.append(rec)
            if len(batch) >= BATCH_LIMIT:
                upsert(batch)
                batch = []
        if batch:
            upsert(batch)

    logger.info("✅ Ингест данных завершён")


# ──────────────────────────────────────────────────────────────────────────────
# 9. Запуск для отладки из IDE
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) == 1:
        logger.info("Аргументы не переданы, подставляем примерные значения …")
        example_args = [
        "--no-confluence",
        "--no-jira",
        "--no-video",
        ]
        sys.argv.extend(example_args)
    main()