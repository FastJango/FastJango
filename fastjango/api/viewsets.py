"""
FastJango API Viewsets - DRF-like ViewSets using FastAPI.
"""

from typing import Any, Dict, List, Optional, Type, Union
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .serializers import Serializer, ModelSerializer
from .permissions import BasePermission, AllowAny
from .authentication import BaseAuthentication
from .pagination import BasePagination
from .filters import BaseFilterBackend
from .exceptions import APIException, NotFound, PermissionDenied


class ViewSet:
    """
    Base ViewSet class that provides common functionality for all viewsets.
    
    This mimics DRF's ViewSet while leveraging FastAPI's performance and features.
    """
    
    serializer_class: Optional[Type[Serializer]] = None
    permission_classes: List[Type[BasePermission]] = [AllowAny]
    authentication_classes: List[Type[BaseAuthentication]] = []
    pagination_class: Optional[Type[BasePagination]] = None
    filter_backends: List[Type[BaseFilterBackend]] = []
    lookup_field: str = 'pk'
    lookup_url_kwarg: Optional[str] = None
    
    def __init__(self, **kwargs):
        """Initialize the viewset."""
        self.action = None
        self.request = None
        self.args = ()
        self.kwargs = {}
        
        # Set up router
        self.router = APIRouter()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up the routes for this viewset."""
        # This will be overridden by subclasses
        pass
    
    def get_serializer_class(self) -> Type[Serializer]:
        """Get the serializer class for this viewset."""
        return self.serializer_class
    
    def get_serializer(self, *args, **kwargs) -> Serializer:
        """Get a serializer instance."""
        serializer_class = self.get_serializer_class()
        return serializer_class(*args, **kwargs)
    
    def get_permissions(self) -> List[BasePermission]:
        """Get the permissions for this viewset."""
        return [permission() for permission in self.permission_classes]
    
    def get_authentication(self) -> List[BaseAuthentication]:
        """Get the authentication classes for this viewset."""
        return [auth() for auth in self.authentication_classes]
    
    def get_pagination_class(self) -> Optional[Type[BasePagination]]:
        """Get the pagination class for this viewset."""
        return self.pagination_class
    
    def get_filter_backends(self) -> List[BaseFilterBackend]:
        """Get the filter backends for this viewset."""
        return [backend() for backend in self.filter_backends]
    
    def check_permissions(self, request: Any) -> None:
        """Check permissions for the request."""
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                raise PermissionDenied()
    
    def check_object_permissions(self, request: Any, obj: Any) -> None:
        """Check object permissions for the request."""
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                raise PermissionDenied()
    
    def get_object(self) -> Any:
        """Get the object for detail views."""
        raise NotImplementedError("Subclasses must implement get_object()")
    
    def list(self, request: Any) -> Dict[str, Any]:
        """List all objects."""
        raise NotImplementedError("Subclasses must implement list()")
    
    def create(self, request: Any) -> Dict[str, Any]:
        """Create a new object."""
        raise NotImplementedError("Subclasses must implement create()")
    
    def retrieve(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Retrieve a single object."""
        raise NotImplementedError("Subclasses must implement retrieve()")
    
    def update(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Update an object."""
        raise NotImplementedError("Subclasses must implement update()")
    
    def partial_update(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Partially update an object."""
        raise NotImplementedError("Subclasses must implement partial_update()")
    
    def destroy(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Delete an object."""
        raise NotImplementedError("Subclasses must implement destroy()")


class ModelViewSet(ViewSet):
    """
    ViewSet that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    
    queryset = None
    model = None
    
    def __init__(self, **kwargs):
        """Initialize the model viewset."""
        super().__init__(**kwargs)
        
        # Set up routes
        self.router.add_api_route(
            "/",
            self.list,
            methods=["GET"],
            response_model=List[Dict[str, Any]],
            summary="List objects"
        )
        self.router.add_api_route(
            "/",
            self.create,
            methods=["POST"],
            response_model=Dict[str, Any],
            summary="Create object"
        )
        self.router.add_api_route(
            "/{pk}",
            self.retrieve,
            methods=["GET"],
            response_model=Dict[str, Any],
            summary="Retrieve object"
        )
        self.router.add_api_route(
            "/{pk}",
            self.update,
            methods=["PUT"],
            response_model=Dict[str, Any],
            summary="Update object"
        )
        self.router.add_api_route(
            "/{pk}",
            self.partial_update,
            methods=["PATCH"],
            response_model=Dict[str, Any],
            summary="Partially update object"
        )
        self.router.add_api_route(
            "/{pk}",
            self.destroy,
            methods=["DELETE"],
            response_model=Dict[str, Any],
            summary="Delete object"
        )
    
    def get_queryset(self):
        """Get the queryset for this viewset."""
        if self.queryset is not None:
            return self.queryset
        elif self.model is not None:
            return self.model.objects.all()
        else:
            raise NotImplementedError("Either queryset or model must be specified")
    
    def get_object(self, pk: Any) -> Any:
        """Get a single object by primary key."""
        queryset = self.get_queryset()
        try:
            return queryset.get(pk=pk)
        except Exception:
            raise NotFound(f"Object with pk={pk} not found")
    
    def list(self, request: Any) -> List[Dict[str, Any]]:
        """List all objects."""
        self.check_permissions(request)
        
        queryset = self.get_queryset()
        
        # Apply filters
        for backend in self.get_filter_backends():
            queryset = backend.filter_queryset(request, queryset, self)
        
        # Apply pagination
        pagination_class = self.get_pagination_class()
        if pagination_class:
            paginator = pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            serializer = self.get_serializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # Serialize
        serializer = self.get_serializer(queryset, many=True)
        return serializer.data
    
    def create(self, request: Any) -> Dict[str, Any]:
        """Create a new object."""
        self.check_permissions(request)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return self.get_serializer(obj).data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=serializer.errors
            )
    
    def retrieve(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Retrieve a single object."""
        self.check_permissions(request)
        
        obj = self.get_object(pk)
        self.check_object_permissions(request, obj)
        
        serializer = self.get_serializer(obj)
        return serializer.data
    
    def update(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Update an object."""
        self.check_permissions(request)
        
        obj = self.get_object(pk)
        self.check_object_permissions(request, obj)
        
        serializer = self.get_serializer(obj, data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            return self.get_serializer(obj).data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=serializer.errors
            )
    
    def partial_update(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Partially update an object."""
        self.check_permissions(request)
        
        obj = self.get_object(pk)
        self.check_object_permissions(request, obj)
        
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            obj = serializer.save()
            return self.get_serializer(obj).data
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=serializer.errors
            )
    
    def destroy(self, request: Any, pk: Any) -> Dict[str, Any]:
        """Delete an object."""
        self.check_permissions(request)
        
        obj = self.get_object(pk)
        self.check_object_permissions(request, obj)
        
        obj.delete()
        return {"detail": "Object deleted successfully"}


class ReadOnlyModelViewSet(ModelViewSet):
    """
    ViewSet that provides default `list()` and `retrieve()` actions.
    """
    
    def __init__(self, **kwargs):
        """Initialize the read-only model viewset."""
        super().__init__(**kwargs)
        
        # Remove create, update, partial_update, and destroy routes
        self.router.routes = [route for route in self.router.routes 
                             if route.methods not in [{"POST"}, {"PUT"}, {"PATCH"}, {"DELETE"}]]


# Example usage:
class UserViewSet(ModelViewSet):
    """Example user viewset."""
    
    serializer_class = None  # Would be set to UserSerializer
    queryset = None  # Would be set to User.objects.all()
    
    def get_queryset(self):
        """Get the queryset for users."""
        return self.queryset.filter(is_active=True)


class ProductViewSet(ModelViewSet):
    """Example product viewset."""
    
    serializer_class = None  # Would be set to ProductSerializer
    queryset = None  # Would be set to Product.objects.all()
    
    def get_queryset(self):
        """Get the queryset for products."""
        return self.queryset.filter(is_active=True)
    
    def list(self, request: Any) -> List[Dict[str, Any]]:
        """List products with category filtering."""
        queryset = self.get_queryset()
        
        # Filter by category if provided
        category_id = request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return serializer.data
