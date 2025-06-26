#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль управления пользовательскими настройками и синхронизацией
User Configuration and Sync Management Module
"""

import os
import json
import logging
import asyncio
import psycopg2
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from atlassian import Confluence, Jira
from gitlab import Gitlab
import aiofiles
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import PyPDF2
import docx
from ebooklib import epub
import magic
from psycopg2.extras import RealDictCursor

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UserConfig:
    """Конфигурация пользователя"""
    user_id: int
    username: str
    email: str
    settings: Dict[str, Any]

@dataclass
class DataSourceConfig:
    """Конфигурация источника данных"""
    source_type: str
    source_name: str
    is_enabled_semantic_search: bool
    is_enabled_architecture_generation: bool
    connection_config: Dict[str, Any]
    last_sync_at: Optional[datetime] = None
    sync_status: str = 'pending'
    sync_schedule: Optional[str] = None
    auto_sync_on_startup: bool = False

@dataclass
class SyncTask:
    """Задача синхронизации"""
    task_id: int
    user_id: int
    task_type: str  # 'manual' or 'scheduled'
    sources: List[str]
    status: str = 'pending'
    progress_percentage: int = 0
    total_items: int = 0
    processed_items: int = 0
    error_count: int = 0

@dataclass
class User:
    id: int
    username: str
    email: str

class EncryptionManager:
    """Менеджер шифрования для паролей и токенов"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Получение или создание ключа шифрования"""
        key_file = 'encryption.key'
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def encrypt(self, data: str) -> str:
        """Шифрование данных"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрование данных"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()


class UserConfigManager:
    """Менеджер пользовательских настроек"""
    
    def __init__(self):
        self.encryption = EncryptionManager()
        self.db_conn = self._get_db_connection()
        
    def _get_db_connection(self):
        """Подключение к базе данных"""
        return psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', 5432),
            database=os.getenv('POSTGRES_DB', 'testdb'),
            user=os.getenv('POSTGRES_USER', 'testuser'),
            password=os.getenv('POSTGRES_PASSWORD', 'testpass')
        )
    
    def create_user_with_defaults(self, username: str, email: str) -> int:
        """Создание пользователя с настройками по умолчанию"""
        with self.db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT create_user_with_defaults(%s, %s)",
                (username, email)
            )
            user_id = cursor.fetchone()[0]
            self.db_conn.commit()
            
        logger.info(f"Создан пользователь {username} с ID {user_id}")
        return user_id
    
    def get_user_config(self, user_id: int) -> Optional[UserConfig]:
        """Получение конфигурации пользователя"""
        with self.db_conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, email, settings FROM users WHERE id = %s",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return UserConfig(
                    user_id=row[0],
                    username=row[1],
                    email=row[2],
                    settings=row[3] or {}
                )
        return None
    
    def get_user_data_sources(self, user_id: int, source_type: Optional[str] = None) -> List[DataSourceConfig]:
        """Получение источников данных пользователя"""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT source_type, source_name, is_enabled_semantic_search, 
                       is_enabled_architecture_generation, connection_config,
                       last_sync_at, sync_status, sync_schedule, auto_sync_on_startup
                FROM user_data_sources 
                WHERE user_id = %s
            """
            params = [user_id]
            if source_type:
                query += " AND source_type = %s"
                params.append(source_type)

            cursor.execute(query, tuple(params))
            
            sources = []
            for row in cursor.fetchall():
                sources.append(DataSourceConfig(**row))
            
            return sources
    
    def update_data_source_config(self, user_id: int, source_type: str, source_name: str, 
                                  is_enabled_semantic_search: bool, 
                                  is_enabled_architecture_generation: bool,
                                  sync_schedule: Optional[str] = None):
        """Обновление настроек источника данных"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                UPDATE user_data_sources 
                SET is_enabled_semantic_search = %s,
                    is_enabled_architecture_generation = %s,
                    sync_schedule = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND source_type = %s AND source_name = %s
            """, (is_enabled_semantic_search, is_enabled_architecture_generation, 
                  sync_schedule, user_id, source_type, source_name))
            
            self.db_conn.commit()
            
        logger.info(f"Обновлены настройки {source_type}:{source_name} для пользователя {user_id}")
    
    def add_jira_config(self, user_id: int, config_name: str, jira_url: str, 
                       username: str, password: str, projects: List[str] = None):
        """Добавление конфигурации Jira (логин+пароль)"""
        encrypted_password = self.encryption.encrypt(password)
        
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_jira_configs 
                (user_id, config_name, jira_url, username, password_encrypted, projects)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, config_name) 
                DO UPDATE SET 
                    jira_url = EXCLUDED.jira_url,
                    username = EXCLUDED.username,
                    password_encrypted = EXCLUDED.password_encrypted,
                    projects = EXCLUDED.projects,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, config_name, jira_url, username, encrypted_password, 
                  json.dumps(projects or [])))
            
            self.db_conn.commit()
            
        logger.info(f"Добавлена конфигурация Jira '{config_name}' для пользователя {user_id}")
    
    def add_confluence_config(self, user_id: int, config_name: str, confluence_url: str, 
                             bearer_token: str, spaces: List[str] = None):
        """Добавление конфигурации Confluence DC ≥ 8.0 (Bearer-PAT)"""
        encrypted_token = self.encryption.encrypt(bearer_token)
        
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_confluence_configs 
                (user_id, config_name, confluence_url, bearer_token_encrypted, spaces)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, config_name) 
                DO UPDATE SET 
                    confluence_url = EXCLUDED.confluence_url,
                    bearer_token_encrypted = EXCLUDED.bearer_token_encrypted,
                    spaces = EXCLUDED.spaces,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, config_name, confluence_url, encrypted_token, 
                  json.dumps(spaces or [])))
            
            self.db_conn.commit()
            
        logger.info(f"Добавлена конфигурация Confluence '{config_name}' для пользователя {user_id}")
    
    def add_gitlab_config(self, user_id: int, alias: str, gitlab_url: str, 
                         access_token: str, projects: List[str] = None):
        """Добавление конфигурации GitLab (динамический список серверов)"""
        encrypted_token = self.encryption.encrypt(access_token)
        
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_gitlab_configs 
                (user_id, alias, gitlab_url, access_token_encrypted, projects)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, alias) 
                DO UPDATE SET 
                    gitlab_url = EXCLUDED.gitlab_url,
                    access_token_encrypted = EXCLUDED.access_token_encrypted,
                    projects = EXCLUDED.projects,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, alias, gitlab_url, encrypted_token, 
                  json.dumps(projects or [])))
            
            self.db_conn.commit()
            
        logger.info(f"Добавлена конфигурация GitLab '{alias}' для пользователя {user_id}")
    
    def get_jira_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение конфигураций Jira пользователя"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT config_name, jira_url, username, password_encrypted, 
                       is_default, projects
                FROM user_jira_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'config_name': row[0],
                    'jira_url': row[1],
                    'username': row[2],
                    'password': self.encryption.decrypt(row[3]),
                    'is_default': row[4],
                    'projects': row[5] or []
                })
            
            return configs
    
    def get_confluence_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение конфигураций Confluence пользователя"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT config_name, confluence_url, bearer_token_encrypted, 
                       is_default, spaces
                FROM user_confluence_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'config_name': row[0],
                    'confluence_url': row[1],
                    'bearer_token': self.encryption.decrypt(row[2]),
                    'is_default': row[3],
                    'spaces': row[4] or []
                })
            
            return configs
    
    def get_gitlab_configs(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение конфигураций GitLab пользователя"""
        with self.db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT alias, gitlab_url, access_token_encrypted, 
                       is_default, projects
                FROM user_gitlab_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'alias': row[0],
                    'gitlab_url': row[1],
                    'access_token': self.encryption.decrypt(row[2]),
                    'is_default': row[3],
                    'projects': row[4] or []
                })
            
            return configs

    def update_sync_status(self, user_id: int, source_type: str, source_name: str, 
                             status: str, error_message: Optional[str] = None):
        """Обновляет статус и время последней синхронизации."""
        with self.db_conn.cursor() as cursor:
            query = """
                UPDATE user_data_sources
                SET sync_status = %s, error_message = %s, last_sync_at = %s
                WHERE user_id = %s AND source_type = %s AND source_name = %s
            """
            
            last_sync_at = datetime.now() if status in ['success', 'error'] else None
            
            cursor.execute(query, (status, error_message, last_sync_at, user_id, source_type, source_name))
            self.db_conn.commit()
            
        logger.info(f"Обновлен статус синхронизации для {source_type}:{source_name} на {status}")

    def get_all_users(self) -> List[User]:
        """Возвращает всех активных пользователей."""
        with self.db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, username, email FROM users WHERE is_active = TRUE")
            users = [User(**row) for row in cursor.fetchall()]
            return users


class FileProcessor:
    """Обработчик пользовательских файлов"""
    
    def __init__(self, user_config_manager: UserConfigManager):
        self.config_manager = user_config_manager
        
    async def process_uploaded_file(self, user_id: int, file_path: str, 
                                   original_filename: str, tags: List[str] = None) -> int:
        """Обработка загруженного файла"""
        # Определение типа файла
        file_type = self._detect_file_type(file_path)
        file_size = os.path.getsize(file_path)
        
        # Извлечение текста
        content_text = await self._extract_text(file_path, file_type)
        
        # Сохранение в базу данных
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_files 
                (user_id, filename, original_filename, file_type, file_size, 
                 file_path, content_text, is_marked_as_user_content, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, os.path.basename(file_path), original_filename, 
                  file_type, file_size, file_path, content_text, True, 
                  json.dumps(tags or [])))
            
            file_id = cursor.fetchone()[0]
            
            # Обновляем статус обработки
            cursor.execute("""
                UPDATE user_files 
                SET is_processed = TRUE, processed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (file_id,))
            
            self.config_manager.db_conn.commit()
            
        logger.info(f"Обработан файл {original_filename} для пользователя {user_id}")
        return file_id
    
    def _detect_file_type(self, file_path: str) -> str:
        """Определение типа файла"""
        try:
            mime_type = magic.from_file(file_path, mime=True)
            
            if mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                               'application/msword']:
                return 'doc'
            elif mime_type == 'application/epub+zip':
                return 'epub'
            elif mime_type.startswith('text/'):
                return 'txt'
            else:
                return 'unknown'
        except:
            # Fallback по расширению
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf':
                return 'pdf'
            elif ext in ['.doc', '.docx']:
                return 'doc'
            elif ext == '.epub':
                return 'epub'
            elif ext in ['.txt', '.md']:
                return 'txt'
            else:
                return 'unknown'
    
    async def _extract_text(self, file_path: str, file_type: str) -> str:
        """Извлечение текста из файла"""
        try:
            if file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type == 'doc':
                return self._extract_from_doc(file_path)
            elif file_type == 'epub':
                return self._extract_from_epub(file_path)
            elif file_type == 'txt':
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            else:
                return ""
        except Exception as e:
            logger.error(f"Ошибка извлечения текста из {file_path}: {e}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Извлечение текста из PDF"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            logger.error(f"Ошибка извлечения из PDF {file_path}: {e}")
            return ""
    
    def _extract_from_doc(self, file_path: str) -> str:
        """Извлечение текста из Word документа"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Ошибка извлечения из DOC {file_path}: {e}")
            return ""
    
    def _extract_from_epub(self, file_path: str) -> str:
        """Извлечение текста из EPUB"""
        try:
            book = epub.read_epub(file_path)
            text = ""
            
            for item in book.get_items():
                if item.get_type() == 9:  # XHTML content
                    content = item.get_content().decode('utf-8')
                    # Простое удаление HTML тегов
                    import re
                    text += re.sub('<[^<]+?>', '', content) + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Ошибка извлечения из EPUB {file_path}: {e}")
            return ""


class SyncManager:
    """Менеджер синхронизации данных с параллельной загрузкой"""
    
    def __init__(self, user_config_manager: UserConfigManager):
        self.config_manager = user_config_manager
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def start_sync_task(self, user_id: int, sources: List[str], 
                             task_type: str = 'manual') -> int:
        """Запуск задачи синхронизации"""
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_tasks 
                (user_id, task_type, sources, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (user_id, task_type, json.dumps(sources), 'pending'))
            
            task_id = cursor.fetchone()[0]
            self.config_manager.db_conn.commit()
            
        logger.info(f"Создана задача синхронизации {task_id} для пользователя {user_id}")
        
        # Запускаем синхронизацию асинхронно
        asyncio.create_task(self._execute_sync_task(task_id))
        
        return task_id
    
    async def _execute_sync_task(self, task_id: int):
        """Выполнение задачи синхронизации с обработкой ошибок"""
        try:
            # Получаем информацию о задаче
            with self.config_manager.db_conn.cursor() as cursor:
                cursor.execute("""
                    SELECT user_id, sources FROM sync_tasks WHERE id = %s
                """, (task_id,))
                
                row = cursor.fetchone()
                if not row:
                    return
                    
                user_id, sources = row
                sources = sources if isinstance(sources, list) else json.loads(sources)
            
            # Обновляем статус
            await self._update_task_status(task_id, 'running')
            
            total_items = 0
            processed_items = 0
            error_count = 0
            
            # Параллельная обработка источников
            tasks = []
            for source in sources:
                task = self._sync_source(user_id, source, task_id)
                tasks.append(task)
            
            # Выполняем все задачи параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Ошибка синхронизации источника {sources[i]}: {result}")
                    error_count += 1
                    await self._log_sync_error(task_id, sources[i], str(result))
                else:
                    items_processed, items_total, errors = result
                    total_items += items_total
                    processed_items += items_processed
                    error_count += errors
                
                # Обновляем прогресс
                progress = int((processed_items / total_items * 100)) if total_items > 0 else 100
                await self._update_task_progress(task_id, progress, total_items, processed_items, error_count)
            
            # Завершаем задачу
            status = 'completed' if error_count == 0 else 'completed_with_errors'
            await self._update_task_status(task_id, status)
            
        except Exception as e:
            logger.error(f"Критическая ошибка в задаче синхронизации {task_id}: {e}")
            await self._update_task_status(task_id, 'failed')
    
    async def _sync_source(self, user_id: int, source: str, task_id: int) -> Tuple[int, int, int]:
        """Синхронизация конкретного источника с обработкой ошибок"""
        items_processed = 0
        items_total = 0
        errors = 0
        
        try:
            if source == 'jira':
                items_processed, items_total, errors = await self._sync_jira(user_id, task_id)
            elif source == 'confluence':
                items_processed, items_total, errors = await self._sync_confluence(user_id, task_id)
            elif source == 'gitlab':
                items_processed, items_total, errors = await self._sync_gitlab(user_id, task_id)
            else:
                await self._log_sync_error(task_id, source, f"Неизвестный источник: {source}")
                errors = 1
                
        except Exception as e:
            logger.error(f"Ошибка синхронизации {source}: {e}")
            await self._log_sync_error(task_id, source, str(e))
            errors = 1
            
        return items_processed, items_total, errors
    
    async def _sync_jira(self, user_id: int, task_id: int) -> Tuple[int, int, int]:
        """Синхронизация Jira с обработкой ошибок"""
        configs = self.config_manager.get_jira_configs(user_id)
        
        if not configs:
            await self._log_sync_error(task_id, 'jira', "Нет конфигураций Jira")
            return 0, 0, 1
        
        total_processed = 0
        total_items = 0
        total_errors = 0
        
        for config in configs:
            try:
                jira = Jira(
                    url=config['jira_url'],
                    username=config['username'],
                    password=config['password']
                )
                
                projects = config.get('projects', [])
                if not projects:
                    # Получаем все проекты если не указаны конкретные
                    all_projects = jira.projects()
                    projects = [p['key'] for p in all_projects[:5]]  # Ограничиваем для тестирования
                
                for project in projects:
                    try:
                        # Получаем задачи проекта
                        issues = jira.jql(f"project = {project}", maxResults=100)
                        
                        total_items += len(issues.get('issues', []))
                        
                        for issue in issues.get('issues', []):
                            try:
                                # Сохраняем в поисковый индекс
                                await self._save_to_search_index(
                                    user_id=user_id,
                                    source_type='jira',
                                    item_id=issue['key'],
                                    title=issue['fields']['summary'],
                                    content=issue['fields'].get('description', ''),
                                    metadata={
                                        'project': project,
                                        'issue_type': issue['fields']['issuetype']['name'],
                                        'status': issue['fields']['status']['name']
                                    }
                                )
                                
                                total_processed += 1
                                
                                await self._log_sync_info(
                                    task_id, 'jira', 
                                    f"Обработана задача {issue['key']}"
                                )
                                
                            except Exception as e:
                                logger.error(f"Ошибка обработки задачи {issue.get('key', 'unknown')}: {e}")
                                total_errors += 1
                                # Продолжаем обработку следующих задач
                                
                    except Exception as e:
                        logger.error(f"Ошибка получения задач проекта {project}: {e}")
                        total_errors += 1
                        # Продолжаем с следующего проекта
                        
            except Exception as e:
                logger.error(f"Ошибка подключения к Jira {config['config_name']}: {e}")
                total_errors += 1
                # Продолжаем с следующей конфигурацией
        
        return total_processed, total_items, total_errors
    
    async def _sync_confluence(self, user_id: int, task_id: int) -> Tuple[int, int, int]:
        """Синхронизация Confluence с обработкой ошибок"""
        configs = self.config_manager.get_confluence_configs(user_id)
        
        if not configs:
            await self._log_sync_error(task_id, 'confluence', "Нет конфигураций Confluence")
            return 0, 0, 1
        
        total_processed = 0
        total_items = 0
        total_errors = 0
        
        for config in configs:
            try:
                # Для Confluence DC ≥ 8.0 используем Bearer токен
                confluence = Confluence(
                    url=config['confluence_url'],
                    token=config['bearer_token']  # Bearer-PAT токен
                )
                
                spaces = config.get('spaces', [])
                if not spaces:
                    # Получаем все пространства если не указаны конкретные
                    all_spaces = confluence.get_all_spaces(limit=5)
                    spaces = [s['key'] for s in all_spaces.get('results', [])]
                
                for space in spaces:
                    try:
                        # Получаем страницы пространства
                        pages = confluence.get_all_pages_from_space(space, limit=50)
                        
                        total_items += len(pages)
                        
                        for page in pages:
                            try:
                                # Получаем содержимое страницы
                                page_content = confluence.get_page_by_id(
                                    page['id'], 
                                    expand='body.storage'
                                )
                                
                                await self._save_to_search_index(
                                    user_id=user_id,
                                    source_type='confluence',
                                    item_id=page['id'],
                                    title=page_content['title'],
                                    content=page_content['body']['storage']['value'],
                                    metadata={
                                        'space': space,
                                        'page_type': page.get('type', 'page'),
                                        'created': page_content.get('history', {}).get('createdDate', '')
                                    }
                                )
                                
                                total_processed += 1
                                
                                await self._log_sync_info(
                                    task_id, 'confluence', 
                                    f"Обработана страница {page_content['title']}"
                                )
                                
                            except Exception as e:
                                logger.error(f"Ошибка обработки страницы {page.get('id', 'unknown')}: {e}")
                                total_errors += 1
                                # Продолжаем с следующей страницей
                                
                    except Exception as e:
                        logger.error(f"Ошибка получения страниц пространства {space}: {e}")
                        total_errors += 1
                        # Продолжаем с следующего пространства
                        
            except Exception as e:
                logger.error(f"Ошибка подключения к Confluence {config['config_name']}: {e}")
                total_errors += 1
                # Продолжаем с следующей конфигурацией
        
        return total_processed, total_items, total_errors
    
    async def _sync_gitlab(self, user_id: int, task_id: int) -> Tuple[int, int, int]:
        """Синхронизация GitLab с обработкой ошибок"""
        configs = self.config_manager.get_gitlab_configs(user_id)
        
        if not configs:
            await self._log_sync_error(task_id, 'gitlab', "Нет конфигураций GitLab")
            return 0, 0, 1
        
        total_processed = 0
        total_items = 0
        total_errors = 0
        
        for config in configs:
            try:
                gitlab = Gitlab(
                    url=config['gitlab_url'],
                    private_token=config['access_token']
                )
                
                projects = config.get('projects', [])
                if not projects:
                    # Получаем проекты пользователя
                    all_projects = gitlab.projects.list(owned=True, limit=10)
                    projects = [p.path_with_namespace for p in all_projects]
                
                for project_path in projects:
                    try:
                        # Ищем проект
                        project = gitlab.projects.get(project_path)
                        total_items += 1
                        
                        # Получаем README и другие документы
                        try:
                            readme = project.files.get('README.md', 'main')
                            content = readme.decode().decode('utf-8')
                            
                            await self._save_to_search_index(
                                user_id=user_id,
                                source_type='gitlab',
                                item_id=f"{project.id}_readme",
                                title=f"{project.name} - README",
                                content=content,
                                metadata={
                                    'project': project.path_with_namespace,
                                    'file_type': 'readme',
                                    'branch': 'main'
                                }
                            )
                            
                            total_processed += 1
                            
                            await self._log_sync_info(
                                task_id, 'gitlab', 
                                f"Обработан README проекта {project.name}"
                            )
                            
                        except Exception:
                            # README может не существовать, продолжаем
                            pass
                            
                    except Exception as e:
                        logger.error(f"Ошибка обработки проекта {project_path}: {e}")
                        total_errors += 1
                        # Продолжаем с следующего проекта
                        
            except Exception as e:
                logger.error(f"Ошибка подключения к GitLab {config['alias']}: {e}")
                total_errors += 1
                # Продолжаем с следующей конфигурацией
        
        return total_processed, total_items, total_errors
    
    async def _save_to_search_index(self, user_id: int, source_type: str, item_id: str, 
                                   title: str, content: str, metadata: Dict[str, Any]):
        """Сохранение в поисковый индекс (заглушка)"""
        # Здесь должна быть реальная логика сохранения в Elasticsearch
        logger.info(f"Сохранен в индекс: {source_type}:{item_id} для пользователя {user_id}")
    
    async def _update_task_status(self, task_id: int, status: str):
        """Обновление статуса задачи"""
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sync_tasks 
                SET status = %s, 
                    started_at = CASE WHEN %s = 'running' THEN CURRENT_TIMESTAMP ELSE started_at END,
                    completed_at = CASE WHEN %s IN ('completed', 'failed', 'completed_with_errors') 
                                        THEN CURRENT_TIMESTAMP ELSE completed_at END
                WHERE id = %s
            """, (status, status, status, task_id))
            
            self.config_manager.db_conn.commit()
    
    async def _update_task_progress(self, task_id: int, progress: int, total: int, 
                                   processed: int, errors: int):
        """Обновление прогресса задачи"""
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                UPDATE sync_tasks 
                SET progress_percentage = %s, total_items = %s, 
                    processed_items = %s, error_count = %s
                WHERE id = %s
            """, (progress, total, processed, errors, task_id))
            
            self.config_manager.db_conn.commit()
    
    async def _log_sync_info(self, task_id: int, source_type: str, message: str):
        """Логирование информации синхронизации"""
        await self._log_sync_message(task_id, source_type, 'INFO', message)
    
    async def _log_sync_error(self, task_id: int, source_type: str, message: str):
        """Логирование ошибки синхронизации"""
        await self._log_sync_message(task_id, source_type, 'ERROR', message)
    
    async def _log_sync_message(self, task_id: int, source_type: str, level: str, message: str):
        """Логирование сообщения синхронизации"""
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sync_logs (task_id, source_type, source_name, log_level, message)
                VALUES (%s, %s, %s, %s, %s)
            """, (task_id, source_type, source_type, level, message))
            
            self.config_manager.db_conn.commit()
    
    def get_sync_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получение статуса синхронизации для GUI"""
        with self.config_manager.db_conn.cursor() as cursor:
            cursor.execute("""
                SELECT status, progress_percentage, total_items, processed_items, 
                       error_count, started_at, completed_at
                FROM sync_tasks 
                WHERE id = %s
            """, (task_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'status': row[0],
                    'progress_percentage': row[1],
                    'total_items': row[2],
                    'processed_items': row[3],
                    'error_count': row[4],
                    'started_at': row[5],
                    'completed_at': row[6]
                }
        return None
    
    def get_sync_logs(self, task_id: int, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получение логов синхронизации для GUI"""
        with self.config_manager.db_conn.cursor() as cursor:
            if level:
                cursor.execute("""
                    SELECT source_type, log_level, message, created_at
                    FROM sync_logs 
                    WHERE task_id = %s AND log_level = %s
                    ORDER BY created_at DESC
                """, (task_id, level))
            else:
                cursor.execute("""
                    SELECT source_type, log_level, message, created_at
                    FROM sync_logs 
                    WHERE task_id = %s
                    ORDER BY created_at DESC
                """, (task_id,))
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'source_type': row[0],
                    'log_level': row[1],
                    'message': row[2],
                    'created_at': row[3]
                })
            
            return logs


_user_config_manager: Optional[UserConfigManager] = None

def get_user_config_manager() -> UserConfigManager:
    global _user_config_manager
    if _user_config_manager is None:
        _user_config_manager = UserConfigManager()
    return _user_config_manager

if __name__ == "__main__":
    # Пример использования
    config_manager = get_user_config_manager()
    
    # Создание пользователя с настройками по умолчанию
    user_id = config_manager.create_user_with_defaults("test_user", "test@example.com")
    
    # Добавление конфигураций согласно требованиям
    
    # Jira (логин+пароль)
    config_manager.add_jira_config(
        user_id=user_id,
        config_name="main_jira",
        jira_url="https://company.atlassian.net",
        username="user@company.com",
        password="secure_password",
        projects=["PROJ1", "PROJ2"]
    )
    
    # Confluence DC ≥ 8.0 (Bearer-PAT)
    config_manager.add_confluence_config(
        user_id=user_id,
        config_name="main_confluence",
        confluence_url="https://company.atlassian.net/wiki",
        bearer_token="Bearer_PAT_token_here",
        spaces=["TECH", "ARCH"]
    )
    
    # GitLab-серверы (динамический список)
    config_manager.add_gitlab_config(
        user_id=user_id,
        alias="main",
        gitlab_url="https://gitlab.company.com",
        access_token="gitlab_access_token_here",
        projects=["group/project1", "group/project2"]
    )
    
    config_manager.add_gitlab_config(
        user_id=user_id,
        alias="open",
        gitlab_url="https://gitlab.com",
        access_token="gitlab_public_token_here",
        projects=["opensource/project1"]
    )
    
    print("Пользователь и конфигурации созданы успешно!") 