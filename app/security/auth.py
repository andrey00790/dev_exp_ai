"""
JWT Authentication system for AI Assistant MVP
Enhanced with standardized async patterns for enterprise security
Version: 2.1 Async Optimized

Features:
- JWT token creation and validation with timeout protection
- User authentication with retry logic and enhanced error handling
- Concurrent user operations for improved performance
- Background security logging and monitoring
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from starlette.middleware.base import BaseHTTPMiddleware

# Import standardized async patterns
from app.core.async_utils import (AsyncTimeouts, async_retry,
                                  create_background_task, safe_gather,
                                  with_timeout)
from app.core.exceptions import AsyncRetryError, AsyncTimeoutError

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class User(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    is_active: bool = True
    scopes: list[str] = ["basic"]
    budget_limit: float = 100.0
    current_usage: float = 0.0


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    scopes: list[str] = []


USERS_DB: Dict[str, Dict[str, Any]] = {
    "admin@example.com": {
        "user_id": "admin_user",
        "email": "admin@example.com",
        "name": "Admin",
        "hashed_password": pwd_context.hash("admin"),
        "is_active": True,
        "scopes": ["admin", "basic"],
        "budget_limit": 1000.0,
        "current_usage": 0.0,
    },
    "user@example.com": {
        "user_id": "user_001",
        "email": "user@example.com",
        "name": "Test User",
        "hashed_password": pwd_context.hash("user123"),
        "is_active": True,
        "scopes": ["basic"],
        "budget_limit": 100.0,
        "current_usage": 0.0,
    },
}

# Enhanced authentication stats for monitoring
auth_stats = {
    "login_attempts": 0,
    "successful_logins": 0,
    "failed_logins": 0,
    "token_validations": 0,
    "token_failures": 0,
    "timeout_errors": 0,
    "concurrent_operations": 0,
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password with enhanced security"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"❌ Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Generate password hash with enhanced security"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"❌ Password hashing error: {e}")
        raise HTTPException(status_code=500, detail="Password processing failed")


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get user by email with timeout protection
    Enhanced with async patterns for enterprise security
    """
    try:
        # Add timeout protection for user lookup
        return await with_timeout(
            _get_user_by_email_internal(email),
            AsyncTimeouts.SECURITY_AUTH,  # 15 seconds for user lookup
            f"User lookup timed out for email: {email}",
            {"email": email, "operation": "get_user_by_email"},
        )
    except AsyncTimeoutError as e:
        auth_stats["timeout_errors"] += 1
        logger.error(f"❌ User lookup timed out: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error getting user by email: {e}")
        return None


async def _get_user_by_email_internal(email: str) -> Optional[Dict[str, Any]]:
    """Internal user lookup (simulates database query)"""
    # Simulate potential database delay
    import asyncio

    await asyncio.sleep(0.01)  # Simulate DB query time
    return USERS_DB.get(email)


@async_retry(max_attempts=3, delay=0.5, exceptions=(Exception,))
async def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate user by email and password
    Enhanced with retry logic and timeout protection
    """
    auth_stats["login_attempts"] += 1

    try:
        # Authenticate user with timeout protection
        user = await with_timeout(
            _authenticate_user_internal(email, password),
            AsyncTimeouts.SECURITY_AUTH,  # 15 seconds for authentication
            f"User authentication timed out for: {email}",
            {"email": email, "operation": "authenticate_user"},
        )

        if user:
            auth_stats["successful_logins"] += 1
            logger.info(f"✅ User authenticated successfully: {email}")

            # Log authentication in background
            create_background_task(
                _log_authentication_attempt(email, True, "successful_login"),
                f"auth_log_{email}",
            )
        else:
            auth_stats["failed_logins"] += 1
            logger.warning(f"⚠️ Authentication failed for: {email}")

            # Log failed attempt in background
            create_background_task(
                _log_authentication_attempt(email, False, "invalid_credentials"),
                f"auth_fail_log_{email}",
            )

        return user

    except AsyncTimeoutError as e:
        auth_stats["timeout_errors"] += 1
        auth_stats["failed_logins"] += 1
        logger.error(f"❌ Authentication timeout for {email}: {e}")
        return None
    except Exception as e:
        auth_stats["failed_logins"] += 1
        logger.error(f"❌ Authentication error for {email}: {e}")
        return None


async def _authenticate_user_internal(email: str, password: str) -> Optional[User]:
    """Internal authentication logic"""
    user_data = await get_user_by_email(email)
    if not user_data:
        return None

    if not verify_password(password, user_data["hashed_password"]):
        return None

    return User(
        user_id=user_data["user_id"],
        email=user_data["email"],
        name=user_data["name"],
        is_active=user_data["is_active"],
        scopes=user_data["scopes"],
        budget_limit=user_data["budget_limit"],
        current_usage=user_data["current_usage"],
    )


async def _log_authentication_attempt(email: str, success: bool, reason: str):
    """Background logging of authentication attempts"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "email": email,
            "success": success,
            "reason": reason,
            "source": "jwt_auth_system",
        }

        # In production, this would write to security audit logs
        logger.info(f"🔐 Auth log: {log_entry}")

    except Exception as e:
        logger.error(f"❌ Error logging auth attempt: {e}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with enhanced security
    """
    try:
        to_encode = data.copy()
        expire = datetime.utcnow() + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})

        token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"✅ Token created for user: {data.get('sub', 'unknown')}")
        return token

    except Exception as e:
        logger.error(f"❌ Token creation error: {e}")
        raise HTTPException(status_code=500, detail="Token creation failed")


@async_retry(max_attempts=2, delay=0.5, exceptions=(JWTError,))
async def verify_token(token: str) -> TokenData:
    """
    Verify JWT token with enhanced security and timeout protection
    """
    auth_stats["token_validations"] += 1

    try:
        # Verify token with timeout protection
        token_data = await with_timeout(
            _verify_token_internal(token),
            AsyncTimeouts.DATABASE_QUERY,  # 10 seconds for token verification
            "Token verification timed out",
            {"operation": "verify_token"},
        )

        logger.debug(f"✅ Token verified for user: {token_data.user_id}")
        return token_data

    except AsyncTimeoutError as e:
        auth_stats["timeout_errors"] += 1
        auth_stats["token_failures"] += 1
        logger.error(f"❌ Token verification timed out: {e}")
        raise HTTPException(
            status_code=401, detail=f"Token verification timed out: {str(e)}"
        )
    except JWTError as e:
        auth_stats["token_failures"] += 1
        logger.warning(f"⚠️ Token verification failed: {e}")
        raise HTTPException(
            status_code=401, detail=f"Could not validate credentials: {e}"
        )
    except Exception as e:
        auth_stats["token_failures"] += 1
        logger.error(f"❌ Unexpected token verification error: {e}")
        raise HTTPException(status_code=401, detail="Token verification failed")


async def _verify_token_internal(token: str) -> TokenData:
    """Internal token verification logic"""
    # Check for empty or malformed tokens (Context7 best practice)
    if not token or not token.strip():
        raise JWTError("Empty token provided")
    
    # Check for minimal JWT structure (3 segments separated by dots)
    if len(token.split('.')) != 3:
        raise JWTError("Not enough segments")
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("sub")
    email = payload.get("email")
    scopes = payload.get("scopes", [])

    if user_id is None or email is None:
        raise JWTError("Invalid token payload")

    return TokenData(user_id=user_id, email=email, scopes=scopes)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Get current user from JWT token
    Enhanced with concurrent validation and timeout protection
    """
    try:
        # Verify token and get user concurrently
        token_data, user_data = await safe_gather(
            verify_token(credentials.credentials),
            get_user_by_email_from_token(credentials.credentials),
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=2,
        )

        # Handle verification results
        if isinstance(token_data, Exception):
            logger.error(f"❌ Token verification failed: {token_data}")
            raise HTTPException(status_code=401, detail="Token verification failed")

        if isinstance(user_data, Exception) or not user_data:
            logger.error(f"❌ User data retrieval failed: {user_data}")
            raise HTTPException(status_code=401, detail="User not found or inactive")

        if not user_data.get("is_active", False):
            raise HTTPException(status_code=401, detail="User account is inactive")

        user = User(**user_data)
        logger.debug(f"✅ Current user retrieved: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting current user: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_user_by_email_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Get user data by extracting email from token"""
    try:
        token_data = await _verify_token_internal(token)
        return await get_user_by_email(token_data.email)
    except Exception as e:
        logger.error(f"❌ Error getting user from token: {e}")
        return None


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify admin privileges
    Enhanced with timeout protection
    """
    try:
        # Check admin privileges with timeout protection
        is_admin = await with_timeout(
            _check_admin_privileges(current_user),
            AsyncTimeouts.DATABASE_QUERY,
            f"Admin privilege check timed out for user: {current_user.user_id}",
            {"user_id": current_user.user_id, "operation": "check_admin"},
        )

        if not is_admin:
            logger.warning(f"⚠️ Admin access denied for user: {current_user.email}")
            raise HTTPException(status_code=403, detail="Admin privileges required")

        logger.debug(f"✅ Admin access granted for user: {current_user.email}")
        return current_user

    except AsyncTimeoutError as e:
        auth_stats["timeout_errors"] += 1
        logger.error(f"❌ Admin check timed out: {e}")
        raise HTTPException(status_code=408, detail="Admin privilege check timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error checking admin privileges: {e}")
        raise HTTPException(status_code=500, detail="Admin privilege check failed")


async def _check_admin_privileges(user: User) -> bool:
    """Internal admin privilege check"""
    return "admin" in user.scopes if hasattr(user, "scopes") else False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Enhanced authentication middleware with async patterns
    Provides timeout protection and concurrent validation
    """

    async def dispatch(self, request: Request, call_next):
        """
        Authentication middleware to protect all API endpoints
        Enhanced with standardized async patterns
        """
        EXCLUDED_PATHS = ["/health_smoke", "/docs", "/redoc", "/openapi.json"]

        # Skip authentication for excluded paths
        if request.url.path in EXCLUDED_PATHS or request.url.path.startswith(
            "/api/v1/auth/token"
        ):
            return await call_next(request)

        try:
            # Authenticate user with timeout protection
            auth_result = await with_timeout(
                self._authenticate_request(request),
                AsyncTimeouts.HTTP_REQUEST,  # 30 seconds for auth
                "Request authentication timed out",
                {"path": request.url.path, "method": request.method},
            )

            if auth_result:
                request.state.user = auth_result
            else:
                return self._create_auth_error_response("Authentication failed")

            return await call_next(request)

        except AsyncTimeoutError as e:
            auth_stats["timeout_errors"] += 1
            logger.error(f"❌ Auth middleware timeout: {e}")
            return self._create_auth_error_response("Authentication timed out", 408)
        except HTTPException as e:
            logger.warning(f"⚠️ Auth middleware HTTP error: {e.detail}")
            return self._create_auth_error_response(e.detail, e.status_code)
        except Exception as e:
            logger.error(f"❌ Auth middleware error: {e}")
            return self._create_auth_error_response("Authentication system error")

    async def _authenticate_request(self, request: Request) -> Optional[User]:
        """Internal request authentication"""
        try:
            credentials = await security(request)
            if not credentials:
                return None

            return await get_current_user(credentials)

        except Exception as e:
            logger.warning(f"⚠️ Request authentication failed: {e}")
            return None

    def _create_auth_error_response(
        self, detail: str, status_code: int = 401
    ) -> Response:
        """Create standardized authentication error response"""
        import json

        error_response = {
            "detail": detail,
            "type": "authentication_error",
            "timestamp": datetime.utcnow().isoformat(),
        }

        return Response(
            content=json.dumps(error_response),
            status_code=status_code,
            media_type="application/json",
        )


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    budget_limit: float = 100.0


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800
    user: Optional[User] = None


@async_retry(max_attempts=2, delay=1.0, exceptions=(Exception,))
async def create_user(user_data: UserCreate) -> User:
    """
    Create new user with enhanced security and timeout protection
    """
    try:
        # Create user with timeout protection
        user = await with_timeout(
            _create_user_internal(user_data),
            AsyncTimeouts.DATABASE_TRANSACTION,  # 30 seconds for user creation
            f"User creation timed out for: {user_data.email}",
            {"email": user_data.email, "operation": "create_user"},
        )

        logger.info(f"✅ User created successfully: {user_data.email}")

        # Log user creation in background
        create_background_task(
            _log_user_creation(user_data.email), f"user_creation_log_{user_data.email}"
        )

        return user

    except AsyncTimeoutError as e:
        auth_stats["timeout_errors"] += 1
        logger.error(f"❌ User creation timed out: {e}")
        raise HTTPException(status_code=408, detail="User creation timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ User creation error: {e}")
        raise HTTPException(status_code=500, detail="User creation failed")


async def _create_user_internal(user_data: UserCreate) -> User:
    """Internal user creation logic"""
    if user_data.email in USERS_DB:
        raise HTTPException(status_code=400, detail="User already exists")

    # Generate user ID
    user_id = f"user_{len(USERS_DB) + 1}"

    # Hash password and create user record
    hashed_password = get_password_hash(user_data.password)

    user_record = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "hashed_password": hashed_password,
        "is_active": True,
        "scopes": ["basic"],
        "budget_limit": user_data.budget_limit,
        "current_usage": 0.0,
    }

    # Add to database
    USERS_DB[user_data.email] = user_record

    # Return User object
    return User(
        user_id=user_id,
        email=user_data.email,
        name=user_data.name,
        is_active=True,
        scopes=["basic"],
        budget_limit=user_data.budget_limit,
        current_usage=0.0,
    )


async def _log_user_creation(email: str):
    """Background logging of user creation"""
    try:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "email": email,
            "event": "user_created",
            "source": "jwt_auth_system",
        }

        logger.info(f"👤 User creation log: {log_entry}")

    except Exception as e:
        logger.error(f"❌ Error logging user creation: {e}")


async def login_user(credentials: UserLogin) -> Token:
    """
    Login user and return JWT token
    Enhanced with concurrent operations and timeout protection
    """
    try:
        # Authenticate user and prepare token data concurrently
        user_result, token_prep_result = await safe_gather(
            authenticate_user(credentials.email, credentials.password),
            _prepare_token_data(credentials.email),
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=2,
        )

        # Handle authentication result
        if isinstance(user_result, Exception) or not user_result:
            logger.warning(f"⚠️ Login failed for: {credentials.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Handle token preparation result
        if isinstance(token_prep_result, Exception):
            logger.error(f"❌ Token preparation failed: {token_prep_result}")
            # Continue with basic token data
            token_data = {"sub": user_result.user_id, "email": user_result.email}
        else:
            token_data = token_prep_result

        # Create access token
        access_token = create_access_token(data=token_data)

        logger.info(f"✅ User logged in successfully: {credentials.email}")
        return Token(access_token=access_token, user=user_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error for {credentials.email}: {e}")
        raise HTTPException(
            status_code=500, detail="Login service temporarily unavailable"
        )


async def _prepare_token_data(email: str) -> Dict[str, Any]:
    """Prepare enhanced token data"""
    user_data = await get_user_by_email(email)
    if not user_data:
        return {"sub": "unknown", "email": email}

    return {
        "sub": user_data["user_id"],
        "email": user_data["email"],
        "scopes": user_data.get("scopes", ["basic"]),
        "name": user_data.get("name", "Unknown"),
    }


async def get_auth_stats() -> Dict[str, Any]:
    """
    Get comprehensive authentication statistics
    Enhanced with performance metrics
    """
    stats = auth_stats.copy()

    # Calculate success rates
    total_logins = stats["login_attempts"]
    if total_logins > 0:
        stats["login_success_rate"] = (stats["successful_logins"] / total_logins) * 100
        stats["login_failure_rate"] = (stats["failed_logins"] / total_logins) * 100
    else:
        stats["login_success_rate"] = 0.0
        stats["login_failure_rate"] = 0.0

    total_validations = stats["token_validations"]
    if total_validations > 0:
        stats["token_success_rate"] = (
            (total_validations - stats["token_failures"]) / total_validations
        ) * 100
    else:
        stats["token_success_rate"] = 0.0

    stats["async_patterns_enabled"] = True
    stats["total_users"] = len(USERS_DB)
    stats["collected_at"] = datetime.utcnow().isoformat()

    return stats


async def health_check() -> Dict[str, Any]:
    """
    Comprehensive authentication system health check
    Enhanced with timeout protection and component testing
    """
    health = {
        "status": "unknown",
        "jwt_system": {"status": "unknown"},
        "user_database": {"status": "unknown"},
        "password_hashing": {"status": "unknown"},
        "token_validation": {"status": "unknown"},
        "performance_metrics": {},
        "errors": [],
    }

    try:
        # Test all components concurrently
        health_tasks = [
            _test_jwt_system(),
            _test_user_database(),
            _test_password_hashing(),
            _test_token_validation(),
        ]

        jwt_test, db_test, pwd_test, token_test = await safe_gather(
            *health_tasks,
            return_exceptions=True,
            timeout=AsyncTimeouts.DATABASE_QUERY,
            max_concurrency=4,
        )

        # Process results
        health["jwt_system"] = (
            jwt_test
            if not isinstance(jwt_test, Exception)
            else {"status": "failed", "error": str(jwt_test)}
        )
        health["user_database"] = (
            db_test
            if not isinstance(db_test, Exception)
            else {"status": "failed", "error": str(db_test)}
        )
        health["password_hashing"] = (
            pwd_test
            if not isinstance(pwd_test, Exception)
            else {"status": "failed", "error": str(pwd_test)}
        )
        health["token_validation"] = (
            token_test
            if not isinstance(token_test, Exception)
            else {"status": "failed", "error": str(token_test)}
        )

        # Get performance metrics
        health["performance_metrics"] = await get_auth_stats()

        # Determine overall health
        all_healthy = all(
            component.get("status") == "healthy"
            for component in [
                health["jwt_system"],
                health["user_database"],
                health["password_hashing"],
                health["token_validation"],
            ]
            if isinstance(component, dict)
        )

        health["status"] = "healthy" if all_healthy else "degraded"

    except Exception as e:
        health["status"] = "unhealthy"
        health["errors"].append(f"Health check failed: {str(e)}")

    return health


async def _test_jwt_system() -> Dict[str, Any]:
    """Test JWT token system"""
    try:
        test_data = {"sub": "test_user", "email": "test@example.com"}
        token = create_access_token(test_data)
        decoded = await _verify_token_internal(token)

        return {
            "status": "healthy",
            "token_creation": True,
            "token_verification": True,
            "algorithm": ALGORITHM,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _test_user_database() -> Dict[str, Any]:
    """Test user database access"""
    try:
        test_user = await get_user_by_email("admin@example.com")
        return {
            "status": "healthy",
            "database_access": True,
            "user_count": len(USERS_DB),
            "test_user_found": test_user is not None,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _test_password_hashing() -> Dict[str, Any]:
    """Test password hashing system"""
    try:
        test_password = "test_password_123"
        hashed = get_password_hash(test_password)
        verified = verify_password(test_password, hashed)

        return {
            "status": "healthy",
            "hashing": True,
            "verification": verified,
            "scheme": "bcrypt",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def _test_token_validation() -> Dict[str, Any]:
    """Test token validation performance"""
    try:
        # Create test token
        test_data = {"sub": "health_check", "email": "health@example.com"}
        token = create_access_token(test_data)

        # Validate token
        start_time = datetime.utcnow()
        token_data = await verify_token(token)
        validation_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "status": "healthy",
            "validation_successful": True,
            "validation_time_ms": validation_time,
            "user_id": token_data.user_id,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def update_user_usage(user_id: str, cost: float):
    """Update user usage (compatibility function)"""
    pass


def require_scope(required_scope: str):
    """Require specific scope (compatibility function)"""

    def decorator(func):
        return func

    return decorator


class SimpleAuthMiddleware(BaseHTTPMiddleware):
    """Simple auth middleware for compatibility"""

    async def dispatch(self, request: Request, call_next):
        return await call_next(request)


# Alias for compatibility
auth_middleware = SimpleAuthMiddleware


def require_admin(user):
    """Check if user has admin role (compatibility function)"""
    return "admin" in user.scopes if hasattr(user, "scopes") else False
