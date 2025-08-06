"""
Example usage of FastJango DRF-like API features.

This demonstrates how to use serializers, viewsets, permissions, authentication,
and pagination in a FastJango application.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import List, Optional
from pydantic import BaseModel

from fastjango.api import (
    # Serializers
    Serializer, ModelSerializer, ListSerializer,
    SerializerMethodField, ReadOnlyField, HiddenField,
    
    # Viewsets
    ViewSet, ModelViewSet, ReadOnlyModelViewSet,
    
    # Permissions
    BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly,
    IsAdminUser, AllowAny, DjangoModelPermissions,
    
    # Authentication
    BaseAuthentication, SessionAuthentication, TokenAuthentication,
    BasicAuthentication, OAuth2Authentication, JWTAuthentication,
    
    # Pagination
    PageNumberPagination, LimitOffsetPagination, CursorPagination,
    
    # Filters
    BaseFilterBackend, SearchFilter, OrderingFilter,
    
    # Exceptions
    APIException, NotFound, PermissionDenied,
    
    # Routers
    DefaultRouter, SimpleRouter,
    
    # Decorators
    action,
)

# Example models (would be imported from your app)
class User:
    def __init__(self, id: int, username: str, email: str, is_staff: bool = False):
        self.id = id
        self.username = username
        self.email = email
        self.is_staff = is_staff
        self.is_authenticated = True
    
    def has_perm(self, perm: str) -> bool:
        return self.is_staff or perm in getattr(self, 'permissions', [])

class Product:
    def __init__(self, id: int, name: str, price: float, category: str, owner: User):
        self.id = id
        self.name = name
        self.price = price
        self.category = category
        self.owner = owner

# Example serializers
class UserSerializer(ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_staff']
        read_only_fields = ['id']

class ProductSerializer(ModelSerializer):
    """Serializer for Product model."""
    
    owner_name = SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'owner', 'owner_name']
        read_only_fields = ['id', 'owner_name']
    
    def get_owner_name(self, obj):
        """Get the owner's username."""
        return obj.owner.username if obj.owner else None

# Example permissions
class IsProductOwner(BasePermission):
    """Custom permission for product ownership."""
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the owner of the product."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Check if user is the product owner
        if hasattr(obj, 'owner'):
            return user == obj.owner
        
        return False

# Example viewsets
class UserViewSet(ModelViewSet):
    """ViewSet for User model."""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """Get the queryset for users."""
        # This would typically be User.objects.all()
        return [
            User(1, "admin", "admin@example.com", is_staff=True),
            User(2, "user1", "user1@example.com"),
            User(3, "user2", "user2@example.com"),
        ]
    
    def list(self, request):
        """List all users."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return serializer.data
    
    def retrieve(self, request, pk):
        """Retrieve a specific user."""
        queryset = self.get_queryset()
        user = next((u for u in queryset if u.id == int(pk)), None)
        if not user:
            raise NotFound(f"User with pk={pk} not found")
        
        serializer = self.get_serializer(user)
        return serializer.data

class ProductViewSet(ModelViewSet):
    """ViewSet for Product model."""
    
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsProductOwner]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        """Get the queryset for products."""
        # This would typically be Product.objects.all()
        users = [
            User(1, "admin", "admin@example.com"),
            User(2, "user1", "user1@example.com"),
        ]
        return [
            Product(1, "Laptop", 999.99, "Electronics", users[0]),
            Product(2, "Phone", 599.99, "Electronics", users[1]),
            Product(3, "Book", 19.99, "Books", users[0]),
        ]
    
    def list(self, request):
        """List all products with optional filtering."""
        queryset = self.get_queryset()
        
        # Filter by category if provided
        category = request.query_params.get('category')
        if category:
            queryset = [p for p in queryset if p.category == category]
        
        serializer = self.get_serializer(queryset, many=True)
        return serializer.data
    
    def retrieve(self, request, pk):
        """Retrieve a specific product."""
        queryset = self.get_queryset()
        product = next((p for p in queryset if p.id == int(pk)), None)
        if not product:
            raise NotFound(f"Product with pk={pk} not found")
        
        serializer = self.get_serializer(product)
        return serializer.data
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk):
        """Custom action to toggle product active status."""
        product = self.get_object(pk)
        # This would typically update the product's active status
        return {"message": f"Product {product.name} active status toggled"}

# Example API views
class ProductStatsViewSet(ReadOnlyModelViewSet):
    """Read-only ViewSet for product statistics."""
    
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CursorPagination
    
    def get_queryset(self):
        """Get product statistics."""
        # This would typically be Product.objects.all()
        users = [User(1, "admin", "admin@example.com")]
        return [
            Product(1, "Laptop", 999.99, "Electronics", users[0]),
            Product(2, "Phone", 599.99, "Electronics", users[0]),
        ]
    
    def list(self, request):
        """List product statistics."""
        queryset = self.get_queryset()
        
        # Calculate statistics
        total_products = len(queryset)
        total_value = sum(p.price for p in queryset)
        categories = list(set(p.category for p in queryset))
        
        return {
            "total_products": total_products,
            "total_value": total_value,
            "categories": categories,
            "products": self.get_serializer(queryset, many=True).data
        }

# Example custom filters
class CategoryFilter(BaseFilterBackend):
    """Filter products by category."""
    
    def filter_queryset(self, request, queryset, view):
        """Filter queryset by category."""
        category = request.query_params.get('category')
        if category:
            return [p for p in queryset if p.category == category]
        return queryset

class PriceRangeFilter(BaseFilterBackend):
    """Filter products by price range."""
    
    def filter_queryset(self, request, queryset, view):
        """Filter queryset by price range."""
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        
        if min_price:
            try:
                min_price = float(min_price)
                queryset = [p for p in queryset if p.price >= min_price]
            except ValueError:
                pass
        
        if max_price:
            try:
                max_price = float(max_price)
                queryset = [p for p in queryset if p.price <= max_price]
            except ValueError:
                pass
        
        return queryset

# Example custom pagination
class ProductPagination(PageNumberPagination):
    """Custom pagination for products."""
    
    page_size = 10
    max_page_size = 50
    
    def get_paginated_response(self, data):
        """Custom paginated response."""
        return {
            'total_count': len(data),
            'page_size': self.page_size,
            'products': data
        }

# Example custom authentication
class CustomTokenAuthentication(TokenAuthentication):
    """Custom token authentication."""
    
    def authenticate_credentials(self, key):
        """Authenticate the given token."""
        # This would typically validate against a database
        if key == 'valid_token':
            user = User(1, "token_user", "token@example.com")
            return (user, key)
        return None

# Example API setup
def create_api_app():
    """Create a FastAPI app with FastJango API features."""
    app = FastAPI(title="FastJango API Example")
    
    # Set up routers
    router = DefaultRouter()
    
    # Register viewsets
    router.register(r'users', UserViewSet, basename='user')
    router.register(r'products', ProductViewSet, basename='product')
    router.register(r'stats', ProductStatsViewSet, basename='stats')
    
    # Include router
    app.include_router(router.router, prefix="/api/v1")
    
    return app

# Example usage in a FastJango app
if __name__ == "__main__":
    # Create the API app
    app = create_api_app()
    
    # Example of how to use the API
    print("FastJango DRF-like API Example")
    print("=" * 50)
    print()
    print("Available endpoints:")
    print("- GET /api/v1/users/ - List users")
    print("- GET /api/v1/users/{id}/ - Get user details")
    print("- POST /api/v1/users/ - Create user")
    print("- PUT /api/v1/users/{id}/ - Update user")
    print("- DELETE /api/v1/users/{id}/ - Delete user")
    print()
    print("- GET /api/v1/products/ - List products")
    print("- GET /api/v1/products/{id}/ - Get product details")
    print("- POST /api/v1/products/ - Create product")
    print("- PUT /api/v1/products/{id}/ - Update product")
    print("- DELETE /api/v1/products/{id}/ - Delete product")
    print("- POST /api/v1/products/{id}/toggle_active/ - Toggle product active status")
    print()
    print("- GET /api/v1/stats/ - Get product statistics")
    print()
    print("Features demonstrated:")
    print("- ModelSerializers with automatic field mapping")
    print("- ViewSets with CRUD operations")
    print("- Custom permissions (IsProductOwner)")
    print("- Multiple authentication classes")
    print("- Pagination (PageNumber, LimitOffset, Cursor)")
    print("- Custom filters (CategoryFilter, PriceRangeFilter)")
    print("- Custom actions with @action decorator")
    print("- Read-only ViewSets")
    print("- Custom pagination responses")