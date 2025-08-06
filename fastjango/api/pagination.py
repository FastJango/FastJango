"""
FastJango API Pagination - DRF-like pagination classes using FastAPI.
"""

from typing import Any, Dict, List, Optional, Type
from fastapi import Request, Query
from pydantic import BaseModel


class BasePagination:
    """
    Base pagination class that all pagination classes should inherit from.
    
    This mimics DRF's BasePagination while working with FastAPI.
    """
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def paginate_queryset(self, queryset: Any, request: Request) -> List[Any]:
        """
        Return a page of results.
        
        Args:
            queryset: The queryset to paginate
            request: The request object
            
        Returns:
            List of paginated results
        """
        raise NotImplementedError("Subclasses must implement paginate_queryset()")
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """
        Return a paginated response.
        
        Args:
            data: The paginated data
            
        Returns:
            Dictionary containing paginated response
        """
        raise NotImplementedError("Subclasses must implement get_paginated_response()")
    
    def get_page_size(self, request: Request) -> int:
        """
        Get the page size from the request.
        
        Args:
            request: The request object
            
        Returns:
            The page size
        """
        page_size = request.query_params.get(self.page_size_query_param)
        if page_size:
            try:
                page_size = int(page_size)
                if page_size > 0:
                    return min(page_size, self.max_page_size)
            except (ValueError, TypeError):
                pass
        return self.page_size


class PageNumberPagination(BasePagination):
    """
    A simple page number based pagination.
    """
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'
    
    def paginate_queryset(self, queryset: Any, request: Request) -> List[Any]:
        """
        Return a page of results.
        
        Args:
            queryset: The queryset to paginate
            request: The request object
            
        Returns:
            List of paginated results
        """
        page_size = self.get_page_size(request)
        page_number = self.get_page_number(request)
        
        # Calculate offset
        offset = (page_number - 1) * page_size
        
        # Apply pagination
        if hasattr(queryset, 'limit') and hasattr(queryset, 'offset'):
            return list(queryset.offset(offset).limit(page_size))
        elif hasattr(queryset, '__getitem__'):
            return list(queryset[offset:offset + page_size])
        else:
            # Fallback for list-like objects
            items = list(queryset)
            return items[offset:offset + page_size]
    
    def get_page_number(self, request: Request) -> int:
        """
        Get the page number from the request.
        
        Args:
            request: The request object
            
        Returns:
            The page number
        """
        page_number = request.query_params.get(self.page_query_param, '1')
        try:
            page_number = int(page_number)
            return max(1, page_number)
        except (ValueError, TypeError):
            return 1
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """
        Return a paginated response.
        
        Args:
            data: The paginated data
            
        Returns:
            Dictionary containing paginated response
        """
        return {
            'count': len(data),
            'next': None,  # Would be calculated based on total count
            'previous': None,  # Would be calculated based on current page
            'results': data
        }
    
    def get_count(self, queryset: Any) -> int:
        """
        Get the total count of the queryset.
        
        Args:
            queryset: The queryset
            
        Returns:
            The total count
        """
        if hasattr(queryset, 'count'):
            return queryset.count()
        elif hasattr(queryset, '__len__'):
            return len(queryset)
        else:
            return 0


class LimitOffsetPagination(BasePagination):
    """
    A limit/offset based pagination.
    """
    
    default_limit = 10
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100
    
    def paginate_queryset(self, queryset: Any, request: Request) -> List[Any]:
        """
        Return a page of results.
        
        Args:
            queryset: The queryset to paginate
            request: The request object
            
        Returns:
            List of paginated results
        """
        limit = self.get_limit(request)
        offset = self.get_offset(request)
        
        # Apply pagination
        if hasattr(queryset, 'limit') and hasattr(queryset, 'offset'):
            return list(queryset.offset(offset).limit(limit))
        elif hasattr(queryset, '__getitem__'):
            return list(queryset[offset:offset + limit])
        else:
            # Fallback for list-like objects
            items = list(queryset)
            return items[offset:offset + limit]
    
    def get_limit(self, request: Request) -> int:
        """
        Get the limit from the request.
        
        Args:
            request: The request object
            
        Returns:
            The limit
        """
        limit = request.query_params.get(self.limit_query_param)
        if limit:
            try:
                limit = int(limit)
                if limit > 0:
                    return min(limit, self.max_limit)
            except (ValueError, TypeError):
                pass
        return self.default_limit
    
    def get_offset(self, request: Request) -> int:
        """
        Get the offset from the request.
        
        Args:
            request: The request object
            
        Returns:
            The offset
        """
        offset = request.query_params.get(self.offset_query_param, '0')
        try:
            offset = int(offset)
            return max(0, offset)
        except (ValueError, TypeError):
            return 0
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """
        Return a paginated response.
        
        Args:
            data: The paginated data
            
        Returns:
            Dictionary containing paginated response
        """
        return {
            'count': len(data),
            'next': None,  # Would be calculated based on total count
            'previous': None,  # Would be calculated based on current offset
            'results': data
        }


class CursorPagination(BasePagination):
    """
    A cursor-based pagination.
    """
    
    page_size = 10
    cursor_query_param = 'cursor'
    ordering = '-created_at'
    
    def paginate_queryset(self, queryset: Any, request: Request) -> List[Any]:
        """
        Return a page of results.
        
        Args:
            queryset: The queryset to paginate
            request: The request object
            
        Returns:
            List of paginated results
        """
        cursor = request.query_params.get(self.cursor_query_param)
        page_size = self.get_page_size(request)
        
        # Apply ordering
        if hasattr(queryset, 'order_by'):
            queryset = queryset.order_by(self.ordering)
        
        # Apply cursor pagination
        if cursor:
            # Here you would typically decode the cursor and apply filtering
            # For now, we'll just limit the results
            if hasattr(queryset, 'limit'):
                return list(queryset.limit(page_size))
            else:
                items = list(queryset)
                return items[:page_size]
        else:
            # First page
            if hasattr(queryset, 'limit'):
                return list(queryset.limit(page_size))
            else:
                items = list(queryset)
                return items[:page_size]
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """
        Return a paginated response.
        
        Args:
            data: The paginated data
            
        Returns:
            Dictionary containing paginated response
        """
        return {
            'next': None,  # Would be calculated based on cursor
            'previous': None,  # Would be calculated based on cursor
            'results': data
        }


# Pydantic models for pagination responses
class PageNumberPaginationResponse(BaseModel):
    """Response model for page number pagination."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Any]


class LimitOffsetPaginationResponse(BaseModel):
    """Response model for limit/offset pagination."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Any]


class CursorPaginationResponse(BaseModel):
    """Response model for cursor pagination."""
    next: Optional[str]
    previous: Optional[str]
    results: List[Any]


# Example usage:
class CustomPageNumberPagination(PageNumberPagination):
    """Custom pagination with different page size."""
    
    page_size = 20
    max_page_size = 50
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """Custom paginated response."""
        return {
            'total_count': len(data),
            'page_size': self.page_size,
            'items': data
        }


class ProductPagination(LimitOffsetPagination):
    """Custom pagination for products."""
    
    default_limit = 25
    max_limit = 100
    
    def get_paginated_response(self, data: List[Any]) -> Dict[str, Any]:
        """Custom paginated response for products."""
        return {
            'products': data,
            'total': len(data),
            'limit': self.default_limit
        }