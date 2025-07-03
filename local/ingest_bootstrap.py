#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ingest_bootstrap.py

Модуль для обработки bootstrap материалов в Qdrant.

Функциональность:
- Обработка файлов из папки bootstrap
- Поддержка PDF, TXT, ZIP архивов
- Извлечение метаданных из .json файлов
- Интеграция с системой источников данных
"""

import os
import sys
import json
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator, Tuple
import hashlib
import uuid
import textwrap

# Добавляем путь к модулям проекта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from models.data_source import (
        SourceType, DataSourceManager, SourceMetadata, 
        create_source_metadata_from_file, get_data_source_manager
    )
except ImportError:
    # Fallback если модель недоступна
    print("Warning: data_source model not available, using fallback")
    SourceType = type('SourceType', (), {'BOOTSTRAP': 'bootstrap'})()

logger = logging.getLogger("ingest_bootstrap")

# Константы для векторизации
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")

def sha_str(s: str) -> str:
    """Создает SHA-1 хеш строки"""
    return hashlib.sha1(s.encode()).hexdigest()

def sha_uuid(s: str) -> str:
    """Создает UUID5 из строки"""
    return str(uuid.uuid5(NAMESPACE, s))

def wrap_text(text: str, chunk_size: int = 1500) -> List[str]:
    """Разбивает текст на чанки"""
    return textwrap.wrap(text, chunk_size, break_long_words=False, break_on_hyphens=False)


class BootstrapProcessor:
    """Обработчик bootstrap материалов"""
    
    def __init__(self, bootstrap_dir: str = "bootstrap"):
        self.bootstrap_dir = Path(bootstrap_dir)
        self.data_source_manager = get_data_source_manager() if 'get_data_source_manager' in globals() else None
        self.stats = {
            "files_processed": 0,
            "chunks_created": 0,
            "errors": 0,
            "categories": {}
        }
        
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Извлекает текст из PDF файла"""
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            logger.warning("PyPDF2 не установлен, пропускаем PDF файл")
            return f"PDF файл: {pdf_path.name}\nТребуется PyPDF2 для извлечения текста."
        except Exception as e:
            logger.error(f"Ошибка при обработке PDF {pdf_path}: {e}")
            return f"PDF файл: {pdf_path.name}\nОшибка при извлечении текста: {e}"
            
    def extract_text_from_zip(self, zip_path: Path) -> str:
        """Извлекает текст из ZIP архива (файлы README, markdown и т.д.)"""
        text_content = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Получаем список интересных файлов
                interesting_files = []
                for file_info in zip_file.infolist():
                    if not file_info.is_dir():
                        name = file_info.filename.lower()
                        if any(ext in name for ext in [
                            'readme', '.md', '.txt', '.rst', 
                            'doc', 'guide', 'tutorial'
                        ]):
                            interesting_files.append(file_info)
                
                # Ограничиваем количество файлов для обработки
                interesting_files = interesting_files[:20]
                
                for file_info in interesting_files:
                    try:
                        with zip_file.open(file_info) as file:
                            content = file.read()
                            # Пытаемся декодировать как UTF-8
                            try:
                                text = content.decode('utf-8')
                            except UnicodeDecodeError:
                                text = content.decode('latin-1', errors='ignore')
                                
                            text_content.append(f"\n--- {file_info.filename} ---\n")
                            text_content.append(text)
                            
                    except Exception as e:
                        logger.warning(f"Не удалось прочитать файл {file_info.filename} из архива: {e}")
                        
        except Exception as e:
            logger.error(f"Ошибка при обработке ZIP архива {zip_path}: {e}")
            return f"ZIP архив: {zip_path.name}\nОшибка при обработке: {e}"
            
        return "\n".join(text_content) if text_content else f"ZIP архив: {zip_path.name}\nНе найдено текстового содержимого"
        
    def extract_text_from_txt(self, txt_path: Path) -> str:
        """Читает содержимое текстового файла"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            try:
                with open(txt_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Ошибка при чтении текстового файла {txt_path}: {e}")
                return f"Текстовый файл: {txt_path.name}\nОшибка при чтении: {e}"
        except Exception as e:
            logger.error(f"Ошибка при чтении файла {txt_path}: {e}")
            return f"Файл: {txt_path.name}\nОшибка при чтении: {e}"
            
    def load_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Загружает метаданные из соответствующего .json файла"""
        metadata_path = file_path.with_suffix('.json')
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Не удалось загрузить метаданные из {metadata_path}: {e}")
        return None
        
    def process_file(self, file_path: Path) -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
        """Обрабатывает один файл и возвращает чанки для векторизации"""
        
        # Пропускаем файлы метаданных и служебные файлы
        if file_path.suffix == '.json' or file_path.name in ['download_stats.json', 'README.md', 'example_guide.txt']:
            return
            
        logger.info(f"Обрабатываем файл: {file_path}")
        
        # Загружаем метаданные
        metadata = self.load_metadata(file_path)
        
        # Извлекаем текст в зависимости от типа файла
        if file_path.suffix.lower() == '.pdf':
            text_content = self.extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() == '.zip':
            text_content = self.extract_text_from_zip(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md', '.rst']:
            text_content = self.extract_text_from_txt(file_path)
        else:
            logger.warning(f"Неподдерживаемый тип файла: {file_path}")
            return
            
        if not text_content or len(text_content.strip()) < 10:
            logger.warning(f"Слишком мало текста в файле {file_path}")
            return
            
        # Создаем базовые метаданные для payload
        base_payload = {
            "src": "bootstrap",
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "category": "general"
        }
        
        # Добавляем метаданные из .json файла если есть
        if metadata:
            base_payload.update({
                "name": metadata.get('name', file_path.stem),
                "category": metadata.get('category', 'general'),
                "role": metadata.get('role'),
                "original_url": metadata.get('url'),
                "url_type": metadata.get('url_type'),
                "downloaded_at": metadata.get('downloaded_at')
            })
            
        # Обновляем статистику по категориям
        category = base_payload.get('category', 'general')
        if category not in self.stats["categories"]:
            self.stats["categories"][category] = 0
        self.stats["categories"][category] += 1
        
        # Разбиваем текст на чанки
        chunks = wrap_text(text_content)
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:  # Пропускаем слишком короткие чанки
                continue
                
            # Создаем уникальный ID для чанка
            chunk_id = f"{file_path.stem}_{i}"
            sha_hex = sha_str(f"bootstrap:{chunk_id}:{chunk[:50]}")
            uid = sha_uuid(sha_hex)
            
            # Создаем payload для чанка
            chunk_payload = base_payload.copy()
            chunk_payload.update({
                "chunk_id": chunk_id,
                "chunk_index": i,
                "text": chunk,
                "url": f"bootstrap://{file_path.name}#{chunk_id}"
            })
            
            yield uid, chunk, chunk_payload
            
        self.stats["files_processed"] += 1
        logger.info(f"Обработан файл {file_path}: {len(chunks)} чанков")
        
    def process_directory(self, category_dir: Path) -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
        """Обрабатывает все файлы в директории категории РЕКУРСИВНО"""
        if not category_dir.exists() or not category_dir.is_dir():
            return
            
        logger.info(f"Обрабатываем категорию: {category_dir.name}")
        
        # Рекурсивно обрабатываем все файлы в директории и поддиректориях
        for file_path in category_dir.rglob("*"):
            if file_path.is_file():
                try:
                    yield from self.process_file(file_path)
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {file_path}: {e}")
                    self.stats["errors"] += 1
                    
    def ingest_all_bootstrap(self) -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
        """Обрабатывает все bootstrap материалы РЕКУРСИВНО"""
        logger.info(f"Начинаем РЕКУРСИВНУЮ обработку bootstrap материалов из {self.bootstrap_dir}")
        
        if not self.bootstrap_dir.exists():
            logger.warning(f"Директория bootstrap не существует: {self.bootstrap_dir}")
            return
            
        # Рекурсивно обрабатываем ВСЕ файлы в bootstrap директории и всех поддиректориях
        for file_path in self.bootstrap_dir.rglob("*"):
            if file_path.is_file():
                try:
                    yield from self.process_file(file_path)
                except Exception as e:
                    logger.error(f"Ошибка при обработке файла {file_path}: {e}")
                    self.stats["errors"] += 1
                    
        logger.info("Завершена РЕКУРСИВНАЯ обработка bootstrap материалов")
        self.print_stats()
        
    def print_stats(self):
        """Выводит статистику обработки"""
        logger.info("═══ СТАТИСТИКА ОБРАБОТКИ BOOTSTRAP ═══")
        logger.info(f"Файлов обработано: {self.stats['files_processed']}")
        logger.info(f"Чанков создано: {self.stats['chunks_created']}")
        logger.info(f"Ошибок: {self.stats['errors']}")
        logger.info("Категории:")
        for category, count in self.stats["categories"].items():
            logger.info(f"  {category}: {count} файлов")
        logger.info("═══════════════════════════════════════")


def ingest_bootstrap_materials(bootstrap_dir: str = "bootstrap") -> Generator[Tuple[str, str, Dict[str, Any]], None, None]:
    """
    Основная функция для интеграции с ingest_data.py
    
    Возвращает генератор кортежей (uid, text, payload) для векторизации
    """
    processor = BootstrapProcessor(bootstrap_dir)
    
    for uid, text, payload in processor.ingest_all_bootstrap():
        processor.stats["chunks_created"] += 1
        yield uid, text, payload


# Пример использования в ingest_data.py:
def test_bootstrap_ingestion():
    """Тестовая функция для проверки обработки bootstrap материалов"""
    logger.info("🧪 Тестирование обработки bootstrap материалов...")
    
    count = 0
    for uid, text, payload in ingest_bootstrap_materials():
        count += 1
        if count <= 3:  # Показываем первые 3 чанка
            logger.info(f"UID: {uid}")
            logger.info(f"Категория: {payload.get('category')}")
            logger.info(f"Файл: {payload.get('file_name')}")
            logger.info(f"Текст (первые 100 символов): {text[:100]}...")
            logger.info("---")
            
    logger.info(f"Всего обработано чанков: {count}")


if __name__ == "__main__":
    # Настройка логирования для тестирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    test_bootstrap_ingestion() 