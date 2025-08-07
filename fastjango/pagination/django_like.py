"""
FastJango Django-like Pagination - Django DRF-style pagination.

This module provides Django-like pagination for FastJango, mimicking
Django DRF pagination behavior and API structure.
"""

from typing import List, Dict, Any, Optional, Generic, TypeVar, Union
from fastapi import Request, Query, Depends
from pydantic import BaseModel, Field
from math import ceil
from urllib.parse import urlencode, parse_qs, urlparse, urlunparse

from .pagination import BasePagination, PaginationResponse, PaginationParams


T = TypeVar('T')


class DjangoLikePagination(BasePagination):
    """Django-like pagination with DRF-style behavior."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size",
                 ordering_query_param: str = "ordering"):
        """Initialize Django-like pagination."""
        super().__init__(page_size, max_page_size, page_query_param, page_size_query_param, ordering_query_param)
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get pagination parameters in Django style."""
        page = self.get_page_number(request)
        page_size = self.get_page_size(request)
        ordering = self.get_ordering(request)
        
        return PaginationParams(page=page, page_size=page_size, ordering=ordering)
    
    def get_ordering(self, request: Request) -> Optional[str]:
        """Get ordering parameter from request."""
        return request.query_params.get(self.ordering_query_param)
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset in Django style."""
        params = self.get_pagination_params(request)
        
        # Apply ordering if specified
        if params.ordering:
            queryset = self._apply_ordering(queryset, params.ordering)
        
        # Apply pagination
        start = (params.page - 1) * params.page_size
        end = start + params.page_size
        
        return queryset[start:end]
    
    def _apply_ordering(self, queryset: List[Any], ordering: str) -> List[Any]:
        """Apply ordering to queryset."""
        if not ordering:
            return queryset
        
        # Parse ordering fields
        order_fields = [field.strip() for field in ordering.split(',')]
        
        # Sort queryset by multiple fields
        for field in reversed(order_fields):
            reverse = field.startswith('-')
            sort_key = field[1:] if reverse else field
            
            try:
                queryset = sorted(queryset, key=lambda x: getattr(x, sort_key, 0), reverse=reverse)
            except (AttributeError, TypeError):
                # Fallback to default sorting
                pass
        
        return queryset
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response in Django DRF style."""
        params = self.get_pagination_params(request)
        
        total_pages = ceil(count / params.page_size) if count > 0 else 0
        has_next = params.page < total_pages
        has_previous = params.page > 1
        
        # Build pagination links in Django style
        next_url = None
        previous_url = None
        
        base_url = str(request.url)
        
        if has_next:
            next_url = self._build_url(base_url, {self.page_query_param: params.page + 1})
        
        if has_previous:
            previous_url = self._build_url(base_url, {self.page_query_param: params.page - 1})
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )


class DjangoLikePageNumberPagination(DjangoLikePagination):
    """Django-like page number pagination."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 page_query_param: str = "page",
                 page_size_query_param: str = "page_size"):
        """Initialize Django-like page number pagination."""
        super().__init__(page_size, max_page_size, page_query_param, page_size_query_param)
    
    def get_page_number(self, request: Request) -> int:
        """Get page number in Django style."""
        try:
            page = int(request.query_params.get(self.page_query_param, 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def get_page_size(self, request: Request) -> int:
        """Get page size in Django style."""
        try:
            page_size = int(request.query_params.get(self.page_size_query_param, self.page_size))
            return min(page_size, self.max_page_size)
        except (ValueError, TypeError):
            return self.page_size


class DjangoLikeLimitOffsetPagination(DjangoLikePagination):
    """Django-like limit/offset pagination."""
    
    def __init__(self, 
                 default_limit: int = 20,
                 max_limit: int = 100,
                 limit_query_param: str = "limit",
                 offset_query_param: str = "offset"):
        """Initialize Django-like limit/offset pagination."""
        super().__init__(default_limit, max_limit)
        self.default_limit = default_limit
        self.max_limit = max_limit
        self.limit_query_param = limit_query_param
        self.offset_query_param = offset_query_param
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get limit/offset pagination parameters."""
        limit = self.get_limit(request)
        offset = self.get_offset(request)
        ordering = self.get_ordering(request)
        
        return PaginationParams(limit=limit, offset=offset, ordering=ordering)
    
    def get_limit(self, request: Request) -> int:
        """Get limit in Django style."""
        try:
            limit = int(request.query_params.get(self.limit_query_param, self.default_limit))
            return min(limit, self.max_limit)
        except (ValueError, TypeError):
            return self.default_limit
    
    def get_offset(self, request: Request) -> int:
        """Get offset in Django style."""
        try:
            offset = int(request.query_params.get(self.offset_query_param, 0))
            return max(0, offset)
        except (ValueError, TypeError):
            return 0
    
    def paginate_queryset(self, queryset: List[Any], request: Request) -> List[Any]:
        """Paginate queryset using limit/offset."""
        params = self.get_pagination_params(request)
        
        # Apply ordering if specified
        if params.ordering:
            queryset = self._apply_ordering(queryset, params.ordering)
        
        # Apply limit/offset
        return queryset[params.offset:params.offset + params.limit]
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response for limit/offset."""
        params = self.get_pagination_params(request)
        
        has_next = params.offset + params.limit < count
        has_previous = params.offset > 0
        
        # Build pagination links
        next_url = None
        previous_url = None
        
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
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=params.limit,
            has_next=has_next,
            has_previous=has_previous
        )


class DjangoLikeCursorPagination(DjangoLikePagination):
    """Django-like cursor-based pagination."""
    
    def __init__(self, 
                 page_size: int = 20,
                 max_page_size: int = 100,
                 cursor_query_param: str = "cursor",
                 ordering: str = "-id"):
        """Initialize Django-like cursor pagination."""
        super().__init__(page_size, max_page_size)
        self.cursor_query_param = cursor_query_param
        self.ordering = ordering
    
    def get_pagination_params(self, request: Request) -> PaginationParams:
        """Get cursor pagination parameters."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        return PaginationParams(cursor=cursor, page_size=page_size, ordering=self.ordering)
    
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
        """Get paginated response for cursor pagination."""
        cursor = self.get_cursor(request)
        page_size = self.get_page_size(request)
        
        has_next = len(data) == page_size
        has_previous = cursor is not None
        
        # Build pagination links
        next_url = None
        previous_url = None
        
        base_url = str(request.url)
        
        if has_next and data:
            last_item = data[-1]
            sort_key = self.ordering[1:] if self.ordering.startswith('-') else self.ordering
            next_cursor = getattr(last_item, sort_key, last_item.id)
            next_url = self._build_url(base_url, {self.cursor_query_param: str(next_cursor)})
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous
        )


# Django-like dependency functions
def get_django_page_pagination(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    ordering: Optional[str] = Query(None, description="Ordering field(s)")
) -> PaginationParams:
    """Get Django-like page number pagination parameters."""
    return PaginationParams(page=page, page_size=page_size, ordering=ordering)


def get_django_limit_offset_pagination(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    ordering: Optional[str] = Query(None, description="Ordering field(s)")
) -> PaginationParams:
    """Get Django-like limit/offset pagination parameters."""
    return PaginationParams(limit=limit, offset=offset, ordering=ordering)


def get_django_cursor_pagination(
    cursor: Optional[str] = Query(None, description="Cursor for pagination")
) -> PaginationParams:
    """Get Django-like cursor pagination parameters."""
    return PaginationParams(cursor=cursor)


# Django DRF-style pagination classes
class DjangoDRFPageNumberPagination(DjangoLikePageNumberPagination):
    """Django DRF-style page number pagination."""
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response in Django DRF style."""
        params = self.get_pagination_params(request)
        
        total_pages = ceil(count / params.page_size) if count > 0 else 0
        has_next = params.page < total_pages
        has_previous = params.page > 1
        
        # Build pagination links
        next_url = None
        previous_url = None
        
        base_url = str(request.url)
        
        if has_next:
            next_url = self._build_url(base_url, {self.page_query_param: params.page + 1})
        
        if has_previous:
            previous_url = self._build_url(base_url, {self.page_query_param: params.page - 1})
        
        return PaginationResponse(
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )


class DjangoDRFLimitOffsetPagination(DjangoLikeLimitOffsetPagination):
    """Django DRF-style limit/offset pagination."""
    
    def get_paginated_response(self, data: List[Any], count: int, request: Request) -> PaginationResponse:
        """Get paginated response in Django DRF style."""
        params = self.get_pagination_params(request)
        
        has_next = params.offset + params.limit < count
        has_previous = params.offset > 0
        
        # Build pagination links
        next_url = None
        previous_url = None
        
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
            count=count,
            next=next_url,
            previous=previous_url,
            results=data,
            page_size=params.limit,
            has_next=has_next,
            has_previous=has_previous
        )