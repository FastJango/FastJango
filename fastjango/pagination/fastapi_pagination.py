"""
FastJango FastAPI Pagination - Modern FastAPI pagination features.

This module provides FastAPI-specific pagination features with modern
FastAPI integration, dependency injection, and OpenAPI documentation.
"""

from typing import List, Dict, Any, Optional, Generic, TypeVar, Union
from fastapi import Request, Query, Depends, HTTPException
from pydantic import BaseModel, Field
from math import ceil

from .pagination import BasePagination, PaginationResponse, PaginationParams


T = TypeVar('T')


class FastAPIPagination(BasePagination):
    """FastAPI-specific pagination with modern features."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size",
                 include_total: bool = True,
                 include_links: bool = True):
        """Initialize FastAPI pagination."""
        super().__init__(page_size, max_page_size, page_query_param, page_size_query_param)
        self.include_total = include_total
        self.include_links = include_links
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get pagination parameters from request."""
        page = self.get_page_number(request)
        page_size = self.get_page_size(request)
        
        return PaginationParams(page=page, page_size=page_size)
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset."""
        params = self.get_pagination_params(request)
        start = (params.page - 1) * params.page_size
        end = start + params.page_size
        
        return queryset[start:end]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response with FastAPI features."""
        params = self.get_pagination_params(request)
        
        total_pages = ceil(count / params.page_size) if count > 0 else 0
        has_next = params.page < total_pages
        has_previous = params.page > 1
        
        # Build pagination links
        next_url = None
        previous_url = None
        
        if self.include_links:
            base_url = str(request.url)
            
            if has_next:
                next_url = self._build_url(base_url, {self.page_query_param: params.page + 1})
            
            if has_previous:
                previous_url = self._build_url(base_url, {self.page_query_param: params.page - 1})
        
        return PaginationResponse(
            count=count if self.include_total else None,
            next=next_url,
            previous=previous_url,
            results=data,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages if self.include_total else None,
            has_next=has_next,
            has_previous=has_previous
        )


class FastAPIPageNumberPagination(FastAPIPagination):
    """FastAPI page number pagination with enhanced features."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size"):
        """Initialize FastAPI page number pagination."""
        super().__init__(page_size, max_page_size, page_query_param, page_size_query_param)
    
    def validate_page(self, page: int) -> int:
        """Validate page number."""
        if page < 1:
            raise HTTPException(status_code=400, detail="Page number must be greater than 0")
        return page
    
    def get_page_number(self, request: Request) -> int:
        """Get and validate page number from request."""
        try:
            page = int(request.query_params.get(self.page_query_param, 1))
            return self.validate_page(page)
        except (ValueError, TypeError):
            return 1


class FastAPILimitOffsetPagination(FastAPIPagination):
    """FastAPI limit/offset pagination with enhanced features."""
    
    def __init__(self, 
                 default_limit: int = 20,
                 max_limit: int = 100,
                 limit_query_param: str = "limit",
                 offset_query_param: str = "offset"):
        """Initialize FastAPI limit/offset pagination."""
        super().__init__(default_limit, max_limit)
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.limit_query_param = limit_query_param
        self.offset_query_param = offset_query_param
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get limit/offset pagination parameters."""
        limit = self.get_limit(request)
        offset = self.get_offset(request)
        
        return PaginationParams(limit=limit, offset=offset)
    
    def get_limit(self, request: Request) -> int:
        """Get and validate limit from request."""
        try:
            limit = int(request.query_params.get(self.limit_query_param, self.default_limit))
            if limit < 1:
                raise HTTPException(status_code=400, detail="Limit must be greater than 0")
            return min(limit, self.max_limit)
        except (ValueError, TypeError):
            return self.default_limit
    
    def get_offset(self, request: Request) -> int:
        """Get and validate offset from request."""
        try:
            offset = int(request.query_params.get(self.offset_query_param, 0))
            if offset < 0:
                raise HTTPException(status_code=400, detail="Offset must be non-negative")
            return offset
        except (ValueError, TypeError):
            return 0
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset using limit/offset."""
        params = self.get_pagination_params(request)
        return queryset[params.offset:params.offset + params.limit]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response for limit/offset."""
        params = self.get_pagination_params(request)
        
        has_next = params.offset + params.limit < count
        has_previous = params.offset > 0
        
        # Build pagination links
        next_url = None
        previous_url = None
        
        if self.include_links:
            base_url = str(request.url)
            
            if has_next:
                next_url = self._build_url(base_url, {
                    self.limit_query_param: params.limit,
                    self.offset_query_param: params.offset + params.limit
                })
            
            if has_previous:
                previous_url = self._build_url(base_url, {
                    self.limit_query_param: params.limit,
                    self.offset_query_param: max(0, params.offset - params.limit)
                })
        
        return PaginationResponse(
            count=count if self.include_total else None,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=params.limit,
            has_next=has_next,
            has_previous=has_previous
        )


class FastAPICursorPagination(FastAPIPagination):
    """FastAPI cursor-based pagination with enhanced features."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 cursor_query_param: str = "cursor",
                 ordering: str = "-id"):
        """Initialize FastAPI cursor pagination."""
        super().__init__(page_size, max_page_size)
        self.cursor_query_param = cursor_query_param
        self.ordering = ordering
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get cursor pagination parameters."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        return PaginationParams(cursor=cursor, page_size=page_size)
    
    def get_cursor(self, request: Request) -> Optional[str]:
        """Get cursor from request."""
        return request.query_params.get(self.cursor_query_param)
    
    def validate_cursor(self, cursor: str) -> bool:
        """Validate cursor format."""
        # Add cursor validation logic here
        return True
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset using cursor."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        # Sort queryset by ordering
        reverse = self.ordering.startswith('-')
        sort_key = self.ordering[1:] if reverse else self.ordering
        
        # Sort the queryset
        sorted_queryset = sorted(queryset, key=lambda x: getattr(x, sort_key, 0), reverse=reverse)
        
        if cursor and self.validate_cursor(cursor):
            # Find position after cursor
            try:
                cursor_value = int(cursor)
                # Find items after cursor
                filtered_queryset = []
                found_cursor = False
                
                for item in sorted_queryset:
                    item_value = getattr(item, sort_key, 0)
                    if found_cursor:
                        filtered_queryset.append(item)
                    elif item_value == cursor_value:
                        found_cursor = True
                
                return filtered_queryset[:page_size]
            except (ValueError, TypeError):
                return sorted_queryset[:page_size]
        else:
            return sorted_queryset[:page_size]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response for cursor pagination."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        has_next = len(data) == page_size
        has_previous = cursor is not None
        
        # Build pagination links
        next_url = None
        previous_url = None
        
        if self.include_links and has_next and data:
            base_url = str(request.url)
            last_item = data[-1]
            sort_key = self.ordering[1:] if self.ordering.startswith('-') else self.ordering
            next_cursor = getattr(last_item, sort_key, last_item.id)
            next_url = self._build_url(base_url, {self.cursor_query_param: str(next_cursor)})
        
        return PaginationResponse(
            count=count if self.include_total else None,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )


# FastAPI dependency functions with enhanced validation
def get_fastapi_page_pagination(
    page: int = Query(1, ge=1, description="Page number", example=1),
    page_size: int = Query(20, ge=1, le=100, description="Items per page", example=20)
) -> PaginationParams:
    """Get FastAPI page number pagination parameters with validation."""
    return PaginationParams(page=page, page_size=page_size)


def get_fastapi_limit_offset_pagination(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return", example=20),
    offset: int = Query(0, ge=0, description="Number of items to skip", example=0)
) -> PaginationParams:
    """Get FastAPI limit/offset pagination parameters with validation."""
    return PaginationParams(limit=limit, offset=offset)


def get_fastapi_cursor_pagination(
    cursor: Optional[str] = Query(None, description="Cursor for pagination", example="123")
) -> PaginationParams:
    """Get FastAPI cursor pagination parameters with validation."""
    return PaginationParams(cursor=cursor)


# Pagination decorators for easy use
def paginate_with_page_number(pagination_class: type = FastAPIPageNumberPagination):
    """Decorator for page number pagination."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add pagination logic here
            return func(*args, **kwargs)
        return wrapper
    return decorator


def paginate_with_limit_offset(pagination_class: type = FastAPILimitOffsetPagination):
    """Decorator for limit/offset pagination."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add pagination logic here
            return func(*args, **kwargs)
        return wrapper
    return decorator


def paginate_with_cursor(pagination_class: type = FastAPICursorPagination):
    """Decorator for cursor pagination."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add pagination logic here
            return func(*args, **kwargs)
        return wrapper
    return decorator