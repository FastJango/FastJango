"""
FastJango Admin - Django-like admin interface for FastJango.
"""

import os
from typing import Any, Dict, List, Optional, Type, Union
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from .views import AdminListView, AdminDetailView, AdminCreateView, AdminUpdateView, AdminDeleteView
from .forms import AdminModelForm
from .permissions import AdminPermission


class AdminSite:
    """
    Django-like admin site for FastJango.
    """
    
    def __init__(self, name: str = "FastJango Admin", 
                 site_header: str = "FastJango Administration",
                 site_title: str = "FastJango Admin",
                 index_title: str = "Welcome to FastJango Admin",
                 admin_path: str = "/admin"):
        """
        Initialize the admin site.
        
        Args:
            name: The admin site name
            site_header: The site header
            site_title: The site title
            index_title: The index page title
            admin_path: The admin URL path (default: /admin)
        """
        self.name = name
        self.site_header = site_header
        self.site_title = site_title
        self.index_title = index_title
        self.admin_path = admin_path.rstrip('/')
        
        self._registry = {}
        self._urls = []
        self.templates = None
        
    def register(self, model: Type, admin_class: Type = None, **options):
        """
        Register a model with the admin site.
        
        Args:
            model: The model class to register
            admin_class: The admin class to use
            **options: Additional options
        """
        if admin_class is None:
            from .admin import ModelAdmin
            admin_class = ModelAdmin
        
        admin_instance = admin_class(model, self, **options)
        self._registry[model] = admin_instance
        
        # Generate URLs for the model
        model_name = model.__name__.lower()
        model_path = f"{self.admin_path}/{model_name}"
        
        self._urls.extend([
            (f"{model_path}/", admin_instance.changelist_view, "GET"),
            (f"{model_path}/add/", admin_instance.add_view, "GET"),
            (f"{model_path}/add/", admin_instance.add_view, "POST"),
            (f"{model_path}/{{pk}}/", admin_instance.change_view, "GET"),
            (f"{model_path}/{{pk}}/", admin_instance.change_view, "POST"),
            (f"{model_path}/{{pk}}/delete/", admin_instance.delete_view, "GET"),
            (f"{model_path}/{{pk}}/delete/", admin_instance.delete_view, "POST"),
        ])
    
    def get_urls(self) -> List[tuple]:
        """
        Get all admin URLs.
        
        Returns:
            List of URL tuples (path, view, method)
        """
        urls = [
            (f"{self.admin_path}/", self.index_view, "GET"),
            (f"{self.admin_path}/login/", self.login_view, "GET"),
            (f"{self.admin_path}/login/", self.login_view, "POST"),
            (f"{self.admin_path}/logout/", self.logout_view, "GET"),
        ]
        urls.extend(self._urls)
        return urls
    
    def mount(self, app: FastAPI):
        """
        Mount the admin site to a FastAPI app.
        
        Args:
            app: The FastAPI app
        """
        # Set up templates
        self._setup_templates()
        
        # Add admin URLs
        for path, view, method in self.get_urls():
            if method == "GET":
                app.get(path)(view)
            elif method == "POST":
                app.post(path)(view)
        
        # Add admin site to app state
        app.state.admin_site = self
    
    def _setup_templates(self):
        """Set up admin templates."""
        # Create admin templates directory
        admin_templates_dir = Path(__file__).parent / "templates"
        if admin_templates_dir.exists():
            self.templates = Jinja2Templates(directory=str(admin_templates_dir))
        else:
            # Use default templates
            self.templates = Jinja2Templates(directory="templates")
    
    async def index_view(self, request: Request):
        """Admin index view."""
        context = {
            "site_header": self.site_header,
            "site_title": self.site_title,
            "index_title": self.index_title,
            "app_list": self.get_app_list(),
            "admin_path": self.admin_path,
        }
        
        if self.templates:
            return self.templates.TemplateResponse("admin/index.html", {"request": request, **context})
        else:
            return self._render_index_html(context)
    
    async def login_view(self, request: Request):
        """Admin login view."""
        if request.method == "POST":
            # Handle login logic
            form_data = await request.form()
            username = form_data.get("username")
            password = form_data.get("password")
            
            # Simple authentication (replace with proper auth)
            if username == "admin" and password == "admin":
                response = RedirectResponse(url=f"{self.admin_path}/", status_code=302)
                response.set_cookie("admin_session", "authenticated")
                return response
            else:
                context = {
                    "error": "Invalid credentials",
                    "admin_path": self.admin_path,
                }
                return self._render_login_html(context)
        
        context = {"admin_path": self.admin_path}
        return self._render_login_html(context)
    
    async def logout_view(self, request: Request):
        """Admin logout view."""
        response = RedirectResponse(url=f"{self.admin_path}/login/", status_code=302)
        response.delete_cookie("admin_session")
        return response
    
    def get_app_list(self) -> List[Dict[str, Any]]:
        """
        Get the list of registered apps and models.
        
        Returns:
            List of app dictionaries
        """
        apps = {}
        
        for model, admin_instance in self._registry.items():
            app_label = getattr(model, '_meta', {}).get('app_label', 'unknown')
            
            if app_label not in apps:
                apps[app_label] = {
                    'name': app_label.title(),
                    'app_label': app_label,
                    'models': []
                }
            
            apps[app_label]['models'].append({
                'name': model.__name__,
                'object_name': model.__name__,
                'admin_url': f"{self.admin_path}/{model.__name__.lower()}/",
                'add_url': f"{self.admin_path}/{model.__name__.lower()}/add/",
                'count': 0,  # Would be model.objects.count()
            })
        
        return list(apps.values())
    
    def _render_index_html(self, context: Dict[str, Any]) -> HTMLResponse:
        """Render admin index HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{context['site_title']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background: #417690; color: white; padding: 20px; margin-bottom: 20px; }}
                .content {{ max-width: 1200px; margin: 0 auto; }}
                .app-list {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
                .app-card {{ border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
                .app-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .model-list {{ list-style: none; padding: 0; }}
                .model-item {{ margin: 5px 0; }}
                .model-link {{ color: #417690; text-decoration: none; }}
                .model-link:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{context['site_header']}</h1>
            </div>
            <div class="content">
                <h2>{context['index_title']}</h2>
                <div class="app-list">
                    {self._render_app_list(context['app_list'])}
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    def _render_app_list(self, app_list: List[Dict[str, Any]]) -> str:
        """Render the app list HTML."""
        html = ""
        for app in app_list:
            html += f"""
            <div class="app-card">
                <div class="app-title">{app['name']}</div>
                <ul class="model-list">
            """
            for model in app['models']:
                html += f"""
                    <li class="model-item">
                        <a href="{model['admin_url']}" class="model-link">
                            {model['name']} ({model['count']})
                        </a>
                    </li>
                """
            html += """
                </ul>
            </div>
            """
        return html
    
    def _render_login_html(self, context: Dict[str, Any]) -> HTMLResponse:
        """Render admin login HTML."""
        error_html = f'<div style="color: red; margin-bottom: 10px;">{context.get("error", "")}</div>' if context.get("error") else ""
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Admin Login</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .login-container {{ max-width: 400px; margin: 100px auto; background: white; padding: 40px; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="text"], input[type="password"] {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }}
                button {{ width: 100%; padding: 12px; background: #417690; color: white; border: none; border-radius: 3px; cursor: pointer; }}
                button:hover {{ background: #2c5aa0; }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <div class="header">
                    <h1>Admin Login</h1>
                </div>
                {error_html}
                <form method="post">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit">Login</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


class ModelAdmin:
    """
    Django-like ModelAdmin for FastJango.
    """
    
    def __init__(self, model: Type, admin_site: AdminSite, **options):
        """
        Initialize the ModelAdmin.
        
        Args:
            model: The model class
            admin_site: The admin site
            **options: Additional options
        """
        self.model = model
        self.admin_site = admin_site
        self.list_display = getattr(self, 'list_display', ['__str__'])
        self.list_filter = getattr(self, 'list_filter', [])
        self.search_fields = getattr(self, 'search_fields', [])
        self.ordering = getattr(self, 'ordering', [])
        self.readonly_fields = getattr(self, 'readonly_fields', [])
        self.fields = getattr(self, 'fields', '__all__')
        self.exclude = getattr(self, 'exclude', [])
        self.fieldsets = getattr(self, 'fieldsets', None)
        
        # Set up form
        self.form = self.get_form()
    
    def get_form(self):
        """Get the form class for this admin."""
        if hasattr(self, 'form_class'):
            return self.form_class
        
        class AdminModelForm(AdminModelForm):
            class Meta:
                model = self.model
                fields = self.fields
                exclude = self.exclude
        
        return AdminModelForm
    
    async def changelist_view(self, request: Request):
        """Admin changelist view."""
        # Get queryset
        queryset = self.get_queryset(request)
        
        # Apply filters
        queryset = self.apply_filters(request, queryset)
        
        # Apply search
        queryset = self.apply_search(request, queryset)
        
        # Apply ordering
        queryset = self.apply_ordering(request, queryset)
        
        # Paginate
        page = self.paginate_queryset(request, queryset)
        
        context = {
            'admin_site': self.admin_site,
            'model_admin': self,
            'model': self.model,
            'object_list': page,
            'list_display': self.list_display,
            'list_filter': self.list_filter,
            'search_fields': self.search_fields,
            'admin_path': self.admin_site.admin_path,
        }
        
        return self._render_changelist_html(context)
    
    async def add_view(self, request: Request):
        """Admin add view."""
        if request.method == "POST":
            form_data = await request.form()
            form = self.form(data=form_data)
            
            if form.is_valid():
                obj = form.save()
                return RedirectResponse(
                    url=f"{self.admin_site.admin_path}/{self.model.__name__.lower()}/{obj.pk}/",
                    status_code=302
                )
        else:
            form = self.form()
        
        context = {
            'admin_site': self.admin_site,
            'model_admin': self,
            'model': self.model,
            'form': form,
            'admin_path': self.admin_site.admin_path,
        }
        
        return self._render_change_form_html(context)
    
    async def change_view(self, request: Request, pk: Any):
        """Admin change view."""
        # Get object
        obj = self.get_object(request, pk)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        
        if request.method == "POST":
            form_data = await request.form()
            form = self.form(data=form_data, instance=obj)
            
            if form.is_valid():
                obj = form.save()
                return RedirectResponse(
                    url=f"{self.admin_site.admin_path}/{self.model.__name__.lower()}/{obj.pk}/",
                    status_code=302
                )
        else:
            form = self.form(instance=obj)
        
        context = {
            'admin_site': self.admin_site,
            'model_admin': self,
            'model': self.model,
            'object': obj,
            'form': form,
            'admin_path': self.admin_site.admin_path,
        }
        
        return self._render_change_form_html(context)
    
    async def delete_view(self, request: Request, pk: Any):
        """Admin delete view."""
        # Get object
        obj = self.get_object(request, pk)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        
        if request.method == "POST":
            # Delete object
            obj.delete()
            return RedirectResponse(
                url=f"{self.admin_site.admin_path}/{self.model.__name__.lower()}/",
                status_code=302
            )
        
        context = {
            'admin_site': self.admin_site,
            'model_admin': self,
            'model': self.model,
            'object': obj,
            'admin_path': self.admin_site.admin_path,
        }
        
        return self._render_delete_confirmation_html(context)
    
    def get_queryset(self, request: Request):
        """Get the queryset for this admin."""
        # This would typically return model.objects.all()
        # For now, return an empty list
        return []
    
    def get_object(self, request: Request, pk: Any):
        """Get a specific object by primary key."""
        # This would typically return model.objects.get(pk=pk)
        # For now, return None
        return None
    
    def apply_filters(self, request: Request, queryset):
        """Apply filters to the queryset."""
        return queryset
    
    def apply_search(self, request: Request, queryset):
        """Apply search to the queryset."""
        return queryset
    
    def apply_ordering(self, request: Request, queryset):
        """Apply ordering to the queryset."""
        return queryset
    
    def paginate_queryset(self, request: Request, queryset):
        """Paginate the queryset."""
        return queryset
    
    def _render_changelist_html(self, context: Dict[str, Any]) -> HTMLResponse:
        """Render changelist HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{context['model'].__name__} - Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background: #417690; color: white; padding: 20px; margin-bottom: 20px; }}
                .content {{ max-width: 1200px; margin: 0 auto; }}
                .actions {{ margin-bottom: 20px; }}
                .btn {{ padding: 10px 20px; background: #417690; color: white; text-decoration: none; border-radius: 3px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
                th {{ background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{context['model'].__name__}</h1>
            </div>
            <div class="content">
                <div class="actions">
                    <a href="{context['admin_path']}/{context['model'].__name__.lower()}/add/" class="btn">Add {context['model'].__name__}</a>
                </div>
                <table>
                    <thead>
                        <tr>
                            {''.join(f'<th>{field}</th>' for field in context['list_display'])}
                        </tr>
                    </thead>
                    <tbody>
                        {self._render_object_list(context['object_list'], context['list_display'])}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    def _render_object_list(self, object_list: List, list_display: List[str]) -> str:
        """Render the object list HTML."""
        html = ""
        for obj in object_list:
            html += "<tr>"
            for field in list_display:
                if field == '__str__':
                    value = str(obj)
                else:
                    value = getattr(obj, field, '')
                html += f"<td>{value}</td>"
            html += "</tr>"
        return html
    
    def _render_change_form_html(self, context: Dict[str, Any]) -> HTMLResponse:
        """Render change form HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{context['model'].__name__} - Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background: #417690; color: white; padding: 20px; margin-bottom: 20px; }}
                .content {{ max-width: 800px; margin: 0 auto; }}
                .form-group {{ margin-bottom: 20px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                input[type="text"], input[type="password"], textarea, select {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box; }}
                button {{ padding: 10px 20px; background: #417690; color: white; border: none; border-radius: 3px; cursor: pointer; }}
                .btn-secondary {{ background: #6c757d; margin-left: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{'Edit' if context.get('object') else 'Add'} {context['model'].__name__}</h1>
            </div>
            <div class="content">
                <form method="post">
                    {self._render_form_fields(context['form'])}
                    <button type="submit">Save</button>
                    <a href="{context['admin_path']}/{context['model'].__name__.lower()}/" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)
    
    def _render_form_fields(self, form) -> str:
        """Render form fields HTML."""
        html = ""
        for field_name, field in form.fields.items():
            html += f"""
            <div class="form-group">
                <label for="{field_name}">{field_name.title()}:</label>
                <input type="text" id="{field_name}" name="{field_name}" value="{getattr(form.instance, field_name, '') if hasattr(form, 'instance') and form.instance else ''}">
            </div>
            """
        return html
    
    def _render_delete_confirmation_html(self, context: Dict[str, Any]) -> HTMLResponse:
        """Render delete confirmation HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Delete {context['model'].__name__} - Admin</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background: #417690; color: white; padding: 20px; margin-bottom: 20px; }}
                .content {{ max-width: 600px; margin: 0 auto; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 3px; margin-bottom: 20px; }}
                button {{ padding: 10px 20px; background: #dc3545; color: white; border: none; border-radius: 3px; cursor: pointer; }}
                .btn-secondary {{ background: #6c757d; margin-left: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Delete {context['model'].__name__}</h1>
            </div>
            <div class="content">
                <div class="warning">
                    <h2>Are you sure?</h2>
                    <p>Are you sure you want to delete "{context['object']}"?</p>
                    <p>This action cannot be undone.</p>
                </div>
                <form method="post">
                    <button type="submit">Yes, I'm sure</button>
                    <a href="{context['admin_path']}/{context['model'].__name__.lower()}/" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html)


# Global admin site instance
site = AdminSite()
admin_site = site


def register(model: Type, admin_class: Type = None, **options):
    """
    Register a model with the admin site.
    
    Args:
        model: The model class to register
        admin_class: The admin class to use
        **options: Additional options
    """
    site.register(model, admin_class, **options)


# Example usage:
def setup_admin(app: FastAPI, admin_path: str = "/admin"):
    """
    Set up admin interface for a FastAPI app.
    
    Args:
        app: The FastAPI app
        admin_path: The admin URL path (default: /admin)
    """
    # Create admin site with custom path
    admin_site = AdminSite(admin_path=admin_path)
    
    # Register models (example)
    # from myapp.models import User, Product
    # admin_site.register(User)
    # admin_site.register(Product)
    
    # Mount admin site
    admin_site.mount(app)
    
    return admin_site
