"""
User service module
"""

import asyncio
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta

from ..core.exceptions import AsyncResourceError
from ..security.auth import verify_password, hash_password


class UserService:
    """User management service"""
    
    def __init__(self, user_repository=None, email_service=None):
        self.user_repository = user_repository
        self.email_service = email_service
        self.users: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    async def create_user(self, email: str, password: str, username: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        # Check if user already exists
        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user data
        user_data = {
            "id": str(self.next_id),
            "email": email,
            "username": username or email,
            "password_hash": password_hash,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Store user
        self.users[user_data["id"]] = user_data
        self.next_id += 1
        
        # Send verification email if email service is available
        if self.email_service:
            verification_token = secrets.token_urlsafe(32)
            await self.email_service.send_verification_email(email, verification_token)
        
        return user_data
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if self.user_repository:
            return await self.user_repository.get_user_by_id(user_id)
        return self.users.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        if self.user_repository:
            return await self.user_repository.get_user_by_email(email)
        
        for user in self.users.values():
            if user["email"] == email:
                return user
        return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user"""
        if self.user_repository:
            return await self.user_repository.update_user(user_id, updates)
        
        if user_id not in self.users:
            return False
        
        # Update timestamp
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Hash password if provided
        if "password" in updates:
            updates["password_hash"] = hash_password(updates.pop("password"))
        
        self.users[user_id].update(updates)
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        if self.user_repository:
            return await self.user_repository.delete_user(user_id)
        
        if user_id not in self.users:
            return False
        
        del self.users[user_id]
        return True
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not user.get("is_active"):
            return None
        
        if verify_password(password, user["password_hash"]):
            return user
        
        return None
    
    async def verify_user_email(self, email: str, token: str) -> bool:
        """Verify user email"""
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        # For now, just mark as verified
        await self.update_user(user["id"], {"is_verified": True})
        return True
    
    async def request_password_reset(self, email: str) -> bool:
        """Request password reset"""
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # Store reset token (in real implementation, this would be in database)
        await self.update_user(user["id"], {
            "reset_token": reset_token,
            "reset_token_expires": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        })
        
        # Send reset email if email service is available
        if self.email_service:
            await self.email_service.send_password_reset_email(email, reset_token)
        
        return True
    
    async def reset_password(self, email: str, token: str, new_password: str) -> bool:
        """Reset password"""
        user = await self.get_user_by_email(email)
        if not user:
            return False
        
        # Check token
        if user.get("reset_token") != token:
            return False
        
        # Check token expiry
        if user.get("reset_token_expires"):
            expires_at = datetime.fromisoformat(user["reset_token_expires"])
            if datetime.now(timezone.utc) > expires_at:
                return False
        
        # Update password
        await self.update_user(user["id"], {
            "password": new_password,
            "reset_token": None,
            "reset_token_expires": None
        })
        
        return True
    
    async def list_users(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List users"""
        if self.user_repository:
            # In real implementation, this would use repository method
            pass
        
        users = list(self.users.values())
        return users[offset:offset + limit]
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.get("is_active"))
        verified_users = sum(1 for user in self.users.values() if user.get("is_verified"))
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "unverified_users": total_users - verified_users
        }
    
    def clear_users(self):
        """Clear all users (for testing)"""
        self.users.clear()
        self.next_id = 1


# Global instance
user_service = UserService() 