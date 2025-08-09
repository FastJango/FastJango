#!/usr/bin/env python3
"""
Test FastJango Pagination and CORS Features

This script demonstrates the pagination and CORS features implemented in FastJango,
showing how to use Django-like settings with ALLOWED_HOSTS and CORS configuration.
"""

import os
import sys
import asyncio
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Request, Depends, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

# Import FastJango components
from fastjango.core.settings import FastJangoSettings, configure_settings, get_settings_instance
from fastjango.pagination import (
    PageNumberPagination, LimitOffsetPagination, CursorPagination,
    FastAPIPageNumberPagination, FastAPILimitOffsetPagination, FastAPICursorPagination,
    DjangoLikePageNumberPagination, DjangoLikeLimitOffsetPagination, DjangoLikeCursorPagination,
    get_page_number_pagination, get_limit_offset_pagination, get_cursor_pagination,
    get_fastapi_page_pagination, get_fastapi_limit_offset_pagination, get_fastapi_cursor_pagination,
    get_django_page_pagination, get_django_limit_offset_pagination, get_django_cursor_pagination
)


# Sample data model
@dataclass
class Product:
    id: int
    name: str
    price: float
    category: str
    created_at: datetime
    is_active: bool


# Generate sample products
def generate_sample_products(count: int = 100) -> List[Product]:
    """Generate sample product data."""
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']
    products = []
    
    for i in range(1, count + 1):
        product = Product(
            id=i,
            name=f"Product {i}",
            price=round(10.0 + (i * 0.5), 2),
            category=categories[i % len(categories)],
            created_at=datetime.now(),
            is_active=i % 3 != 0  # Some products inactive
        )
        products.append(product)
    
    return products


# Configure FastJango settings
settings_dict = {
    'DEBUG': True,
    'ALLOWED_HOSTS': ['localhost', '127.0.0.1', '0.0.0.0', 'test.example.com'],
    'CORS_ALLOWED_ORIGINS': [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8080',
        'https://test.example.com'
    ],
    'CORS_ALLOWED_ORIGIN_REGEXES': [
        r'^https://\w+\.example\.com$',
        r'^http://localhost:\d+$'
    ],
    'CORS_ALLOWED_METHODS': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    'CORS_ALLOWED_HEADERS': [
        'accept', 'accept-encoding', 'authorization', 'content-type',
        'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
    ],
    'CORS_EXPOSED_HEADERS': ['content-type', 'content-length', 'x-total-count'],
    'CORS_ALLOW_CREDENTIALS': True,
    'CORS_MAX_AGE': 86400,
    'CORS_ALLOW_ALL_ORIGINS': False,
    'CORS_ALLOW_ALL_METHODS': False,
    'CORS_ALLOW_ALL_HEADERS': False,
    'PAGINATION_PAGE_SIZE': 10,
    'PAGINATION_MAX_PAGE_SIZE': 50,
    'API_PAGINATION_CLASS': 'fastjango.pagination.PageNumberPagination',
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_FRAME_DENY': True,
}

configure_settings(settings_dict)

# Sample data
SAMPLE_PRODUCTS = generate_sample_products(100)

# Create FastAPI app
app = FastAPI(
    title="FastJango Pagination & CORS Test",
    description="Testing pagination and CORS features",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_dict['CORS_ALLOWED_ORIGINS'],
    allow_credentials=settings_dict['CORS_ALLOW_CREDENTIALS'],
    allow_methods=settings_dict['CORS_ALLOWED_METHODS'],
    allow_headers=settings_dict['CORS_ALLOWED_HEADERS'],
    expose_headers=settings_dict['CORS_EXPOSED_HEADERS'],
    max_age=settings_dict['CORS_MAX_AGE'],
)


# Helper function to convert products to dict
def products_to_dict(products: List[Product]) -> List[Dict[str, Any]]:
    """Convert products to dictionary format."""
    return [asdict(product) for product in products]


# Basic pagination endpoints
@app.get("/products/page")
async def get_products_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_page_number_pagination)
):
    """Get products with page number pagination."""
    paginator = PageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


@app.get("/products/limit-offset")
async def get_products_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_limit_offset_pagination)
):
    """Get products with limit/offset pagination."""
    paginator = LimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


@app.get("/products/cursor")
async def get_products_cursor(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_cursor_pagination)
):
    """Get products with cursor pagination."""
    paginator = CursorPagination(page_size=10, ordering="-id")
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


# FastAPI pagination endpoints
@app.get("/products/fastapi-page")
async def get_products_fastapi_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_fastapi_page_pagination)
):
    """Get products with FastAPI page number pagination."""
    paginator = FastAPIPageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


@app.get("/products/fastapi-limit-offset")
async def get_products_fastapi_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_fastapi_limit_offset_pagination)
):
    """Get products with FastAPI limit/offset pagination."""
    paginator = FastAPILimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


# Django-like pagination endpoints
@app.get("/products/django-page")
async def get_products_django_page(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_django_page_pagination)
):
    """Get products with Django-like page number pagination."""
    paginator = DjangoLikePageNumberPagination(page_size=10)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


@app.get("/products/django-limit-offset")
async def get_products_django_limit_offset(
    request: Request,
    pagination: Dict[str, Any] = Depends(get_django_limit_offset_pagination)
):
    """Get products with Django-like limit/offset pagination."""
    paginator = DjangoLikeLimitOffsetPagination(default_limit=10, max_limit=50)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(SAMPLE_PRODUCTS, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(SAMPLE_PRODUCTS), 
        request
    )
    
    return JSONResponse(content=response.dict())


# Advanced pagination with filtering and ordering
@app.get("/products/advanced")
async def get_products_advanced(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
    search: str = Query(None, description="Search term"),
    category: str = Query(None, description="Filter by category"),
    ordering: str = Query("name", description="Ordering field"),
    is_active: bool = Query(None, description="Filter by active status"),
    min_price: float = Query(None, description="Minimum price"),
    max_price: float = Query(None, description="Maximum price")
):
    """Get products with advanced pagination, filtering, and ordering."""
    # Filter products
    filtered_products = SAMPLE_PRODUCTS.copy()
    
    if search:
        filtered_products = [p for p in filtered_products if search.lower() in p.name.lower()]
    
    if category:
        filtered_products = [p for p in filtered_products if p.category.lower() == category.lower()]
    
    if is_active is not None:
        filtered_products = [p for p in filtered_products if p.is_active == is_active]
    
    if min_price is not None:
        filtered_products = [p for p in filtered_products if p.price >= min_price]
    
    if max_price is not None:
        filtered_products = [p for p in filtered_products if p.price <= max_price]
    
    # Apply ordering
    reverse = ordering.startswith('-')
    sort_key = ordering[1:] if reverse else ordering
    
    try:
        filtered_products.sort(key=lambda x: getattr(x, sort_key, x.name), reverse=reverse)
    except (AttributeError, TypeError):
        # Fallback to name sorting
        filtered_products.sort(key=lambda x: x.name)
    
    # Apply pagination
    paginator = PageNumberPagination(page_size=page_size)
    
    # Get paginated data
    paginated_products = paginator.paginate_queryset(filtered_products, request)
    
    # Get paginated response
    response = paginator.get_paginated_response(
        products_to_dict(paginated_products), 
        len(filtered_products), 
        request
    )
    
    return JSONResponse(content=response.dict())


# Settings endpoint
@app.get("/settings")
async def get_settings():
    """Get current settings."""
    settings = get_settings_instance()
    
    return JSONResponse(content={
        'DEBUG': settings.DEBUG,
        'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
        'CORS_ALLOWED_ORIGINS': settings.CORS_ALLOWED_ORIGINS,
        'CORS_ALLOWED_ORIGIN_REGEXES': settings.CORS_ALLOWED_ORIGIN_REGEXES,
        'CORS_ALLOWED_METHODS': settings.CORS_ALLOWED_METHODS,
        'CORS_ALLOWED_HEADERS': settings.CORS_ALLOWED_HEADERS,
        'CORS_EXPOSED_HEADERS': settings.CORS_EXPOSED_HEADERS,
        'CORS_ALLOW_CREDENTIALS': settings.CORS_ALLOW_CREDENTIALS,
        'CORS_MAX_AGE': settings.CORS_MAX_AGE,
        'PAGINATION_PAGE_SIZE': settings.PAGINATION_PAGE_SIZE,
        'PAGINATION_MAX_PAGE_SIZE': settings.PAGINATION_MAX_PAGE_SIZE,
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "features": {
            "pagination": "enabled",
            "cors": "enabled",
            "settings": "enabled"
        }
    })


# Test function
def test_pagination_and_cors():
    """Test pagination and CORS features."""
    print("🧪 Testing FastJango Pagination and CORS Features")
    print("=" * 60)
    
    # Create test client
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test settings endpoint
    print("\n2. Testing settings endpoint...")
    response = client.get("/settings")
    print(f"   Status: {response.status_code}")
    settings = response.json()
    print(f"   ALLOWED_HOSTS: {settings['ALLOWED_HOSTS']}")
    print(f"   CORS_ALLOWED_ORIGINS: {settings['CORS_ALLOWED_ORIGINS']}")
    
    # Test page number pagination
    print("\n3. Testing page number pagination...")
    response = client.get("/products/page?page=1&page_size=5")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Page: {data['page']}")
    print(f"   Page Size: {data['page_size']}")
    print(f"   Total Pages: {data['total_pages']}")
    print(f"   Results Count: {len(data['results'])}")
    
    # Test limit/offset pagination
    print("\n4. Testing limit/offset pagination...")
    response = client.get("/products/limit-offset?limit=5&offset=10")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Results Count: {len(data['results'])}")
    print(f"   Has Next: {data['has_next']}")
    print(f"   Has Previous: {data['has_previous']}")
    
    # Test cursor pagination
    print("\n5. Testing cursor pagination...")
    response = client.get("/products/cursor?cursor=50")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Results Count: {len(data['results'])}")
    print(f"   Has Next: {data['has_next']}")
    
    # Test FastAPI pagination
    print("\n6. Testing FastAPI pagination...")
    response = client.get("/products/fastapi-page?page=2&page_size=3")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Page: {data['page']}")
    print(f"   Results Count: {len(data['results'])}")
    
    # Test Django-like pagination
    print("\n7. Testing Django-like pagination...")
    response = client.get("/products/django-page?page=1&page_size=4&ordering=price")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Page: {data['page']}")
    print(f"   Results Count: {len(data['results'])}")
    
    # Test advanced pagination with filtering
    print("\n8. Testing advanced pagination with filtering...")
    response = client.get("/products/advanced?page=1&page_size=5&search=product&category=Electronics&min_price=10&max_price=20&ordering=-price")
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    print(f"   Page: {data['page']}")
    print(f"   Results Count: {len(data['results'])}")
    
    # Test CORS headers
    print("\n9. Testing CORS headers...")
    response = client.get("/products/page", headers={"Origin": "http://localhost:3000"})
    print(f"   Status: {response.status_code}")
    cors_headers = {k: v for k, v in response.headers.items() if k.startswith('Access-Control')}
    print(f"   CORS Headers: {cors_headers}")
    
    # Test CORS preflight
    print("\n10. Testing CORS preflight...")
    response = client.options("/products/page", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type"
    })
    print(f"   Status: {response.status_code}")
    cors_headers = {k: v for k, v in response.headers.items() if k.startswith('Access-Control')}
    print(f"   CORS Headers: {cors_headers}")
    
    print("\n✅ All tests completed successfully!")
    print("\n📋 Available endpoints:")
    print("   - GET /health - Health check")
    print("   - GET /settings - Current settings")
    print("   - GET /products/page - Page number pagination")
    print("   - GET /products/limit-offset - Limit/offset pagination")
    print("   - GET /products/cursor - Cursor pagination")
    print("   - GET /products/fastapi-page - FastAPI page pagination")
    print("   - GET /products/fastapi-limit-offset - FastAPI limit/offset pagination")
    print("   - GET /products/django-page - Django-like page pagination")
    print("   - GET /products/django-limit-offset - Django-like limit/offset pagination")
    print("   - GET /products/advanced - Advanced pagination with filtering")


if __name__ == "__main__":
    print("🚀 FastJango Pagination and CORS Test")
    print("=" * 50)
    
    # Run tests
    test_pagination_and_cors()
    
    print("\n🎉 Test completed! You can also run the server with:")
    print("   uvicorn test_pagination_and_cors:app --reload --host 0.0.0.0 --port 8000")
