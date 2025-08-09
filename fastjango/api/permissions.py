"""
FastJango API Permissions - DRF-like permission classes using FastAPI.
"""

from typing import Any, Optional
from fastapi import HTTPException, status


class BasePermission:
    """
    Base permission class that all permission classes should inherit from.
    
    This mimics DRF's BasePermission while working with FastAPI.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        
        Args:
            request: The request object
            view: The view object
            
        Returns:
            True if permission is granted, False otherwise
        """
        return True
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        
        Args:
            request: The request object
            view: The view object
            obj: The object being accessed
            
        Returns:
            True if permission is granted, False otherwise
        """
        return True


class AllowAny(BasePermission):
    """
    Allow any user, authenticated or not.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Allow any user."""
        return True


class IsAuthenticated(BasePermission):
    """
    Allow only authenticated users.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if user is authenticated."""
        user = getattr(request, 'user', None)
        return user is not None and user.is_authenticated
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check if user is authenticated for object access."""
        return self.has_permission(request, view)


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Allow authenticated users to perform any action.
    Allow unauthenticated users to perform read-only actions.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check permissions based on request method."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Require authentication for write methods
        return user is not None and user.is_authenticated
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check object permissions based on request method."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Require authentication for write methods
        return user is not None and user.is_authenticated


class IsAdminUser(BasePermission):
    """
    Allow only admin users.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if user is admin."""
        user = getattr(request, 'user', None)
        return user is not None and user.is_authenticated and user.is_staff
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check if user is admin for object access."""
        return self.has_permission(request, view)


class IsOwnerOrReadOnly(BasePermission):
    """
    Allow owners of an object to edit it.
    Allow read-only access to all users.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Allow all users to read."""
        return True
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check if user is owner or request is read-only."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Check if user is owner
        if hasattr(obj, 'user'):
            return user == obj.user
        elif hasattr(obj, 'owner'):
            return user == obj.owner
        elif hasattr(obj, 'created_by'):
            return user == obj.created_by
        
        return False


class DjangoModelPermissions(BasePermission):
    """
    Permission class that follows Django's standard model permissions.
    """
    
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
    
    def get_required_permissions(self, method: str, model_cls: Any) -> list:
        """
        Get the required permissions for a method and model.
        
        Args:
            method: The HTTP method
            model_cls: The model class
            
        Returns:
            List of required permissions
        """
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        
        return [perm % {
            'app_label': app_label,
            'model_name': model_name,
        } for perm in self.perms_map.get(method, [])]
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if user has required permissions."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Get the model class
        model_cls = getattr(view, 'model', None)
        if not model_cls:
            return False
        
        # Get required permissions
        perms = self.get_required_permissions(request.method, model_cls)
        
        # Check if user has all required permissions
        return user.has_perms(perms)
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check object permissions."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Get the model class
        model_cls = type(obj)
        
        # Get required permissions
        perms = self.get_required_permissions(request.method, model_cls)
        
        # Check if user has all required permissions
        return user.has_perms(perms)


class DjangoObjectPermissions(BasePermission):
    """
    Permission class that follows Django's standard object permissions.
    """
    
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
    
    def get_required_object_permissions(self, method: str, model_cls: Any) -> list:
        """
        Get the required object permissions for a method and model.
        
        Args:
            method: The HTTP method
            model_cls: The model class
            
        Returns:
            List of required object permissions
        """
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name
        
        return [perm % {
            'app_label': app_label,
            'model_name': model_name,
        } for perm in self.perms_map.get(method, [])]
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if user has required permissions."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Get the model class
        model_cls = getattr(view, 'model', None)
        if not model_cls:
            return False
        
        # Get required permissions
        perms = self.get_required_object_permissions(request.method, model_cls)
        
        # Check if user has all required permissions
        return user.has_perms(perms)
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check object permissions."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Get the model class
        model_cls = type(obj)
        
        # Get required object permissions
        perms = self.get_required_object_permissions(request.method, model_cls)
        
        # Check if user has all required object permissions
        return user.has_perms(perms, obj)


class TokenHasReadWriteScope(BasePermission):
    """
    Permission class for OAuth2 token-based authentication with scopes.
    """
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if token has required scope."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Check if user has the required scope
        if hasattr(user, 'scope'):
            return 'read' in user.scope or 'write' in user.scope
        
        return True
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check object permissions."""
        return self.has_permission(request, view)


class TokenHasScope(BasePermission):
    """
    Permission class for OAuth2 token-based authentication with specific scopes.
    """
    
    required_scopes = []
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if token has required scopes."""
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        
        # Check if user has all required scopes
        if hasattr(user, 'scope'):
            return all(scope in user.scope for scope in self.required_scopes)
        
        return True
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check object permissions."""
        return self.has_permission(request, view)


# Example usage:
class IsProductOwner(BasePermission):
    """Custom permission for product ownership."""
    
    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        """Check if user is the owner of the product."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Check if user is the product owner
        if hasattr(obj, 'owner'):
            return user == obj.owner
        
        return False


class HasProductPermission(BasePermission):
    """Custom permission for product-related actions."""
    
    def has_permission(self, request: Any, view: Any) -> bool:
        """Check if user has product permissions."""
        user = getattr(request, 'user', None)
        
        # Allow read-only methods for all users
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        
        # Require authentication for write methods
        if not user or not user.is_authenticated:
            return False
        
        # Check if user has product management permissions
        if hasattr(user, 'has_perm'):
            return user.has_perm('products.add_product') or user.has_perm('products.change_product')
        
        return True
