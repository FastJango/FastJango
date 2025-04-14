"""
FastAPI dependencies for FastJango.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from fastjango.core.logging import Logger

logger = Logger("fastjango.core.dependencies")

# Create OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    """
    Get the current authenticated user.
    
    Args:
        token: The authentication token
        
    Returns:
        The current user or None
        
    Raises:
        HTTPException: If authentication fails
    """
    if not token:
        # Allow anonymous access by default
        return None
    
    try:
        # This is a placeholder for actual auth logic
        # In a real implementation, you would:
        # 1. Verify the token
        # 2. Extract user ID
        # 3. Fetch user from database
        
        # Simple placeholder implementation
        user = {"id": 1, "username": "demo", "email": "demo@example.com"}
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_required_user(user: Optional[dict] = Depends(get_current_user)):
    """
    Get the current authenticated user, requiring authentication.
    
    Args:
        user: The current user from get_current_user
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If no authenticated user
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user 