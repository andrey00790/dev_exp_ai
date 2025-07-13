"""
Mock services for testing
"""

import asyncio
from typing import Dict, Any, Optional, List
from unittest.mock import Mock

from backend.application.ports.email_service import EmailServicePort


class MockEmailService(EmailServicePort):
    """Mock email service for testing"""
    
    def __init__(self):
        self.sent_emails: List[Dict[str, Any]] = []
        self.should_fail = False
    
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """Mock email sending"""
        if self.should_fail:
            return False
        
        email_data = {
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "sent_at": asyncio.get_event_loop().time()
        }
        self.sent_emails.append(email_data)
        return True
    
    async def send_verification_email(self, email: str, token: str) -> bool:
        """Mock verification email sending"""
        return await self.send_email(
            to=email,
            subject="Email Verification",
            body=f"Verification token: {token}"
        )
    
    async def send_password_reset_email(self, email: str, token: str) -> bool:
        """Mock password reset email sending"""
        return await self.send_email(
            to=email,
            subject="Password Reset",
            body=f"Password reset token: {token}"
        )
    
    def get_sent_emails(self) -> List[Dict[str, Any]]:
        """Get list of sent emails"""
        return self.sent_emails.copy()
    
    def clear_sent_emails(self):
        """Clear sent emails list"""
        self.sent_emails.clear()
    
    def set_should_fail(self, should_fail: bool):
        """Set whether email sending should fail"""
        self.should_fail = should_fail


class MockUserRepository:
    """Mock user repository for testing"""
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a mock user"""
        user_id = str(self.next_id)
        self.next_id += 1
        
        user = {
            "id": user_id,
            "email": user_data["email"],
            "username": user_data.get("username", user_data["email"]),
            "password_hash": user_data.get("password_hash", "mock_hash"),
            "is_active": True,
            "is_verified": False,
            "created_at": asyncio.get_event_loop().time()
        }
        
        self.users[user_id] = user
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        if user_id not in self.users:
            return False
        
        self.users[user_id].update(updates)
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        if user_id not in self.users:
            return False
        
        del self.users[user_id]
        return True
    
    def clear_users(self):
        """Clear all users"""
        self.users.clear()
        self.next_id = 1


class MockAuthService:
    """Mock authentication service for testing"""
    
    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.user_repository = MockUserRepository()
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Mock user authentication"""
        user = await self.user_repository.get_user_by_email(email)
        if user and user.get("password_hash") == f"hash_{password}":
            return user
        return None
    
    async def create_token(self, user_id: str) -> str:
        """Create mock token"""
        token = f"mock_token_{user_id}_{len(self.tokens)}"
        self.tokens[token] = {
            "user_id": user_id,
            "created_at": asyncio.get_event_loop().time(),
            "expires_at": asyncio.get_event_loop().time() + 3600
        }
        return token
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate mock token"""
        token_data = self.tokens.get(token)
        if not token_data:
            return None
        
        if token_data["expires_at"] < asyncio.get_event_loop().time():
            return None
        
        return token_data
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke mock token"""
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def clear_tokens(self):
        """Clear all tokens"""
        self.tokens.clear()


class MockCacheService:
    """Mock cache service for testing"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Any:
        """Get value from mock cache"""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in mock cache"""
        self.cache[key] = value
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from mock cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> bool:
        """Clear mock cache"""
        self.cache.clear()
        return True
    
    def get_cache_size(self) -> int:
        """Get cache size"""
        return len(self.cache)


class MockVectorStoreService:
    """Mock vector store service for testing"""
    
    def __init__(self):
        self.vectors: Dict[str, Dict[str, Any]] = {}
        self.collections: Dict[str, List[str]] = {}
    
    async def add_vector(self, collection: str, vector_id: str, vector: List[float], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add vector to mock store"""
        if collection not in self.collections:
            self.collections[collection] = []
        
        self.vectors[vector_id] = {
            "collection": collection,
            "vector": vector,
            "metadata": metadata or {}
        }
        self.collections[collection].append(vector_id)
        return True
    
    async def search_vectors(self, collection: str, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """Search vectors in mock store"""
        if collection not in self.collections:
            return []
        
        results = []
        for vector_id in self.collections[collection][:limit]:
            vector_data = self.vectors[vector_id]
            results.append({
                "id": vector_id,
                "score": 0.9,  # Mock similarity score
                "metadata": vector_data["metadata"]
            })
        
        return results
    
    async def delete_vector(self, collection: str, vector_id: str) -> bool:
        """Delete vector from mock store"""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            if collection in self.collections:
                self.collections[collection] = [
                    vid for vid in self.collections[collection] if vid != vector_id
                ]
            return True
        return False
    
    def clear_vectors(self):
        """Clear all vectors"""
        self.vectors.clear()
        self.collections.clear() 