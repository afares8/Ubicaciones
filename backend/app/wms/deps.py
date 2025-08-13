from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from typing import Optional
import jwt
import os
from enum import Enum

security = HTTPBearer()

class UserRole(str, Enum):
    ADMIN = "Admin"
    WAREHOUSE_MANAGER = "WarehouseManager"
    OPERATOR = "Operator"
    AUDITOR = "Auditor"

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALG", "HS256")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        roles = payload.get("roles", [])
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "username": username,
            "roles": roles
        }
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_role: UserRole):
    """Dependency factory for role-based access control"""
    def role_checker(current_user: dict = Depends(get_current_user)):
        if required_role.value not in current_user["roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def get_db_session() -> Session:
    """Get database session dependency"""
    return Depends(get_db)

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Optional authentication for endpoints that work with or without auth"""
    if not credentials:
        return None
    return get_current_user(credentials)
