"""
StartProject command - Creates a new FastJango project
"""

import os
import re
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

from fastjango.core.exceptions import ProjectCreationError
from fastjango.core.logging import Logger

# Get logger
logger = Logger("fastjango.cli.commands.startproject")

# Project templates path
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "project_template"


def validate_project_name(name: str) -> None:
    """
    Validate the project name.
    
    Args:
        name: The project name to validate
        
    Raises:
        ProjectCreationError: If the project name is invalid
    """
    if not name:
        raise ProjectCreationError("Project name cannot be empty")
    
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        raise ProjectCreationError(
            "Project name must start with a letter and contain only letters, numbers, and underscores"
        )
    
    # Reserved keywords
    python_keywords = [
        "False", "None", "True", "and", "as", "assert", "break", "class", "continue", 
        "def", "del", "elif", "else", "except", "finally", "for", "from", "global", 
        "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", 
        "return", "try", "while", "with", "yield"
    ]
    
    if name.lower() in [k.lower() for k in python_keywords]:
        raise ProjectCreationError(f"Project name '{name}' is a Python reserved keyword")
    
    if name.lower() in ["fastjango", "django", "fastapi", "app", "test"]:
        raise ProjectCreationError(f"Project name '{name}' is a reserved framework name")


def create_context(project_name: str) -> Dict[str, Any]:
    """
    Create the template context for project creation.
    
    Args:
        project_name: The name of the project
        
    Returns:
        A dictionary with the template context
    """
    return {
        "project_name": project_name,
        "project_name_snake": project_name.replace("-", "_").lower(),
        "fastjango_version": "0.1.1"
    }


def create_project(project_name: str, target_dir: Path) -> None:
    """
    Create a new FastJango project.
    
    Args:
        project_name: The name of the project
        target_dir: The directory to create the project in
        
    Raises:
        ProjectCreationError: If project creation fails
    """
    try:
        # Validate project name
        validate_project_name(project_name)
        
        # Create project directory
        project_dir = target_dir / project_name
        project_root = project_dir / project_name.replace("-", "_").lower()
        
        # Check if directory already exists
        if project_dir.exists():
            raise ProjectCreationError(f"Directory '{project_dir}' already exists")
        
        # Create project directory structure
        logger.debug(f"Creating project directory structure at {project_dir}")
        project_dir.mkdir(parents=True, exist_ok=True)
        project_root.mkdir(parents=True, exist_ok=True)
        (project_dir / "templates").mkdir(parents=True, exist_ok=True)
        
        # Create context for templating
        context = create_context(project_name)
        
        # Copy template files
        if not TEMPLATES_DIR.exists():
            # If templates directory doesn't exist, create project files from scratch
            logger.warning("Template directory not found, creating project files from scratch")
            
            # Create project files
            create_project_files(project_dir, project_root, context)
        else:
            # Copy and process template files
            logger.debug("Copying template files")
            copy_template_files(TEMPLATES_DIR, project_dir, context)
        
        logger.info(f"Project '{project_name}' created at {project_dir}")
        
    except ProjectCreationError as e:
        # Re-raise project creation errors
        raise e
    except Exception as e:
        # Log and wrap other exceptions
        logger.error(f"Failed to create project: {str(e)}", exc_info=True)
        raise ProjectCreationError(f"Failed to create project: {str(e)}")


def create_project_files(project_dir: Path, project_root: Path, context: Dict[str, Any]) -> None:
    """
    Create project files from scratch when no templates are available.
    
    Args:
        project_dir: The project directory
        project_root: The project root directory
        context: The template context
    """
    project_name = context["project_name"]
    project_name_snake = context["project_name_snake"]
    
    # Create __init__.py files
    (project_root / "__init__.py").write_text("")
    
    # Create settings.py
    settings_content = f'''"""
Settings for {project_name} project.
"""

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-fastjango-development-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    # FastJango apps
    "{project_name_snake}.core",
    
    # Third-party apps
    
    # Your apps
]

# Middleware
MIDDLEWARE = [
    "fastjango.middleware.security.SecurityMiddleware",
    "fastjango.middleware.session.SessionMiddleware",
    "fastapi.middleware.cors.CORSMiddleware",
    "fastjango.middleware.common.CommonMiddleware",
    "fastjango.middleware.csrf.CsrfMiddleware",
    "fastjango.middleware.auth.AuthenticationMiddleware",
    "fastjango.middleware.messages.MessageMiddleware",
]

ROOT_URLCONF = "{project_name_snake}.urls"

TEMPLATES = [
    {{
        "BACKEND": "fastjango.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {{
            "context_processors": [
                "fastjango.template.context_processors.debug",
                "fastjango.template.context_processors.request",
                "fastjango.template.context_processors.auth",
                "fastjango.template.context_processors.messages",
            ],
        }},
    }},
]

WSGI_APPLICATION = "{project_name_snake}.wsgi.application"
ASGI_APPLICATION = "{project_name_snake}.asgi.application"

# Database
DATABASES = {{
    "default": {{
        "ENGINE": "fastjango.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }}
}}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {{
        "NAME": "fastjango.auth.password_validation.UserAttributeSimilarityValidator",
    }},
    {{
        "NAME": "fastjango.auth.password_validation.MinimumLengthValidator",
    }},
    {{
        "NAME": "fastjango.auth.password_validation.CommonPasswordValidator",
    }},
    {{
        "NAME": "fastjango.auth.password_validation.NumericPasswordValidator",
    }},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "fastjango.db.models.BigAutoField"
'''
    (project_root / "settings.py").write_text(settings_content)
    
    # Create urls.py
    urls_content = f'''"""
URL configuration for {project_name} project.
"""

from fastjango.urls import path, include
from fastjango.http import JsonResponse

# Define API endpoints
def index(request):
    return JsonResponse({{"message": "Welcome to {project_name}"}})

urlpatterns = [
    path("/", index),
    path("/api", include("{project_name_snake}.api.urls")),
]
'''
    (project_root / "urls.py").write_text(urls_content)
    
    # Create asgi.py
    asgi_content = f'''"""
ASGI config for {project_name} project.
"""

import os
from fastjango.core.asgi import get_asgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{project_name_snake}.settings")

application = get_asgi_application()
'''
    (project_root / "asgi.py").write_text(asgi_content)
    
    # Create wsgi.py
    wsgi_content = f'''"""
WSGI config for {project_name} project.
"""

import os
from fastjango.core.wsgi import get_wsgi_application

os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{project_name_snake}.settings")

application = get_wsgi_application()
'''
    (project_root / "wsgi.py").write_text(wsgi_content)
    
    # Create api directory and urls.py
    api_dir = project_root / "api"
    api_dir.mkdir(parents=True, exist_ok=True)
    (api_dir / "__init__.py").write_text("")
    
    api_urls_content = f'''"""
API URLs for {project_name} project.
"""

from fastjango.urls import path
from fastjango.http import JsonResponse

def api_root(request):
    return JsonResponse({{"message": "{project_name} API v1.0"}})

urlpatterns = [
    path("/", api_root),
]
'''
    (api_dir / "urls.py").write_text(api_urls_content)
    
    # Create manage.py
    manage_content = f'''#!/usr/bin/env python
"""
FastJango's command-line utility for administrative tasks.
"""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault("FASTJANGO_SETTINGS_MODULE", "{project_name_snake}.settings")
    try:
        from fastjango.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import FastJango. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'''
    (project_dir / "manage.py").write_text(manage_content)
    os.chmod(project_dir / "manage.py", 0o755)  # Make executable
    
    # Create requirements.txt
    requirements_content = "fastjango>=0.1.1,<0.2.0\n"
    (project_dir / "requirements.txt").write_text(requirements_content)


def copy_template_files(templates_dir: Path, target_dir: Path, context: Dict[str, Any]) -> None:
    """
    Copy template files to the target directory, replacing placeholders.
    
    Args:
        templates_dir: The templates directory
        target_dir: The target directory
        context: The template context
    """
    # Walk through template directory
    for root, dirs, files in os.walk(templates_dir):
        # Calculate relative path
        rel_path = os.path.relpath(root, templates_dir)
        if rel_path == ".":
            rel_path = ""
        
        # Process directory structure
        target_path = target_dir / rel_path
        
        # Replace placeholders in path
        target_path_str = str(target_path)
        for key, value in context.items():
            target_path_str = target_path_str.replace(f"{{{{project_name}}}}", context["project_name"])
            target_path_str = target_path_str.replace(f"{{{{project_name_snake}}}}", context["project_name_snake"])
        
        target_path = Path(target_path_str)
        
        # Create directory if it doesn't exist
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
        
        # Process files
        for file in files:
            # Skip __pycache__ directories and .pyc files
            if "__pycache__" in root or file.endswith(".pyc"):
                continue
            
            # Get source and destination file paths
            src_file = Path(root) / file
            dest_file = target_path / file
            
            # Replace placeholders in filename
            dest_file_str = str(dest_file)
            for key, value in context.items():
                dest_file_str = dest_file_str.replace(f"{{{{project_name}}}}", context["project_name"])
                dest_file_str = dest_file_str.replace(f"{{{{project_name_snake}}}}", context["project_name_snake"])
            
            dest_file = Path(dest_file_str)
            
            # Copy and process file content
            if file.endswith((".py", ".html", ".txt", ".md", ".ini", ".yml", ".yaml", ".json")):
                # Read source file
                content = src_file.read_text(encoding="utf-8")
                
                # Replace placeholders
                for key, value in context.items():
                    content = content.replace(f"{{{{project_name}}}}", context["project_name"])
                    content = content.replace(f"{{{{project_name_snake}}}}", context["project_name_snake"])
                    content = content.replace(f"{{{{fastjango_version}}}}", context["fastjango_version"])
                
                # Write processed content
                dest_file.write_text(content, encoding="utf-8")
                
                # Make file executable if it's manage.py
                if file == "manage.py":
                    os.chmod(dest_file, 0o755)
            else:
                # Binary file, just copy
                shutil.copy2(src_file, dest_file) 