"""
FastJango Base Pagination - Django-like pagination with FastAPI features.

This module provides base pagination classes for FastJango, similar to Django DRF
pagination but adapted for FastAPI with modern features.
"""

from typing import List, Dict, Any, Optional, Generic, TypeVar, Union
from dataclasses import dataclass
from math import ceil
from urllib.parse import urlencode, parse_qs, urlparse, urlunparse

from fastapi import Request, Query, Depends
from pydantic import BaseModel, Field

from fastjango.core.exceptions import FastJangoError


T = TypeVar('T')


@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20
    limit: Optional[int] = None
    offset: Optional[int] = None
    cursor: Optional[str] = None
    ordering: Optional[str] = None


class PaginationResponse(BaseModel, Generic[T]):
    """Pagination response model."""
    count: int = Field(description="Total number of items")
    next: Optional[str] = Field(None, description="URL to next page")
    previous: Optional[str] = Field(None, description="URL to previous page")
    results: List[T] = Field(description="List of items for current page")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    has_next: Optional[bool] = Field(None, description="Whether there is a next page")
    has_previous: Optional[bool] = Field(None, description="Whether there is a previous page")


class BasePagination:
    """Base pagination class."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size",
                 ordering_query_param: str = "ordering"):
        """
        Initialize pagination.
        
        Args:
            page_size: Default page size
            max_page_size: Maximum allowed page size
            page_query_param: Query parameter name for page
            page_size_query_param: Query parameter name for page size
            ordering_query_param: Query parameter name for ordering
        """
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.page_query_param = page_query_param
        self.page_size_query_param = page_size_query_param
        self.ordering_query_param = ordering_query_param
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response."""
        raise NotImplementedError
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset."""
        raise NotImplementedError
    
    def get_pagination_links(self, request: Request, **kwargs) -> Dict[str, Optional[str]]:
        """Get pagination links."""
        raise NotImplementedError


class PageNumberPagination(BasePagination):
    """Page number pagination similar to Django DRF."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size"):
        """Initialize page number pagination."""
        super().__init__(page_size, max_page_size, page_query_param, page_size_query_param)
    
    def get_page_number(self, request: Request) -> int:
        """Get page number from request."""
        try:
            page = int(request.query_params.get(self.page_query_param, 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def get_page_size(self, request: Request) -> int:
        """Get page size from request."""
        try:
            page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
            return min(page_size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset."""
        page_number = self.get_page_number(request)
        page_size = self.get_page_size(request)
        
        start = (page_number - 1) * page_size
        end = start + page_size
        
        return queryset[start:end]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response."""
        page_number = self.get_page_number(request)
        page_size = self.get_page_size(request)
        
        total_pages = ceil(count / page_size) if count > 0 else 0
        has_next = page_number < total_pages
        has_previous = page_number > 1
        
        # Build pagination links
        base_url = str(request.url)
        next_url = None
        previous_url = None
        
        if has_next:
            next_url = self._build_url(base_url, {self.page_query_param: page_number + 1})
        
        if has_previous:
            previous_url = self._build_url(base_url, {self.page_query_param: page_number - 1})
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page=page_number,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )
    
    def _build_url(self, base_url: str, params: Dict[str, Any]) -> str:
        """Build URL with query parameters."""
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Update with new parameters
        for key, value in params.items():
            query_params[key] = [str(value)]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))


class LimitOffsetPagination(BasePagination):
    """Limit/offset pagination similar to Django DRF."""
    
    def __init__(self, 
                 default_limit: int = 20,
                 max_limit: int = 100,
                 limit_query_param: str = "limit",
                 offset_query_param: str = "offset"):
        """Initialize limit/offset pagination."""
        super().__init__(default_limit, max_limit)
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.limit_query_param = limit_query_param
        self.offset_query_param = offset_query_param
    
    def get_limit(self, request: Request) -> int:
        """Get limit from request."""
        try:
            limit = int(request.query_params.get(self.limit_query_param, self.default_limit))
            return min(limit, self.max_limit)
        except (ValueError, TypeError):
            return self.default_limit
    
    def get_offset(self, request: Request) -> int:
        """Get offset from request."""
        try:
            offset = int(request.query_params.get(self.offset_query_param, 0))
            return max(0, offset)
        except (ValueError, TypeError):
            return 0
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset."""
        limit = self.get_limit(request)
        offset = self.get_offset(request)
        
        return queryset[offset:offset + limit]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response."""
        limit = self.get_limit(request)
        offset = self.get_offset(request)
        
        has_next = offset + limit < count
        has_previous = offset > 0
        
        # Build pagination links
        base_url = str(request.url)
        next_url = None
        previous_url = None
        
        if has_next:
            next_url = self._build_url(base_url, {
                self.limit_query_param: limit,
                self.offset_query_param: offset + limit
            })
        
        if has_previous:
            previous_url = self._build_url(base_url, {
                self.limit_query_param: limit,
                self.offset_query_param: max(0, offset - limit)
            })
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=limit,
            has_next=has_next,
            has_previous=has_previous
        )
    
    def _build_url(self, base_url: str, params: Dict[str, Any]) -> str:
        """Build URL with query parameters."""
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Update with new parameters
        for key, value in params.items():
            query_params[key] = [str(value)]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))


class CursorPagination(BasePagination):
    """Cursor-based pagination for large datasets."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 cursor_query_param: str = "cursor",
                 ordering: str = "-id"):
        """Initialize cursor pagination."""
        super().__init__(page_size, max_page_size)
        self.cursor_query_param = cursor_query_param
        self.ordering = ordering
    
    def get_cursor(self, request: Request) -> Optional[str]:
        """Get cursor from request."""
        return request.query_params.get(self.cursor_query_param)
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset using cursor."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        # Sort queryset by ordering
        reverse = self.ordering.startswith('-')
        sort_key = self.ordering[1:] if reverse else self.ordering
        
        # Sort the queryset
        sorted_queryset = sorted(queryset, key=lambda x: getattr(x, sort_key, 0), reverse=reverse)
        
        if cursor:
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
        """Get paginated response."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        has_next = len(data) == page_size
        has_previous = cursor is not None
        
        # Build pagination links
        base_url = str(request.url)
        next_url = None
        previous_url = None
        
        if has_next and data:
            last_item = data[-1]
            sort_key = self.ordering[1:] if self.ordering.startswith('-') else self.ordering
            next_cursor = getattr(last_item, sort_key, last_item.id)
            next_url = self._build_url(base_url, {self.cursor_query_param: str(next_cursor)})
        
        if has_previous:
            # For previous, we'd need to implement reverse cursor logic
            # This is simplified for now
            pass
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )
    
    def _build_url(self, base_url: str, params: Dict[str, Any]) -> str:
        """Build URL with query parameters."""
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Update with new parameters
        for key, value in params.items():
            query_params[key] = [str(value)]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))


# FastAPI dependency functions
def get_page_number_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
) -> PaginationParams:
    """Get page number pagination parameters."""
    return PaginationParams(page=page, page_size=page_size)


def get_limit_offset_pagination(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
) -> PaginationParams:
    """Get limit/offset pagination parameters."""
    return PaginationParams(limit=limit, offset=offset)


def get_cursor_pagination(
    cursor: Optional[str] = Query(None, description="Cursor for pagination")
) -> PaginationParams:
    """Get cursor pagination parameters."""
    return PaginationParams(cursor=cursor)
