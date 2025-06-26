"""
Standardized HTTP client patterns for AI Assistant
Following FastAPI and aiohttp best practices
"""

import aiohttp
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urljoin

from models.shared.types import JSON, Headers, OptionalStr
from .async_utils import AsyncTimeouts, with_timeout, async_retry
from .exceptions import AsyncTimeoutError, AsyncResourceError

logger = logging.getLogger(__name__)


class StandardHttpClient:
    """
    Standard HTTP client with consistent patterns and proper async resource management
    Following FastAPI recommendations for HTTP client usage
    """
    
    def __init__(
        self, 
        base_url: OptionalStr = None,
        default_timeout: float = AsyncTimeouts.HTTP_REQUEST,
        default_headers: Optional[Headers] = None,
        retry_attempts: int = 3
    ):
        self.base_url = base_url.rstrip('/') if base_url else None
        self.default_timeout = default_timeout
        self.default_headers = default_headers or {}
        self.retry_attempts = retry_attempts
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure HTTP session is created and ready"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=60
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.default_timeout,
                connect=10.0,
                sock_read=30.0
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.default_headers,
                raise_for_status=False  # Handle status manually
            )
            
        return self._session
    
    def _build_url(self, path: str) -> str:
        """Build full URL from base URL and path"""
        if path.startswith(('http://', 'https://')):
            return path
        if self.base_url:
            return urljoin(f"{self.base_url}/", path.lstrip('/'))
        return path
    
    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """Perform GET request with retry and timeout"""
        session = await self._ensure_session()
        url = self._build_url(path)
        request_timeout = timeout or self.default_timeout
        
        return await with_timeout(
            session.get(url, params=params, headers=headers),
            request_timeout,
            f"GET request to {url} timed out"
        )
    
    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def post(
        self,
        path: str,
        json_data: Optional[JSON] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """Perform POST request with retry and timeout"""
        session = await self._ensure_session()
        url = self._build_url(path)
        request_timeout = timeout or self.default_timeout
        
        return await with_timeout(
            session.post(url, json=json_data, data=data, headers=headers),
            request_timeout,
            f"POST request to {url} timed out"
        )
    
    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def put(
        self,
        path: str,
        json_data: Optional[JSON] = None,
        data: Optional[Any] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """Perform PUT request with retry and timeout"""
        session = await self._ensure_session()
        url = self._build_url(path)
        request_timeout = timeout or self.default_timeout
        
        return await with_timeout(
            session.put(url, json=json_data, data=data, headers=headers),
            request_timeout,
            f"PUT request to {url} timed out"
        )
    
    @async_retry(max_attempts=3, delay=1.0, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> aiohttp.ClientResponse:
        """Perform DELETE request with retry and timeout"""
        session = await self._ensure_session()
        url = self._build_url(path)
        request_timeout = timeout or self.default_timeout
        
        return await with_timeout(
            session.delete(url, params=params, headers=headers),
            request_timeout,
            f"DELETE request to {url} timed out"
        )
    
    async def get_json(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> JSON:
        """GET request that returns JSON data"""
        response = await self.get(path, params, headers, timeout)
        
        if response.status >= 400:
            error_text = await response.text()
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=f"HTTP {response.status}: {error_text}"
            )
        
        return await response.json()
    
    async def post_json(
        self,
        path: str,
        json_data: Optional[JSON] = None,
        headers: Optional[Headers] = None,
        timeout: Optional[float] = None
    ) -> JSON:
        """POST request that returns JSON data"""
        response = await self.post(path, json_data=json_data, headers=headers, timeout=timeout)
        
        if response.status >= 400:
            error_text = await response.text()
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=f"HTTP {response.status}: {error_text}"
            )
        
        return await response.json()
    
    async def close(self) -> None:
        """Close HTTP session and clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.debug("HTTP client session closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


@asynccontextmanager
async def http_client_context(
    base_url: OptionalStr = None,
    timeout: float = AsyncTimeouts.HTTP_REQUEST,
    headers: Optional[Headers] = None
):
    """
    Context manager for HTTP client with automatic cleanup
    
    Usage:
        async with http_client_context("https://api.example.com") as client:
            response = await client.get("/users")
    """
    client = StandardHttpClient(base_url=base_url, default_timeout=timeout, default_headers=headers)
    try:
        yield client
    finally:
        await client.close()


def http_client_factory(
    base_url: OptionalStr = None,
    timeout: float = AsyncTimeouts.HTTP_REQUEST,
    headers: Optional[Headers] = None,
    retry_attempts: int = 3
) -> StandardHttpClient:
    """
    Factory function for creating HTTP clients
    
    Args:
        base_url: Base URL for all requests
        timeout: Default timeout for requests
        headers: Default headers for all requests
        retry_attempts: Number of retry attempts for failed requests
        
    Returns:
        Configured HTTP client instance
    """
    return StandardHttpClient(
        base_url=base_url,
        default_timeout=timeout,
        default_headers=headers,
        retry_attempts=retry_attempts
    )


# Pre-configured clients for common scenarios
def api_client(base_url: str, api_key: OptionalStr = None) -> StandardHttpClient:
    """Create API client with authentication headers"""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    return http_client_factory(
        base_url=base_url,
        headers=headers,
        timeout=AsyncTimeouts.HTTP_REQUEST
    )


def internal_service_client(service_name: str, base_url: str) -> StandardHttpClient:
    """Create client for internal service communication"""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": f"ai-assistant-{service_name}",
        "X-Service-Name": service_name
    }
    
    return http_client_factory(
        base_url=base_url,
        headers=headers,
        timeout=AsyncTimeouts.HTTP_REQUEST,
        retry_attempts=2  # Fewer retries for internal services
    ) 