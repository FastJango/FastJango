"""
FastJango Pagination - Django-like pagination with FastAPI features.

This module provides pagination for FastJango, similar to Django DRF
pagination but adapted for FastAPI with modern features.
"""

from .pagination import (
    BasePagination, PageNumberPagination, LimitOffsetPagination,
    CursorPagination, PaginationResponse, PaginationParams,
    get_page_number_pagination, get_limit_offset_pagination, get_cursor_pagination
)
from .fastapi_pagination import (
    FastAPIPagination, FastAPIPageNumberPagination,
    FastAPILimitOffsetPagination, FastAPICursorPagination,
    get_fastapi_page_pagination, get_fastapi_limit_offset_pagination, get_fastapi_cursor_pagination
)
from .django_like import (
    DjangoLikePagination, DjangoLikePageNumberPagination,
    DjangoLikeLimitOffsetPagination, DjangoLikeCursorPagination,
    get_django_page_pagination, get_django_limit_offset_pagination, get_django_cursor_pagination
)

__all__ = [
    # Base pagination
    'BasePagination',
    'PageNumberPagination', 
    'LimitOffsetPagination',
    'CursorPagination',
    'PaginationResponse',
    'PaginationParams',
    'get_page_number_pagination',
    'get_limit_offset_pagination',
    'get_cursor_pagination',
    
    # FastAPI pagination
    'FastAPIPagination',
    'FastAPIPageNumberPagination',
    'FastAPILimitOffsetPagination', 
    'FastAPICursorPagination',
    'get_fastapi_page_pagination',
    'get_fastapi_limit_offset_pagination',
    'get_fastapi_cursor_pagination',
    
    # Django-like pagination
    'DjangoLikePagination',
    'DjangoLikePageNumberPagination',
    'DjangoLikeLimitOffsetPagination',
    'DjangoLikeCursorPagination',
    'get_django_page_pagination',
    'get_django_limit_offset_pagination',
    'get_django_cursor_pagination',
]