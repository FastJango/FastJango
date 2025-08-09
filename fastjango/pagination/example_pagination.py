"""
FastJango Pagination Example - Demonstrating pagination features.

This example shows how to use FastJango pagination with FastAPI,
including different pagination types and Django-like settings.
"""

import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Add the parent directory to the path to import fastjango
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import JSONResponse

from fastjango.core.settings import FastJangoSettings, configure_settings
from fastjango.pagination import (
    PageNumberPagination, LimitOffsetPagination, CursorPagination,
    FastAPIPageNumberPagination, FastAPILimitOffsetPagination, FastAPICursorPagination,
    DjangoLikePageNumberPagination, DjangoLikeLimitOffsetPagination, DjangoLikeCursorPagination,
    get_page_number_pagination, get_limit_offset_pagination, get_cursor_pagination,
    get_fastapi_page_pagination, get_fastapi_limit_offset_pagination, get_fastapi_cursor_pagination,
    get_django_page_pagination, get_django_limit_offset_pagination, get_django_cursor_pagination
)


# Sample data
@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool


# Generate sample users
def generate_sample_users(count: int = 100) -> List[User]:
    """Generate sample user data."""
    users = []
    for i in range(1, count + 1):
        user = User(
            id=i,
            name=f"User {i}",
            email=f"user{i}@example.com",
            created_at=datetime.now(),
            is_active=i % 2 == 0
        )
        users.append(user)
    return users


# Sample data
SAMPLE_USERS = generate_sample_users(100)


# Configure settings
settings_dict = {
    'DEBUG': True,
    'ALLOWED_HOSTS': ['localhost', '127.0.0.1', '*'],
    'CORS_ALLOWED_ORIGINS': ['http://localhost:3000', 'http://127.0.0.1:3000'],
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'PAGINATION_PAGE_SIZE': 10,
    'PAGINATION_MAX_PAGE_SIZE': 50,
    'API_PAGINATION_CLASS': 'fastjango.pagination.PageNumberPagination',
}

configure_settings(settings_dict)


# Create FastAPI app
app = FastAPI(
    title="FastJango Pagination Example",
    description="Demonstrating pagination features with FastAPI",
    version="1.0.0"
)


# Basic pagination endpoints
@app.get("/users/page")
async def get_users_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_page_number_pagination)
):
    """Get users with page number pagination."""
    paginator = PageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/limit-offset")
async def get_users_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_limit_offset_pagination)
):
    """Get users with limit/offset pagination."""
    paginator = LimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/cursor")
async def get_users_cursor(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_cursor_pagination)
):
    """Get users with cursor pagination."""
    paginator = CursorPagination(page_size=10, ordering="-id")
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


# FastAPI pagination endpoints
@app.get("/users/fastapi-page")
async def get_users_fastapi_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_fastapi_page_pagination)
):
    """Get users with FastAPI page number pagination."""
    paginator = FastAPIPageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/fastapi-limit-offset")
async def get_users_fastapi_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_fastapi_limit_offset_pagination)
):
    """Get users with FastAPI limit/offset pagination."""
    paginator = FastAPILimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/fastapi-cursor")
async def get_users_fastapi_cursor(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_fastapi_cursor_pagination)
):
    """Get users with FastAPI cursor pagination."""
    paginator = FastAPICursorPagination(page_size=10, ordering="-id")
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


# Django-like pagination endpoints
@app.get("/users/django-page")
async def get_users_django_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_django_page_pagination)
):
    """Get users with Django-like page number pagination."""
    paginator = DjangoLikePageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/django-limit-offset")
async def get_users_django_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_django_limit_offset_pagination)
):
    """Get users with Django-like limit/offset pagination."""
    paginator = DjangoLikeLimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


@app.get("/users/django-cursor")
async def get_users_django_cursor(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_django_cursor_pagination)
):
    """Get users with Django-like cursor pagination."""
    paginator = DjangoLikeCursorPagination(page_size=10, ordering="-id")
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(SAMPLE_USERS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(SAMPLE_USERS), request)
    
    return JSONResponse(content=response.dict())


# Advanced pagination with filtering and ordering
@app.get("/users/advanced")
async def get_users_advanced(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    search: str = Query(None, description="Search term"),
    ordering: str = Query("name", description="Ordering field"),
    is_active: bool = Query(None, description="Filter by active status")
):
    """Get users with advanced pagination, filtering, and ordering."""
    # Filter users
    filtered_users = SAMPLE_USERS.copy()
    
    if search:
        filtered_users = [u for u in filtered_users if search.lower() in u.name.lower()]
    
    if is_active is not None:
        filtered_users = [u for u in filtered_users if u.is_active == is_active]
    
    # Apply ordering
    reverse = ordering.startswith('-')
    sort_key = ordering[1:] if reverse else ordering
    
    try:
        filtered_users.sort(key=lambda x: getattr(x, sort_key, x.name), reverse=reverse)
    except (AttributeError, TypeError):
        # Fallback to name sorting
        filtered_users.sort(key=lambda x: x.name)
    
    # Apply pagination
    paginator = PageNumberPagination(page_size=page_size)
    
    # Get paginated data
    paginated_users = paginator.paginate_queryset(filtered_users, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(paginated_users, len(filtered_users), request)
    
    return JSONResponse(content=response.dict())


# Settings endpoint
@app.get("/settings")
async def get_settings():
    """Get current settings."""
    from fastjango.core.settings import get_settings_instance
    settings = get_settings_instance()
    
    return JSONResponse(content={
        'DEBUG': settings.DEBUG,
        'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
        'CORS_ALLOWED_ORIGINS': settings.CORS_ALLOWED_ORIGINS,
        'PAGINATION_PAGE_SIZE': settings.PAGINATION_PAGE_SIZE,
        'PAGINATION_MAX_PAGE_SIZE': settings.PAGINATION_MAX_PAGE_SIZE,
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    import uvicorn
    
    print("Starting FastJango Pagination Example...")
    print("Available endpoints:")
    print("  - GET /users/page - Page number pagination")
    print("  - GET /users/limit-offset - Limit/offset pagination")
    print("  - GET /users/cursor - Cursor pagination")
    print("  - GET /users/fastapi-page - FastAPI page number pagination")
    print("  - GET /users/fastapi-limit-offset - FastAPI limit/offset pagination")
    print("  - GET /users/fastapi-cursor - FastAPI cursor pagination")
    print("  - GET /users/django-page - Django-like page number pagination")
    print("  - GET /users/django-limit-offset - Django-like limit/offset pagination")
    print("  - GET /users/django-cursor - Django-like cursor pagination")
    print("  - GET /users/advanced - Advanced pagination with filtering")
    print("  - GET /settings - Current settings")
    print("  - GET /health - Health check")
    print("\nExample requests:")
    print("  - http://localhost:8000/users/page?page=1&page_size=5")
    print("  - http://localhost:8000/users/limit-offset?limit=10&offset=20")
    print("  - http://localhost:8000/users/cursor?cursor=50")
    print("  - http://localhost:8000/users/advanced?page=1&page_size=5&search=user&ordering=-id&is_active=true")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
