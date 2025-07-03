"""
GitLab Data Ingestion Client
Многопоточная загрузка файлов из GitLab репозиториев
"""

import asyncio
import aiohttp
import base64
from typing import Dict, List, Any, AsyncGenerator, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, quote
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


@dataclass
class GitLabDocument:
    """Документ из GitLab"""
    id: str
    title: str
    content: str
    file_path: str
    project_name: str
    project_id: str
    branch: str
    url: str
    created_date: str
    modified_date: str
    author: str
    file_extension: str
    file_size: int


class GitLabIngestionClient:
    """Клиент для загрузки данных из GitLab"""
    
    def __init__(self, server_config: Dict[str, Any], processing_config: Dict[str, Any]):
        self.config = server_config
        self.processing_config = processing_config
        self.base_url = server_config["url"].rstrip("/")
        self.token = server_config["token"]
        self.session = None
        
        # Настройки фильтрации файлов
        self.supported_extensions = set(server_config.get("file_extensions", [".md", ".rst", ".txt"]))
        self.max_file_size_mb = server_config.get("max_file_size_mb", 10)
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
    
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
                "Authorization": f"Bearer {self.token}",
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
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Получение списка проектов"""
        projects = []
        page = 1
        per_page = 100
        
        # Получение проектов по группам
        configured_groups = self.config.get("groups", [])
        configured_projects = self.config.get("projects", [])
        
        if configured_groups:
            for group in configured_groups:
                try:
                    group_projects = await self._get_group_projects(group)
                    projects.extend(group_projects)
                except Exception as e:
                    logger.error("Failed to fetch group projects", group=group, error=str(e))
        
        # Получение конкретных проектов
        if configured_projects:
            for project_name in configured_projects:
                try:
                    project = await self._get_project_by_name(project_name)
                    if project:
                        projects.append(project)
                except Exception as e:
                    logger.error("Failed to fetch project", project=project_name, error=str(e))
        
        # Если ничего не настроено, получаем все доступные проекты
        if not configured_groups and not configured_projects:
            while True:
                try:
                    response = await self._make_request(
                        "/api/v4/projects",
                        params={
                            "page": page,
                            "per_page": per_page,
                            "membership": True,
                            "simple": True
                        }
                    )
                    
                    if not response:
                        break
                    
                    projects.extend(response)
                    
                    if len(response) < per_page:
                        break
                    
                    page += 1
                    
                except Exception as e:
                    logger.error("Failed to fetch projects", error=str(e))
                    break
        
        logger.info("Fetched projects", count=len(projects))
        return projects
    
    async def _get_group_projects(self, group_name: str) -> List[Dict[str, Any]]:
        """Получение проектов группы"""
        projects = []
        page = 1
        per_page = 100
        
        # Кодирование имени группы для URL
        encoded_group = quote(group_name, safe='')
        
        while True:
            try:
                response = await self._make_request(
                    f"/api/v4/groups/{encoded_group}/projects",
                    params={
                        "page": page,
                        "per_page": per_page,
                        "simple": True
                    }
                )
                
                if not response:
                    break
                
                projects.extend(response)
                
                if len(response) < per_page:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error("Failed to fetch group projects", group=group_name, error=str(e))
                break
        
        return projects
    
    async def _get_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Получение проекта по имени"""
        try:
            encoded_project = quote(project_name, safe='')
            return await self._make_request(f"/api/v4/projects/{encoded_project}")
        except Exception as e:
            logger.error("Failed to fetch project by name", project=project_name, error=str(e))
            return None
    
    async def get_repository_files(self, project_id: int, project_name: str) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Получение файлов из репозитория"""
        try:
            # Получение дерева файлов
            tree = await self._get_repository_tree(project_id)
            
            # Фильтрация файлов по расширению и размеру
            filtered_files = []
            for item in tree:
                if item.get("type") == "blob":  # Это файл, не директория
                    file_path = item.get("path", "")
                    file_extension = self._get_file_extension(file_path)
                    
                    if file_extension in self.supported_extensions:
                        filtered_files.append({
                            "id": item.get("id"),
                            "path": file_path,
                            "project_id": project_id,
                            "project_name": project_name
                        })
            
            logger.info(
                "Found files for processing",
                project=project_name,
                total_files=len(filtered_files)
            )
            
            # Обработка файлов батчами
            batch_size = self.processing_config.get("batch_size", 50)
            
            for i in range(0, len(filtered_files), batch_size):
                batch = filtered_files[i:i + batch_size]
                
                # Параллельная загрузка файлов в батче
                tasks = [
                    self._fetch_file_content(file_info)
                    for file_info in batch
                ]
                
                file_contents = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Фильтрация успешно загруженных файлов
                valid_files = [
                    content for content in file_contents
                    if isinstance(content, GitLabDocument)
                ]
                
                if valid_files:
                    yield valid_files
                
                # Небольшая пауза между батчами
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(
                "Failed to get repository files",
                project_id=project_id,
                project_name=project_name,
                error=str(e)
            )
    
    async def _get_repository_tree(self, project_id: int, path: str = "", recursive: bool = True) -> List[Dict[str, Any]]:
        """Получение дерева файлов репозитория"""
        tree = []
        page = 1
        per_page = 100
        
        while True:
            try:
                params = {
                    "page": page,
                    "per_page": per_page,
                    "recursive": recursive
                }
                
                if path:
                    params["path"] = path
                
                response = await self._make_request(
                    f"/api/v4/projects/{project_id}/repository/tree",
                    params=params
                )
                
                if not response:
                    break
                
                tree.extend(response)
                
                if len(response) < per_page:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error("Failed to fetch repository tree", project_id=project_id, error=str(e))
                break
        
        return tree
    
    async def _fetch_file_content(self, file_info: Dict[str, Any]) -> Optional[GitLabDocument]:
        """Загрузка содержимого файла"""
        try:
            project_id = file_info["project_id"]
            file_path = file_info["path"]
            
            # Кодирование пути файла
            encoded_path = quote(file_path, safe='')
            
            # Получение информации о файле
            file_data = await self._make_request(
                f"/api/v4/projects/{project_id}/repository/files/{encoded_path}",
                params={"ref": "main"}  # или master, в зависимости от настроек
            )
            
            # Проверка размера файла
            file_size = file_data.get("size", 0)
            if file_size > self.max_file_size_bytes:
                logger.warning(
                    "File too large, skipping",
                    file_path=file_path,
                    size_mb=file_size / 1024 / 1024
                )
                return None
            
            # Декодирование содержимого
            content = file_data.get("content", "")
            encoding = file_data.get("encoding", "base64")
            
            if encoding == "base64":
                try:
                    content = base64.b64decode(content).decode("utf-8")
                except UnicodeDecodeError:
                    # Попытка с другими кодировками
                    try:
                        content = base64.b64decode(content).decode("latin-1")
                    except:
                        logger.warning("Failed to decode file content", file_path=file_path)
                        return None
            
            # Проверка минимальной длины контента
            if len(content.strip()) < 50:
                return None
            
            # Создание URL файла
            file_url = f"{self.base_url}/{file_info['project_name']}/-/blob/main/{file_path}"
            
            return GitLabDocument(
                id=f"{project_id}:{file_path}",
                title=self._get_file_title(file_path),
                content=content,
                file_path=file_path,
                project_name=file_info["project_name"],
                project_id=str(project_id),
                branch="main",
                url=file_url,
                created_date=file_data.get("created_at", ""),
                modified_date=file_data.get("last_commit_id", ""),
                author=file_data.get("author_name", ""),
                file_extension=self._get_file_extension(file_path),
                file_size=file_size
            )
            
        except Exception as e:
            logger.warning(
                "Failed to fetch file content",
                file_path=file_info.get("path"),
                error=str(e)
            )
            return None
    
    def _get_file_extension(self, file_path: str) -> str:
        """Получение расширения файла"""
        return "." + file_path.split(".")[-1].lower() if "." in file_path else ""
    
    def _get_file_title(self, file_path: str) -> str:
        """Получение заголовка файла"""
        filename = file_path.split("/")[-1]
        return filename.split(".")[0] if "." in filename else filename
    
    async def fetch_content_batches(self) -> AsyncGenerator[List[GitLabDocument], None]:
        """Основной метод для получения всего контента батчами"""
        async with self:
            try:
                projects = await self.get_projects()
                
                if not projects:
                    logger.warning("No projects found or configured")
                    return
                
                for project in projects:
                    project_id = project.get("id")
                    project_name = project.get("name", "")
                    
                    logger.info("Processing project", project_name=project_name, project_id=project_id)
                    
                    try:
                        async for file_batch in self.get_repository_files(project_id, project_name):
                            if file_batch:
                                yield file_batch
                                
                    except Exception as e:
                        logger.error(
                            "Failed to process project",
                            project_name=project_name,
                            error=str(e)
                        )
                        continue
                
            except Exception as e:
                logger.error("Failed to fetch GitLab content", error=str(e))
                raise 