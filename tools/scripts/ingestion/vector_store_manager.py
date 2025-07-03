"""
Vector Store Manager for Data Ingestion
Управление векторным хранилищем Qdrant
"""

import asyncio
from typing import Dict, List, Any, Optional
import structlog
from qdrant_client import QdrantClient
from qdrant_client.http import models
import hashlib

logger = structlog.get_logger()


class VectorStoreManager:
    """Менеджер векторного хранилища"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.url = config["url"]
        self.collection_size = config.get("collection_size", 1536)
        
        # Названия коллекций для разных типов источников
        self.collections = {
            "confluence": "confluence_documents",
            "gitlab": "gitlab_documents", 
            "local_files": "local_documents",
            "general": "general_documents"
        }
    
    async def initialize(self):
        """Инициализация клиента Qdrant"""
        try:
            self.client = QdrantClient(url=self.url)
            
            # Проверка подключения
            collections = self.client.get_collections()
            logger.info("Connected to Qdrant", collections_count=len(collections.collections))
            
            # Создание коллекций
            await self._create_collections()
            
            logger.info("Vector store manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize vector store manager", error=str(e))
            raise
    
    async def _create_collections(self):
        """Создание коллекций для разных типов документов"""
        for source_type, collection_name in self.collections.items():
            try:
                # Проверка существования коллекции
                try:
                    collection_info = self.client.get_collection(collection_name)
                    logger.info("Collection already exists", collection=collection_name)
                    continue
                except Exception:
                    # Коллекция не существует, создаем
                    pass
                
                # Создание коллекции
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.collection_size,
                        distance=models.Distance.COSINE
                    ),
                    optimizers_config=models.OptimizersConfig(
                        default_segment_number=2,
                        max_segment_size=20000,
                        memmap_threshold=20000,
                        indexing_threshold=10000,
                        flush_interval_sec=5,
                        max_optimization_threads=2
                    ),
                    hnsw_config=models.HnswConfig(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                        max_indexing_threads=2
                    )
                )
                
                logger.info("Created collection", collection=collection_name)
                
            except Exception as e:
                logger.error(
                    "Failed to create collection",
                    collection=collection_name,
                    error=str(e)
                )
    
    async def store_embeddings(self, documents: List[Any]) -> int:
        """Сохранение эмбеддингов документов"""
        if not documents:
            return 0
        
        stored_count = 0
        
        try:
            # Группировка документов по типу источника
            docs_by_type = {}
            for doc in documents:
                source_type = self._get_source_type(doc)
                if source_type not in docs_by_type:
                    docs_by_type[source_type] = []
                docs_by_type[source_type].append(doc)
            
            # Обработка каждого типа отдельно
            for source_type, docs in docs_by_type.items():
                collection_name = self.collections.get(source_type, self.collections["general"])
                
                # Подготовка данных для Qdrant
                points = []
                for doc in docs:
                    try:
                        # Генерация эмбеддинга (заглушка - в реальности используется OpenAI/другой провайдер)
                        embedding = await self._generate_embedding(doc.content)
                        
                        if embedding:
                            # Создание уникального ID
                            point_id = self._generate_point_id(doc.id)
                            
                            # Подготовка метаданных
                            payload = self._prepare_payload(doc)
                            
                            points.append(
                                models.PointStruct(
                                    id=point_id,
                                    vector=embedding,
                                    payload=payload
                                )
                            )
                    
                    except Exception as e:
                        logger.error(
                            "Failed to prepare point for document",
                            doc_id=getattr(doc, 'id', 'unknown'),
                            error=str(e)
                        )
                
                # Сохранение в Qdrant
                if points:
                    try:
                        result = self.client.upsert(
                            collection_name=collection_name,
                            points=points
                        )
                        
                        if result.status == models.UpdateStatus.COMPLETED:
                            stored_count += len(points)
                            logger.info(
                                "Stored embeddings",
                                collection=collection_name,
                                count=len(points)
                            )
                        else:
                            logger.warning(
                                "Partial success storing embeddings",
                                collection=collection_name,
                                status=result.status
                            )
                    
                    except Exception as e:
                        logger.error(
                            "Failed to store embeddings",
                            collection=collection_name,
                            error=str(e)
                        )
            
            return stored_count
            
        except Exception as e:
            logger.error("Failed to store embeddings batch", error=str(e))
            raise
    
    def _get_source_type(self, doc: Any) -> str:
        """Определение типа источника документа"""
        if hasattr(doc, '__class__'):
            class_name = doc.__class__.__name__.lower()
            if 'confluence' in class_name:
                return "confluence"
            elif 'gitlab' in class_name:
                return "gitlab"
            elif 'local' in class_name:
                return "local_files"
        
        return "general"
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Генерация эмбеддинга для текста"""
        try:
            # В реальной реализации здесь будет вызов OpenAI API или другого провайдера
            # Для демонстрации возвращаем заглушку
            
            # Простая заглушка - хеш текста преобразованный в вектор
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            # Преобразуем хеш в вектор нужной размерности
            embedding = []
            for i in range(0, min(len(text_hash), self.collection_size // 8)):
                # Преобразуем каждые 2 символа хеша в float
                hex_pair = text_hash[i*2:(i*2)+2] if i*2+1 < len(text_hash) else text_hash[i*2:] + "0"
                value = int(hex_pair, 16) / 255.0 - 0.5  # Нормализация в диапазон [-0.5, 0.5]
                embedding.append(value)
            
            # Дополняем до нужной размерности
            while len(embedding) < self.collection_size:
                embedding.append(0.0)
            
            # Обрезаем до нужной размерности
            embedding = embedding[:self.collection_size]
            
            return embedding
            
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return None
    
    def _generate_point_id(self, doc_id: str) -> str:
        """Генерация уникального ID для точки в Qdrant"""
        # Создаем хеш от ID документа для получения числового ID
        hash_obj = hashlib.md5(doc_id.encode())
        # Берем первые 8 байт хеша и преобразуем в int
        point_id = int.from_bytes(hash_obj.digest()[:8], byteorder='big')
        return str(point_id)
    
    def _prepare_payload(self, doc: Any) -> Dict[str, Any]:
        """Подготовка метаданных для сохранения в Qdrant"""
        payload = {
            "doc_id": doc.id,
            "title": doc.title,
            "content_preview": doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
            "content_length": len(doc.content)
        }
        
        # Добавление специфичных для типа метаданных
        if hasattr(doc, '__class__') and 'Confluence' in doc.__class__.__name__:
            payload.update({
                "source_type": "confluence",
                "space_key": getattr(doc, 'space_key', ''),
                "page_type": getattr(doc, 'page_type', ''),
                "author": getattr(doc, 'author', ''),
                "url": getattr(doc, 'url', ''),
                "labels": getattr(doc, 'labels', [])
            })
            
        elif hasattr(doc, '__class__') and 'GitLab' in doc.__class__.__name__:
            payload.update({
                "source_type": "gitlab",
                "project_name": getattr(doc, 'project_name', ''),
                "file_path": getattr(doc, 'file_path', ''),
                "file_extension": getattr(doc, 'file_extension', ''),
                "url": getattr(doc, 'url', ''),
                "branch": getattr(doc, 'branch', '')
            })
            
        elif hasattr(doc, '__class__') and 'Local' in doc.__class__.__name__:
            payload.update({
                "source_type": "local_files",
                "file_name": getattr(doc, 'file_name', ''),
                "file_path": getattr(doc, 'file_path', ''),
                "file_extension": getattr(doc, 'file_extension', ''),
                "file_type": getattr(doc, 'file_type', '')
            })
        
        return payload
    
    async def search_similar(self, query_embedding: List[float], collection_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск похожих документов"""
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
            
        except Exception as e:
            logger.error("Failed to search similar documents", error=str(e))
            return []
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Получение статистики коллекций"""
        stats = {}
        
        try:
            for source_type, collection_name in self.collections.items():
                try:
                    collection_info = self.client.get_collection(collection_name)
                    stats[source_type] = {
                        "collection_name": collection_name,
                        "points_count": collection_info.points_count,
                        "vectors_count": collection_info.vectors_count,
                        "status": collection_info.status.value if collection_info.status else "unknown"
                    }
                except Exception as e:
                    stats[source_type] = {
                        "collection_name": collection_name,
                        "error": str(e)
                    }
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {}
    
    async def close(self):
        """Закрытие соединений"""
        if self.client:
            # Qdrant client не требует явного закрытия
            logger.info("Vector store connections closed") 