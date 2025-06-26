"""
Confluence Data Ingestion Client
Многопоточная загрузка данных из Confluence с защитой от таймаутов
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from urllib.parse import urljoin
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


@dataclass
class ConfluenceDocument:
    """Документ из Confluence"""
    id: str
    title: str
    content: str
    space_key: str
    page_type: str
    url: str
    created_date: str
    modified_date: str
    author: str
    labels: List[str]
    parent_id: Optional[str] = None


class ConfluenceIngestionClient:
    """Клиент для загрузки данных из Confluence"""
    
    def __init__(self, server_config: Dict[str, Any], processing_config: Dict[str, Any]):
        self.config = server_config
        self.processing_config = processing_config
        self.base_url = server_config["url"].rstrip("/")
        self.session = None
        
        # Настройка аутентификации
        if "api_token" in server_config:
            # Atlassian Cloud (email + API token)
            auth_string = f"{server_config['username']}:{server_config['api_token']}"
            self.auth_header = base64.b64encode(auth_string.encode()).decode()
            self.auth_type = "basic"
        elif "password" in server_config:
            # Legacy Confluence (username + password)
            auth_string = f"{server_config['username']}:{server_config['password']}"
            self.auth_header = base64.b64encode(auth_string.encode()).decode()
            self.auth_type = "basic"
        else:
            raise ValueError("No authentication method provided for Confluence")
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            limit=self.processing_config.get("max_workers", 10),
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.processing_config.get("timeout_seconds", 300),
            connect=30,
            sock_read=60
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "Authorization": f"Basic {self.auth_header}",
                "Content-Type": "application/json",
                "User-Agent": "AI-Assistant-Ingestion/1.0"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Выполнение HTTP запроса с retry логикой"""
        url = urljoin(self.base_url, endpoint)
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 429:
                    # Rate limiting
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning("Rate limited, waiting", retry_after=retry_after)
                    await asyncio.sleep(retry_after)
                    raise aiohttp.ClientError("Rate limited")
                
                response.raise_for_status()
                return await response.json()
                
        except asyncio.TimeoutError:
            logger.error("Request timeout", url=url)
            raise
        except aiohttp.ClientError as e:
            logger.error("HTTP request failed", url=url, error=str(e))
            raise
    
    async def get_spaces(self) -> List[Dict[str, Any]]:
        """Получение списка пространств"""
        spaces = []
        start = 0
        limit = 50
        
        while True:
            try:
                response = await self._make_request(
                    "/rest/api/content",
                    params={
                        "type": "space",
                        "start": start,
                        "limit": limit,
                        "expand": "metadata.labels,description"
                    }
                )
                
                batch_spaces = response.get("results", [])
                if not batch_spaces:
                    break
                
                # Фильтрация по настроенным пространствам
                configured_spaces = self.config.get("spaces", [])
                if configured_spaces:
                    batch_spaces = [
                        space for space in batch_spaces
                        if space.get("key") in configured_spaces
                    ]
                
                spaces.extend(batch_spaces)
                
                if len(batch_spaces) < limit:
                    break
                
                start += limit
                
            except Exception as e:
                logger.error("Failed to fetch spaces", error=str(e))
                break
        
        logger.info("Fetched spaces", count=len(spaces))
        return spaces
    
    async def get_pages_in_space(self, space_key: str) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Получение страниц в пространстве батчами"""
        start = 0
        limit = self.processing_config.get("batch_size", 50)
        max_pages = self.config.get("max_pages", 1000)
        total_fetched = 0
        
        content_types = self.config.get("content_types", ["page"])
        
        for content_type in content_types:
            start = 0
            
            while total_fetched < max_pages:
                try:
                    response = await self._make_request(
                        "/rest/api/content",
                        params={
                            "spaceKey": space_key,
                            "type": content_type,
                            "status": "current",
                            "start": start,
                            "limit": min(limit, max_pages - total_fetched),
                            "expand": "body.storage,metadata.labels,space,history,version"
                        }
                    )
                    
                    pages = response.get("results", [])
                    if not pages:
                        break
                    
                    # Фильтрация и обогащение данных
                    processed_pages = []
                    for page in pages:
                        try:
                            processed_page = await self._process_page(page)
                            if processed_page:
                                processed_pages.append(processed_page)
                        except Exception as e:
                            logger.warning(
                                "Failed to process page",
                                page_id=page.get("id"),
                                error=str(e)
                            )
                    
                    if processed_pages:
                        yield processed_pages
                    
                    total_fetched += len(pages)
                    
                    if len(pages) < limit:
                        break
                    
                    start += limit
                    
                    # Небольшая пауза между запросами
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(
                        "Failed to fetch pages",
                        space_key=space_key,
                        content_type=content_type,
                        error=str(e)
                    )
                    break
    
    async def _process_page(self, page_data: Dict[str, Any]) -> Optional[ConfluenceDocument]:
        """Обработка отдельной страницы"""
        try:
            # Извлечение содержимого
            body = page_data.get("body", {})
            storage = body.get("storage", {})
            content = storage.get("value", "")
            
            if not content or len(content.strip()) < 50:
                return None
            
            # Очистка HTML тегов
            content = await self._clean_html_content(content)
            
            # Извлечение метаданных
            space = page_data.get("space", {})
            history = page_data.get("history", {})
            version = page_data.get("version", {})
            
            # Извлечение лейблов
            labels = []
            metadata = page_data.get("metadata", {})
            if "labels" in metadata:
                labels = [
                    label.get("name", "")
                    for label in metadata["labels"].get("results", [])
                ]
            
            # Создание URL
            page_url = urljoin(
                self.base_url,
                f"/wiki/spaces/{space.get('key', '')}/pages/{page_data.get('id', '')}"
            )
            
            return ConfluenceDocument(
                id=page_data.get("id", ""),
                title=page_data.get("title", ""),
                content=content,
                space_key=space.get("key", ""),
                page_type=page_data.get("type", "page"),
                url=page_url,
                created_date=history.get("createdDate", ""),
                modified_date=version.get("when", ""),
                author=history.get("createdBy", {}).get("displayName", ""),
                labels=labels,
                parent_id=page_data.get("parentId")
            )
            
        except Exception as e:
            logger.error(
                "Failed to process page data",
                page_id=page_data.get("id"),
                error=str(e)
            )
            return None
    
    async def _clean_html_content(self, html_content: str) -> str:
        """Очистка HTML контента"""
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Удаление скриптов и стилей
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Извлечение текста
            text = soup.get_text()
            
            # Очистка лишних пробелов и переносов
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.warning("Failed to clean HTML content", error=str(e))
            return html_content
    
    async def fetch_content_batches(self) -> AsyncGenerator[List[ConfluenceDocument], None]:
        """Основной метод для получения всего контента батчами"""
        async with self:
            try:
                spaces = await self.get_spaces()
                
                if not spaces:
                    logger.warning("No spaces found or configured")
                    return
                
                for space in spaces:
                    space_key = space.get("key")
                    logger.info("Processing space", space_key=space_key)
                    
                    try:
                        async for page_batch in self.get_pages_in_space(space_key):
                            if page_batch:
                                yield page_batch
                                
                    except Exception as e:
                        logger.error(
                            "Failed to process space",
                            space_key=space_key,
                            error=str(e)
                        )
                        continue
                
            except Exception as e:
                logger.error("Failed to fetch Confluence content", error=str(e))
                raise 