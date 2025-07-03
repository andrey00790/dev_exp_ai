#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap_fetcher.py

Автоматизированная система загрузки обучающих материалов из разных источников.

Функциональность:
- Читает resource_config.yml
- Скачивает материалы из GitHub, PDF, веб-ресурсов
- Разархивирует zip файлы и сохраняет содержимое в local/bootstrap
- Поддерживает метаданные источников
- Интегрируется с ingestion pipeline
"""

import os
import sys
import yaml
import json
import requests
import hashlib
import logging
import argparse
import tempfile
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("bootstrap_fetcher")

class BootstrapFetcher:
    """Класс для загрузки обучающих материалов из resource_config.yml"""
    
    def __init__(self, config_path: str = "resource_config.yml", output_dir: str = "bootstrap"):
        self.config_path = Path(config_path)
        self.output_dir = Path(output_dir)
        self.session = self._create_session()
        self.stats = {
            "total": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "sources": {}
        }
        
    def _create_session(self) -> requests.Session:
        """Создает HTTP сессию с настройками retry и user-agent"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'AI-Assistant-Bootstrap-Fetcher/1.0 (Educational Material Downloader)'
        })
        return session
        
    def load_config(self) -> List[Dict[str, Any]]:
        """Загружает конфигурацию ресурсов из YAML файла"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Исправляем некорректные символы в YAML
                content = self._fix_yaml_syntax(content)
                config = yaml.safe_load(content)
                
            resources = config.get('resources', [])
            logger.info(f"Загружена конфигурация: {len(resources)} ресурсов")
            return resources
            
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации из {self.config_path}: {e}")
            return []
            
    def _fix_yaml_syntax(self, content: str) -> str:
        """Исправляет некорректные символы в YAML файле"""
        # Удаляем проблемные строки с символами ^[ и attribution
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Пропускаем строки с некорректными символами
            if '^[' in line or 'attribution' in line or ']({"' in line:
                continue
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)
        
    def categorize_url(self, url: str) -> Dict[str, str]:
        """Определяет тип URL и стратегию загрузки"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()
        
        if 'github.com' in domain:
            if '/blob/' in path or '/raw/' in path:
                return {"type": "github_file", "strategy": "direct"}
            else:
                return {"type": "github_repo", "strategy": "clone_or_archive"}
                
        elif path.endswith('.pdf'):
            return {"type": "pdf", "strategy": "direct"}
            
        elif any(ext in path for ext in ['.md', '.txt', '.py', '.js', '.go', '.rs']):
            return {"type": "text_file", "strategy": "direct"}
            
        elif 'harvard.edu' in domain or 'edx.org' in domain:
            return {"type": "educational", "strategy": "webpage"}
            
        else:
            return {"type": "webpage", "strategy": "webpage"}
            
    def generate_filename(self, resource: Dict[str, Any], url_info: Dict[str, str]) -> str:
        """Генерирует имя файла для сохранения ресурса"""
        name = resource.get('name', 'unknown')
        category = resource.get('category', 'general')
        url_type = url_info.get('type', 'file')
        
        # Очищаем имя от недопустимых символов
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Определяем расширение
        if url_type == 'pdf':
            ext = '.pdf'
        elif url_type == 'github_repo':
            # Для GitHub репозиториев мы создаем папку, а не файл
            return safe_name
        elif url_type in ['text_file', 'webpage']:
            ext = '.txt'
        else:
            ext = '.txt'
            
        return f"{category}_{safe_name}{ext}"

    def extract_archive(self, archive_path: Path, extract_to: Path) -> bool:
        """Разархивирует архив в указанную папку"""
        try:
            extract_to.mkdir(parents=True, exist_ok=True)
            
            if archive_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # Извлекаем все файлы
                    zip_ref.extractall(extract_to)
                    
                    # Получаем список извлеченных файлов
                    extracted_files = []
                    for root, dirs, files in os.walk(extract_to):
                        for file in files:
                            extracted_files.append(os.path.join(root, file))
                    
                    logger.info(f"Разархивировано {len(extracted_files)} файлов в {extract_to}")
                    return True
            else:
                logger.warning(f"Неподдерживаемый формат архива: {archive_path.suffix}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при разархивировании {archive_path}: {e}")
            return False
        
    def download_github_repo(self, url: str, output_path: Path) -> bool:
        """Скачивает GitHub репозиторий и разархивирует его содержимое"""
        try:
            # Преобразуем URL в ссылку на архив
            if url.endswith('.git'):
                url = url[:-4]
            
            # Извлекаем owner/repo из URL
            parts = url.replace('https://github.com/', '').split('/')
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
                
                # Пробуем main, если не получится - попробуем master
                response = self.session.get(archive_url, timeout=30)
                if response.status_code != 200:
                    archive_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
                    response = self.session.get(archive_url, timeout=30)
                
                if response.status_code == 200:
                    # Создаем временный файл для zip архива
                    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                        tmp_file.write(response.content)
                        tmp_path = Path(tmp_file.name)
                    
                    try:
                        # Разархивируем во временную папку
                        with tempfile.TemporaryDirectory() as tmp_dir:
                            tmp_extract_path = Path(tmp_dir)
                            
                            if self.extract_archive(tmp_path, tmp_extract_path):
                                # Находим корневую папку репозитория (обычно имеет название вида repo-main или repo-master)
                                repo_folders = [d for d in tmp_extract_path.iterdir() if d.is_dir()]
                                
                                if repo_folders:
                                    # Берем первую папку (обычно единственная)
                                    source_folder = repo_folders[0]
                                    
                                    # Создаем целевую папку
                                    output_path.mkdir(parents=True, exist_ok=True)
                                    
                                    # Копируем содержимое
                                    for item in source_folder.iterdir():
                                        dest_item = output_path / item.name
                                        if item.is_dir():
                                            shutil.copytree(item, dest_item, dirs_exist_ok=True)
                                        else:
                                            shutil.copy2(item, dest_item)
                                    
                                    logger.info(f"Разархивирован GitHub репозиторий: {url} -> {output_path}")
                                    return True
                                else:
                                    logger.warning(f"Не найдено содержимое в архиве {url}")
                            else:
                                logger.error(f"Ошибка разархивирования {url}")
                                
                    finally:
                        # Удаляем временный zip файл
                        tmp_path.unlink(missing_ok=True)
                        
                else:
                    logger.warning(f"Не удалось скачать репозиторий {url}: HTTP {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Ошибка при скачивании GitHub репозитория {url}: {e}")
            
        return False
        
    def download_direct_file(self, url: str, output_path: Path) -> bool:
        """Скачивает файл напрямую и разархивирует если это архив"""
        try:
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Определяем, является ли файл архивом по URL или Content-Type
            is_archive = (
                url.lower().endswith('.zip') or 
                'zip' in response.headers.get('content-type', '').lower() or
                'application/zip' in response.headers.get('content-type', '').lower()
            )
            
            if is_archive:
                # Скачиваем архив во временный файл
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                    tmp_path = Path(tmp_file.name)
                
                try:
                    # Для архивов создаем папку и разархивируем в неё
                    if output_path.suffix:
                        # Убираем расширение и делаем папкой
                        output_path = output_path.with_suffix('')
                    
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    success = self.extract_archive(tmp_path, output_path)
                    if success:
                        logger.info(f"Скачан и разархивирован файл: {url} -> {output_path}")
                    else:
                        logger.error(f"Ошибка разархивирования файла: {url}")
                    return success
                    
                finally:
                    # Удаляем временный файл
                    tmp_path.unlink(missing_ok=True)
            else:
                # Обычный файл, сохраняем как есть
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                logger.info(f"Скачан файл: {url}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка при скачивании файла {url}: {e}")
            return False
            
    def download_webpage(self, url: str, output_path: Path) -> bool:
        """Скачивает веб-страницу как текст"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Сохраняем как текст с метаданными
            content = f"# {url}\n"
            content += f"# Downloaded: {datetime.now().isoformat()}\n"
            content += f"# Content-Type: {response.headers.get('content-type', 'unknown')}\n\n"
            
            if 'text/' in response.headers.get('content-type', ''):
                content += response.text
            else:
                content += f"Binary content ({len(response.content)} bytes)\n"
                content += f"Note: This was a binary file, only metadata saved.\n"
                
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Скачана веб-страница: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании веб-страницы {url}: {e}")
            return False
            
    def download_resource(self, resource: Dict[str, Any]) -> bool:
        """Скачивает один ресурс"""
        url = resource.get('url')
        if not url:
            logger.warning(f"Отсутствует URL для ресурса: {resource.get('name')}")
            return False
            
        # Определяем тип ресурса и стратегию загрузки
        url_info = self.categorize_url(url)
        filename = self.generate_filename(resource, url_info)
        
        # Создаем папку по категории
        category = resource.get('category', 'general')
        category_dir = self.output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = category_dir / filename
        
        # Проверяем, не существует ли уже файл
        if output_path.exists():
            logger.info(f"Файл уже существует, пропускаем: {output_path}")
            self.stats["skipped"] += 1
            return True
            
        # Выбираем стратегию загрузки
        strategy = url_info.get('strategy')
        success = False
        
        if strategy == 'clone_or_archive':
            success = self.download_github_repo(url, output_path)
        elif strategy == 'direct':
            success = self.download_direct_file(url, output_path)
        elif strategy == 'webpage':
            success = self.download_webpage(url, output_path)
        else:
            logger.warning(f"Неизвестная стратегия загрузки: {strategy}")
            
        if success:
            # Сохраняем метаданные
            self.save_metadata(resource, output_path, url_info)
            self.stats["downloaded"] += 1
        else:
            self.stats["failed"] += 1
            
        return success
        
    def save_metadata(self, resource: Dict[str, Any], file_path: Path, url_info: Dict[str, str]):
        """Сохраняет метаданные ресурса"""
        metadata = {
            "name": resource.get('name'),
            "role": resource.get('role'),
            "category": resource.get('category'),
            "url": resource.get('url'),
            "downloaded_at": datetime.now().isoformat(),
            "file_path": str(file_path),
            "url_type": url_info.get('type'),
            "strategy": url_info.get('strategy'),
            "file_size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        metadata_path = file_path.with_suffix('.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
    def update_source_stats(self, category: str):
        """Обновляет статистику по источникам"""
        if category not in self.stats["sources"]:
            self.stats["sources"][category] = {"count": 0, "downloaded": 0}
        self.stats["sources"][category]["count"] += 1
        
    def fetch_all(self, max_resources: Optional[int] = None) -> Dict[str, Any]:
        """Загружает все ресурсы из конфигурации"""
        logger.info("🚀 Начинаем загрузку обучающих материалов...")
        
        # Создаем выходную директорию
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем конфигурацию
        resources = self.load_config()
        if not resources:
            logger.error("Нет ресурсов для загрузки")
            return self.stats
            
        # Ограничиваем количество ресурсов если задано
        if max_resources:
            resources = resources[:max_resources]
            
        self.stats["total"] = len(resources)
        logger.info(f"📊 Всего ресурсов для загрузки: {len(resources)}")
        
        # Загружаем ресурсы
        for i, resource in enumerate(resources, 1):
            name = resource.get('name', 'Unknown')
            category = resource.get('category', 'general')
            
            logger.info(f"📥 [{i}/{len(resources)}] Загружаем: {name} ({category})")
            self.update_source_stats(category)
            
            try:
                success = self.download_resource(resource)
                if success:
                    self.stats["sources"][category]["downloaded"] += 1
                    
            except Exception as e:
                logger.error(f"Критическая ошибка при загрузке {name}: {e}")
                self.stats["failed"] += 1
                
            # Небольшая пауза между загрузками
            time.sleep(0.5)
            
        # Сохраняем общую статистику
        self.save_final_stats()
        
        logger.info("✅ Загрузка завершена!")
        self.print_stats()
        
        return self.stats
        
    def save_final_stats(self):
        """Сохраняет финальную статистику"""
        stats_path = self.output_dir / "download_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
            
    def print_stats(self):
        """Выводит статистику загрузки"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ЗАГРУЗКИ МАТЕРИАЛОВ")
        print("="*60)
        print(f"Всего ресурсов: {self.stats['total']}")
        print(f"Загружено: {self.stats['downloaded']}")
        print(f"Пропущено (уже существуют): {self.stats['skipped']}")
        print(f"Ошибки: {self.stats['failed']}")
        print(f"Успешность: {(self.stats['downloaded'] + self.stats['skipped']) / self.stats['total'] * 100:.1f}%")
        
        print("\n📁 ПО КАТЕГОРИЯМ:")
        for category, stats in self.stats["sources"].items():
            print(f"  {category}: {stats['downloaded']}/{stats['count']}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Bootstrap материалов для AI Assistant")
    parser.add_argument(
        "--config", 
        default="resource_config.yml",
        help="Путь к файлу конфигурации (по умолчанию: resource_config.yml)"
    )
    parser.add_argument(
        "--output", 
        default="bootstrap",
        help="Папка для сохранения материалов (по умолчанию: bootstrap)"
    )
    parser.add_argument(
        "--max-resources", 
        type=int,
        help="Максимальное количество ресурсов для загрузки (для тестирования)"
    )
    parser.add_argument(
        "--category", 
        help="Загружать только ресурсы определенной категории"
    )
    
    args = parser.parse_args()
    
    try:
        fetcher = BootstrapFetcher(
            config_path=args.config,
            output_dir=args.output
        )
        
        stats = fetcher.fetch_all(max_resources=args.max_resources)
        
        # Возвращаем код выхода на основе результатов
        if stats["failed"] == 0:
            sys.exit(0)
        elif stats["downloaded"] > 0:
            sys.exit(1)  # Частичный успех
        else:
            sys.exit(2)  # Полная неудача
            
    except KeyboardInterrupt:
        logger.info("❌ Загрузка прервана пользователем")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 