"""
FastJango API - Django REST Framework-like API using FastAPI and Pydantic.
"""

from .serializers import (
    Serializer, ModelSerializer, ListSerializer,
    SerializerMethodField, ReadOnlyField, HiddenField,
    SerializerError, ValidationError
)
from .viewsets import ViewSet, ModelViewSet, ReadOnlyModelViewSet
from .views import APIView, GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .permissions import (
    BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly,
    IsAdminUser, AllowAny, DjangoModelPermissions
)
from .authentication import (
    BaseAuthentication, SessionAuthentication, TokenAuthentication,
    BasicAuthentication
)
from .pagination import (
    PageNumberPagination, LimitOffsetPagination, CursorPagination
)
from .filters import BaseFilterBackend, SearchFilter, OrderingFilter
from .renderers import (
    JSONRenderer, TemplateRenderer, BrowsableAPIRenderer
)
from .parsers import (
    JSONParser, MultiPartParser, FormParser, FileUploadParser
)
from .throttling import (
    BaseThrottle, AnonRateThrottle, UserRateThrottle
)
from .exceptions import (
    APIException, NotFound, PermissionDenied, ValidationError as APIValidationError
)
from .routers import DefaultRouter, SimpleRouter
from .decorators import action

__all__ = [
    # Serializers
    'Serializer', 'ModelSerializer', 'ListSerializer',
    'SerializerMethodField', 'ReadOnlyField', 'HiddenField',
    'SerializerError', 'ValidationError',
    
    # Viewsets
    'ViewSet', 'ModelViewSet', 'ReadOnlyModelViewSet',
    
    # Views
    'APIView', 'GenericAPIView', 'ListCreateAPIView', 'RetrieveUpdateDestroyAPIView',
    
    # Permissions
    'BasePermission', 'IsAuthenticated', 'IsAuthenticatedOrReadOnly',
    'IsAdminUser', 'AllowAny', 'DjangoModelPermissions',
    
    # Authentication
    'BaseAuthentication', 'SessionAuthentication', 'TokenAuthentication',
    'BasicAuthentication',
    
    # Pagination
    'PageNumberPagination', 'LimitOffsetPagination', 'CursorPagination',
    
    # Filters
    'BaseFilterBackend', 'SearchFilter', 'OrderingFilter',
    
    # Renderers
    'JSONRenderer', 'TemplateRenderer', 'BrowsableAPIRenderer',
    
    # Parsers
    'JSONParser', 'MultiPartParser', 'FormParser', 'FileUploadParser',
    
    # Throttling
    'BaseThrottle', 'AnonRateThrottle', 'UserRateThrottle',
    
    # Exceptions
    'APIException', 'NotFound', 'PermissionDenied', 'APIValidationError',
    
    # Routers
    'DefaultRouter', 'SimpleRouter',
    
    # Decorators
    'action',
]
