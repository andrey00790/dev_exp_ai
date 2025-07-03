"""
Content Processor for Data Ingestion
Обработка и подготовка контента для векторизации
"""

import asyncio
import re
from typing import Dict, List, Any, Optional
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()


@dataclass
class ProcessedChunk:
    """Обработанный чанк текста"""
    text: str
    chunk_index: int
    source_doc_id: str
    metadata: Dict[str, Any]


class ContentProcessor:
    """Процессор контента"""
    
    def __init__(self, text_config: Dict[str, Any], embeddings_config: Dict[str, Any]):
        self.text_config = text_config
        self.embeddings_config = embeddings_config
        
        # Настройки чанкинга
        self.chunk_size = text_config.get("chunk_size", 1000)
        self.chunk_overlap = text_config.get("chunk_overlap", 200)
        self.min_chunk_size = text_config.get("min_chunk_size", 100)
        self.max_chunk_size = text_config.get("max_chunk_size", 4000)
        self.language = text_config.get("language", "ru")
        
        # Настройки эмбеддингов
        self.embedding_provider = embeddings_config.get("provider", "openai")
        self.embedding_model = embeddings_config.get("model", "text-embedding-ada-002")
        self.batch_size = embeddings_config.get("batch_size", 100)
    
    async def initialize(self):
        """Инициализация процессора"""
        try:
            # Инициализация NLP компонентов если нужно
            logger.info("Content processor initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize content processor", error=str(e))
            raise
    
    async def process_batch(self, documents: List[Any], source_type: str) -> List[Any]:
        """Обработка батча документов"""
        processed_docs = []
        
        try:
            for doc in documents:
                try:
                    # Очистка и нормализация контента
                    cleaned_content = await self._clean_content(doc.content)
                    
                    if len(cleaned_content.strip()) < self.min_chunk_size:
                        logger.warning(
                            "Document content too short after cleaning",
                            doc_id=doc.id,
                            length=len(cleaned_content)
                        )
                        continue
                    
                    # Создание обработанного документа
                    processed_doc = await self._create_processed_document(
                        doc, cleaned_content, source_type
                    )
                    
                    if processed_doc:
                        processed_docs.append(processed_doc)
                
                except Exception as e:
                    logger.error(
                        "Failed to process document",
                        doc_id=getattr(doc, 'id', 'unknown'),
                        error=str(e)
                    )
            
            logger.info(
                "Processed document batch",
                source_type=source_type,
                input_count=len(documents),
                output_count=len(processed_docs)
            )
            
            return processed_docs
            
        except Exception as e:
            logger.error("Failed to process document batch", error=str(e))
            raise
    
    async def _clean_content(self, content: str) -> str:
        """Очистка и нормализация контента"""
        try:
            # Удаление HTML тегов
            content = re.sub(r'<[^>]+>', '', content)
            
            # Удаление лишних пробелов и переносов
            content = re.sub(r'\s+', ' ', content)
            
            # Удаление специальных символов
            content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]', ' ', content)
            
            # Нормализация переносов строк
            content = re.sub(r'\n\s*\n', '\n\n', content)
            
            # Удаление ведущих и завершающих пробелов
            content = content.strip()
            
            # Ограничение максимальной длины
            if len(content) > self.max_chunk_size * 10:  # Максимум 10 чанков
                content = content[:self.max_chunk_size * 10]
                logger.warning("Content truncated due to excessive length")
            
            return content
            
        except Exception as e:
            logger.error("Failed to clean content", error=str(e))
            return content
    
    async def _create_processed_document(self, original_doc: Any, cleaned_content: str, source_type: str) -> Any:
        """Создание обработанного документа"""
        try:
            # Создаем копию оригинального документа с очищенным контентом
            processed_doc = self._copy_document(original_doc)
            processed_doc.content = cleaned_content
            
            # Добавляем метаданные обработки
            if hasattr(processed_doc, 'metadata'):
                if not isinstance(processed_doc.metadata, dict):
                    processed_doc.metadata = {}
            else:
                processed_doc.metadata = {}
            
            processed_doc.metadata.update({
                "processed": True,
                "original_length": len(original_doc.content),
                "processed_length": len(cleaned_content),
                "source_type": source_type,
                "chunk_size": self.chunk_size,
                "language": self.language
            })
            
            return processed_doc
            
        except Exception as e:
            logger.error("Failed to create processed document", error=str(e))
            return None
    
    def _copy_document(self, doc: Any) -> Any:
        """Создание копии документа"""
        import copy
        
        try:
            # Создаем shallow copy для избежания проблем с deep copy сложных объектов
            doc_copy = copy.copy(doc)
            
            # Копируем изменяемые атрибуты
            if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                doc_copy.metadata = doc.metadata.copy()
            if hasattr(doc, 'labels') and isinstance(doc.labels, list):
                doc_copy.labels = doc.labels.copy()
            
            return doc_copy
            
        except Exception as e:
            logger.error("Failed to copy document", error=str(e))
            return doc
    
    async def split_into_chunks(self, content: str, doc_id: str) -> List[ProcessedChunk]:
        """Разбиение контента на чанки"""
        chunks = []
        
        try:
            # Простое разбиение по размеру с перекрытием
            start = 0
            chunk_index = 0
            
            while start < len(content):
                # Определяем конец чанка
                end = start + self.chunk_size
                
                if end >= len(content):
                    # Последний чанк
                    chunk_text = content[start:].strip()
                else:
                    # Ищем хорошее место для разрыва (конец предложения)
                    chunk_text = content[start:end]
                    
                    # Попытка найти конец предложения в последних 100 символах
                    last_part = chunk_text[-100:]
                    sentence_ends = ['.', '!', '?', '\n\n']
                    
                    best_break = -1
                    for end_char in sentence_ends:
                        pos = last_part.rfind(end_char)
                        if pos > best_break:
                            best_break = pos
                    
                    if best_break > 0:
                        # Найден хороший разрыв
                        chunk_text = chunk_text[:len(chunk_text) - 100 + best_break + 1]
                    
                    chunk_text = chunk_text.strip()
                
                # Проверка минимального размера чанка
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(ProcessedChunk(
                        text=chunk_text,
                        chunk_index=chunk_index,
                        source_doc_id=doc_id,
                        metadata={
                            "start_pos": start,
                            "end_pos": start + len(chunk_text),
                            "chunk_length": len(chunk_text)
                        }
                    ))
                    chunk_index += 1
                
                # Переход к следующему чанку с перекрытием
                if end >= len(content):
                    break
                
                start = end - self.chunk_overlap
                
                # Защита от бесконечного цикла
                if start <= 0:
                    start = end
            
            logger.info(
                "Split content into chunks",
                doc_id=doc_id,
                content_length=len(content),
                chunks_count=len(chunks)
            )
            
            return chunks
            
        except Exception as e:
            logger.error("Failed to split content into chunks", doc_id=doc_id, error=str(e))
            return []
    
    async def extract_keywords(self, content: str) -> List[str]:
        """Извлечение ключевых слов из контента"""
        try:
            # Простое извлечение ключевых слов на основе частоты
            words = re.findall(r'\b[а-яё]{3,}\b', content.lower())
            
            # Подсчет частоты
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Сортировка по частоте и выбор топ-10
            keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return [word for word, freq in keywords if freq > 1]
            
        except Exception as e:
            logger.error("Failed to extract keywords", error=str(e))
            return []
    
    async def detect_language(self, content: str) -> str:
        """Определение языка контента"""
        try:
            # Простое определение языка по характерным символам
            russian_chars = len(re.findall(r'[а-яё]', content.lower()))
            english_chars = len(re.findall(r'[a-z]', content.lower()))
            
            if russian_chars > english_chars:
                return "ru"
            elif english_chars > 0:
                return "en"
            else:
                return "unknown"
                
        except Exception as e:
            logger.error("Failed to detect language", error=str(e))
            return "unknown"
    
    async def calculate_content_quality_score(self, content: str) -> float:
        """Расчет оценки качества контента"""
        try:
            score = 1.0
            
            # Длина контента
            if len(content) < 100:
                score *= 0.5
            elif len(content) > 10000:
                score *= 0.8
            
            # Соотношение букв к другим символам
            letters = len(re.findall(r'[a-zA-Zа-яёА-ЯЁ]', content))
            total_chars = len(content)
            if total_chars > 0:
                letter_ratio = letters / total_chars
                if letter_ratio < 0.5:
                    score *= 0.7
            
            # Наличие структуры (заголовки, списки)
            if re.search(r'\n\s*[-\*\+]\s+', content):  # Списки
                score *= 1.1
            if re.search(r'\n#+\s+', content):  # Markdown заголовки
                score *= 1.1
            
            # Ограничение диапазона
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error("Failed to calculate content quality score", error=str(e))
            return 0.5
    
    async def close(self):
        """Закрытие ресурсов"""
        logger.info("Content processor closed") 