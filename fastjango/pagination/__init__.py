"""
FastJango Pagination - Django-like pagination with FastAPI features.

This module provides pagination for FastJango, similar to Django DRF
pagination but adapted for FastAPI with modern features.
"""

from .pagination import (
    BasePagination, PageNumberPagination, LimitOffsetPagination,
    CursorPagination, PaginationResponse, PaginationParams
)
from .fastapi_pagination import (
    FastAPIPagination, FastAPIPageNumberPagination,
    FastAPILimitOffsetPagination, FastAPICursorPagination
)
from .django_like import (
    DjangoLikePagination, DjangoLikePageNumberPagination,
    DjangoLikeLimitOffsetPagination, DjangoLikeCursorPagination
)

__all__ = [
    # Base pagination
    'BasePagination',
    'PageNumberPagination', 
    'LimitOffsetPagination',
    'CursorPagination',
    'PaginationResponse',
    'PaginationParams',
    
    # FastAPI pagination
    'FastAPIPagination',
    'FastAPIPageNumberPagination',
    'FastAPILimitOffsetPagination', 
    'FastAPICursorPagination',
    
    # Django-like pagination
    'DjangoLikePagination',
    'DjangoLikePageNumberPagination',
    'DjangoLikeLimitOffsetPagination',
    'DjangoLikeCursorPagination',
]