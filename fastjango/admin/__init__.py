"""
FastJango Admin - Django-like admin interface for FastJango.
"""

from .admin import (
    AdminSite, ModelAdmin, TabularInline, StackedInline,
    register, site, admin_site
)
from .actions import (
    BaseAction, DeleteSelectedAction, ExportAction,
    action, admin_action
)
from .views import (
    AdminView, AdminListView, AdminDetailView, AdminCreateView,
    AdminUpdateView, AdminDeleteView, AdminChangeListView
)
from .forms import (
    AdminModelForm, AdminForm, AdminFilterForm
)
from .filters import (
    BaseFilter, ListFilter, DateFieldListFilter, 
    AllValuesFieldListFilter, ChoicesFieldListFilter
)
from .display import (
    display, display_list, display_search, display_filter,
    list_display, list_filter, search_fields, ordering,
    readonly_fields, fields, exclude, fieldsets
)
from .permissions import (
    AdminPermission, has_add_permission, has_change_permission,
    has_delete_permission, has_view_permission
)

__all__ = [
    # Admin core
    'AdminSite', 'ModelAdmin', 'TabularInline', 'StackedInline',
    'register', 'site', 'admin_site',
    
    # Actions
    'BaseAction', 'DeleteSelectedAction', 'ExportAction',
    'action', 'admin_action',
    
    # Views
    'AdminView', 'AdminListView', 'AdminDetailView', 'AdminCreateView',
    'AdminUpdateView', 'AdminDeleteView', 'AdminChangeListView',
    
    # Forms
    'AdminModelForm', 'AdminForm', 'AdminFilterForm',
    
    # Filters
    'BaseFilter', 'ListFilter', 'DateFieldListFilter',
    'AllValuesFieldListFilter', 'ChoicesFieldListFilter',
    
    # Display
    'display', 'display_list', 'display_search', 'display_filter',
    'list_display', 'list_filter', 'search_fields', 'ordering',
    'readonly_fields', 'fields', 'exclude', 'fieldsets',
    
    # Permissions
    'AdminPermission', 'has_add_permission', 'has_change_permission',
    'has_delete_permission', 'has_view_permission',
]
