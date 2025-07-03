"""
Database Manager for Data Ingestion
Управление сохранением данных в PostgreSQL
"""

import asyncio
import asyncpg
from typing import Dict, List, Any, Optional
import structlog
from datetime import datetime
import json

logger = structlog.get_logger()


class DatabaseManager:
    """Менеджер базы данных для ingestion"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        self.db_url = config["url"]
    
    async def initialize(self):
        """Инициализация пула соединений"""
        try:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,
                max_size=self.config.get("pool_size", 20),
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
            
            # Создание таблиц если не существуют
            await self._create_tables()
            
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database manager", error=str(e))
            raise
    
    async def _create_tables(self):
        """Создание необходимых таблиц"""
        create_documents_table = """
        CREATE TABLE IF NOT EXISTS ingested_documents (
            id VARCHAR(255) PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            source_name VARCHAR(255),
            source_url TEXT,
            file_path TEXT,
            metadata JSONB,
            content_hash VARCHAR(64),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        create_ingestion_stats_table = """
        CREATE TABLE IF NOT EXISTS ingestion_stats (
            id SERIAL PRIMARY KEY,
            source_type VARCHAR(50) NOT NULL,
            source_name VARCHAR(255),
            documents_processed INTEGER DEFAULT 0,
            documents_skipped INTEGER DEFAULT 0,
            documents_failed INTEGER DEFAULT 0,
            total_size_bytes BIGINT DEFAULT 0,
            processing_time_seconds REAL DEFAULT 0,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            status VARCHAR(20) DEFAULT 'running',
            error_message TEXT
        );
        """
        
        create_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_source_type ON ingested_documents(source_type);",
            "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON ingested_documents(created_at);",
            "CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON ingested_documents(content_hash);",
            "CREATE INDEX IF NOT EXISTS idx_ingestion_stats_source ON ingestion_stats(source_type, source_name);"
        ]
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_documents_table)
            await conn.execute(create_ingestion_stats_table)
            
            for index_sql in create_indexes:
                await conn.execute(index_sql)
        
        logger.info("Database tables created/verified")
    
    async def save_documents(self, documents: List[Any]) -> int:
        """Сохранение документов в базу данных"""
        if not documents:
            return 0
        
        saved_count = 0
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for doc in documents:
                        try:
                            # Подготовка данных
                            doc_data = self._prepare_document_data(doc)
                            
                            # Проверка существования документа по хешу
                            existing = await conn.fetchval(
                                "SELECT id FROM ingested_documents WHERE content_hash = $1",
                                doc_data["content_hash"]
                            )
                            
                            if existing:
                                logger.debug("Document already exists, skipping", doc_id=doc_data["id"])
                                continue
                            
                            # Вставка документа
                            await conn.execute("""
                                INSERT INTO ingested_documents 
                                (id, title, content, source_type, source_name, source_url, 
                                 file_path, metadata, content_hash, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                ON CONFLICT (id) DO UPDATE SET
                                    title = EXCLUDED.title,
                                    content = EXCLUDED.content,
                                    metadata = EXCLUDED.metadata,
                                    updated_at = EXCLUDED.updated_at
                            """,
                                doc_data["id"],
                                doc_data["title"],
                                doc_data["content"],
                                doc_data["source_type"],
                                doc_data["source_name"],
                                doc_data["source_url"],
                                doc_data["file_path"],
                                json.dumps(doc_data["metadata"]),
                                doc_data["content_hash"],
                                doc_data["created_at"],
                                doc_data["updated_at"]
                            )
                            
                            saved_count += 1
                            
                        except Exception as e:
                            logger.error(
                                "Failed to save document",
                                doc_id=getattr(doc, 'id', 'unknown'),
                                error=str(e)
                            )
            
            logger.info("Documents saved to database", saved_count=saved_count, total=len(documents))
            return saved_count
            
        except Exception as e:
            logger.error("Failed to save documents batch", error=str(e))
            raise
    
    def _prepare_document_data(self, doc: Any) -> Dict[str, Any]:
        """Подготовка данных документа для сохранения"""
        import hashlib
        
        # Создание хеша содержимого
        content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
        
        # Подготовка метаданных
        metadata = {}
        
        # Обработка разных типов документов
        if hasattr(doc, '__class__') and 'Confluence' in doc.__class__.__name__:
            metadata = {
                "space_key": getattr(doc, 'space_key', ''),
                "page_type": getattr(doc, 'page_type', ''),
                "author": getattr(doc, 'author', ''),
                "labels": getattr(doc, 'labels', []),
                "parent_id": getattr(doc, 'parent_id', None)
            }
            source_type = "confluence"
            source_name = getattr(doc, 'space_key', 'unknown')
            source_url = getattr(doc, 'url', '')
            file_path = None
            
        elif hasattr(doc, '__class__') and 'GitLab' in doc.__class__.__name__:
            metadata = {
                "project_name": getattr(doc, 'project_name', ''),
                "project_id": getattr(doc, 'project_id', ''),
                "branch": getattr(doc, 'branch', ''),
                "file_extension": getattr(doc, 'file_extension', ''),
                "file_size": getattr(doc, 'file_size', 0),
                "author": getattr(doc, 'author', '')
            }
            source_type = "gitlab"
            source_name = getattr(doc, 'project_name', 'unknown')
            source_url = getattr(doc, 'url', '')
            file_path = getattr(doc, 'file_path', '')
            
        elif hasattr(doc, '__class__') and 'Local' in doc.__class__.__name__:
            metadata = {
                "file_name": getattr(doc, 'file_name', ''),
                "file_extension": getattr(doc, 'file_extension', ''),
                "file_size": getattr(doc, 'file_size', 0),
                "file_type": getattr(doc, 'file_type', ''),
                "content_hash": getattr(doc, 'content_hash', '')
            }
            source_type = "local_files"
            source_name = "bootstrap"
            source_url = None
            file_path = getattr(doc, 'file_path', '')
            
        else:
            # Общий случай
            metadata = {
                "type": doc.__class__.__name__ if hasattr(doc, '__class__') else 'unknown'
            }
            source_type = "unknown"
            source_name = "unknown"
            source_url = getattr(doc, 'url', None)
            file_path = getattr(doc, 'file_path', None)
        
        # Парсинг дат
        created_at = self._parse_date(getattr(doc, 'created_date', None))
        modified_at = self._parse_date(getattr(doc, 'modified_date', None))
        
        return {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "source_type": source_type,
            "source_name": source_name,
            "source_url": source_url,
            "file_path": file_path,
            "metadata": metadata,
            "content_hash": content_hash,
            "created_at": created_at or datetime.now(),
            "updated_at": modified_at or datetime.now()
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Парсинг строки даты"""
        if not date_str:
            return None
        
        try:
            # Попытка парсинга ISO формата
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(date_str)
        except:
            try:
                # Попытка парсинга других форматов
                from dateutil import parser
                return parser.parse(date_str)
            except:
                logger.warning("Failed to parse date", date_str=date_str)
                return None
    
    async def save_ingestion_stats(self, stats: Dict[str, Any]) -> int:
        """Сохранение статистики ingestion"""
        try:
            async with self.pool.acquire() as conn:
                stat_id = await conn.fetchval("""
                    INSERT INTO ingestion_stats 
                    (source_type, source_name, documents_processed, documents_skipped, 
                     documents_failed, total_size_bytes, processing_time_seconds, 
                     started_at, completed_at, status, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    RETURNING id
                """,
                    stats.get("source_type"),
                    stats.get("source_name"),
                    stats.get("documents_processed", 0),
                    stats.get("documents_skipped", 0),
                    stats.get("documents_failed", 0),
                    stats.get("total_size_bytes", 0),
                    stats.get("processing_time_seconds", 0),
                    stats.get("started_at"),
                    stats.get("completed_at"),
                    stats.get("status", "completed"),
                    stats.get("error_message")
                )
                
                logger.info("Ingestion stats saved", stat_id=stat_id)
                return stat_id
                
        except Exception as e:
            logger.error("Failed to save ingestion stats", error=str(e))
            raise
    
    async def get_document_count(self, source_type: Optional[str] = None) -> int:
        """Получение количества документов"""
        try:
            async with self.pool.acquire() as conn:
                if source_type:
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM ingested_documents WHERE source_type = $1",
                        source_type
                    )
                else:
                    count = await conn.fetchval("SELECT COUNT(*) FROM ingested_documents")
                
                return count or 0
                
        except Exception as e:
            logger.error("Failed to get document count", error=str(e))
            return 0
    
    async def close(self):
        """Закрытие соединений"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed") 