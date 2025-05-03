"""
StartApp command - Creates a new FastJango app
"""

import os
import re
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

from fastjango.core.exceptions import AppCreationError
from fastjango.core.logging import Logger

# Get logger
logger = Logger("fastjango.cli.commands.startapp")

# App templates path
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "app_template"


def validate_app_name(name: str) -> None:
    """
    Validate the app name.
    
    Args:
        name: The app name to validate
        
    Raises:
        AppCreationError: If the app name is invalid
    """
    if not name:
        raise AppCreationError("App name cannot be empty")
    
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
        raise AppCreationError(
            "App name must start with a letter and contain only letters, numbers, and underscores"
        )
    
    # Reserved keywords
    python_keywords = [
        "False", "None", "True", "and", "as", "assert", "break", "class", "continue", 
        "def", "del", "elif", "else", "except", "finally", "for", "from", "global", 
        "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", 
        "return", "try", "while", "with", "yield"
    ]
    
    if name.lower() in [k.lower() for k in python_keywords]:
        raise AppCreationError(f"App name '{name}' is a Python reserved keyword")
    
    if name.lower() in ["fastjango", "django", "fastapi", "app", "project", "core", "settings"]:
        raise AppCreationError(f"App name '{name}' is a reserved framework name")


def create_context(app_name: str) -> Dict[str, Any]:
    """
    Create the template context for app creation.
    
    Args:
        app_name: The name of the app
        
    Returns:
        A dictionary with the template context
    """
    return {
        "app_name": app_name,
        "app_name_snake": app_name.replace("-", "_").lower(),
        "app_name_camel": "".join(word.capitalize() for word in app_name.replace("-", "_").split("_")),
        "fastjango_version": "0.1.1"
    }


def create_app(app_name: str, target_dir: Path) -> None:
    """
    Create a new FastJango app.
    
    Args:
        app_name: The name of the app
        target_dir: The directory to create the app in
        
    Raises:
        AppCreationError: If app creation fails
    """
    try:
        # Validate app name
        validate_app_name(app_name)
        
        # Create app directory
        app_dir = target_dir / app_name.replace("-", "_").lower()
        
        # Check if directory already exists
        if app_dir.exists():
            raise AppCreationError(f"Directory '{app_dir}' already exists")
        
        # Check if inside a FastJango project
        if not is_fastjango_project(target_dir):
            logger.warning("Not inside a FastJango project, some app features may not work")
        
        # Create app directory structure
        logger.debug(f"Creating app directory structure at {app_dir}")
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Create context for templating
        context = create_context(app_name)
        
        # Copy template files
        if not TEMPLATES_DIR.exists():
            # If templates directory doesn't exist, create app files from scratch
            logger.warning("Template directory not found, creating app files from scratch")
            
            # Create app files
            create_app_files(app_dir, context)
        else:
            # Copy and process template files
            logger.debug("Copying template files")
            copy_template_files(TEMPLATES_DIR, app_dir, context)
        
        logger.info(f"App '{app_name}' created at {app_dir}")
        
        # Provide advice for next steps
        logger.info(f"Don't forget to add '{app_name.replace('-', '_').lower()}' to INSTALLED_APPS in settings.py")
        
    except AppCreationError as e:
        # Re-raise app creation errors
        raise e
    except Exception as e:
        # Log and wrap other exceptions
        logger.error(f"Failed to create app: {str(e)}", exc_info=True)
        raise AppCreationError(f"Failed to create app: {str(e)}")


def is_fastjango_project(directory: Path) -> bool:
    """
    Check if the directory is inside a FastJango project.
    
    Args:
        directory: The directory to check
        
    Returns:
        True if inside a FastJango project, False otherwise
    """
    # Look for manage.py in current or parent directories
    current_dir = directory
    
    # Check up to 3 levels up
    for _ in range(4):
        if (current_dir / "manage.py").exists():
            return True
        
        # Move up one directory
        parent_dir = current_dir.parent
        if parent_dir == current_dir:  # Reached root
            break
        
        current_dir = parent_dir
    
    return False


def create_app_files(app_dir: Path, context: Dict[str, Any]) -> None:
    """
    Create app files from scratch when no templates are available.
    
    Args:
        app_dir: The app directory
        context: The template context
    """
    app_name = context["app_name"]
    app_name_snake = context["app_name_snake"]
    app_name_camel = context["app_name_camel"]
    
    # Create __init__.py
    (app_dir / "__init__.py").write_text("")
    
    # Create models.py
    models_content = f'''"""
Models for {app_name} app.
"""

from fastjango.db import models
from fastjango.core.exceptions import ValidationError


class {app_name_camel}Model(models.Model):
    """
    Example model for {app_name} app.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "{app_name_camel}"
        verbose_name_plural = "{app_name_camel}s"
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Custom validation logic.
        """
        if self.name.lower() == "test":
            raise ValidationError({{"name": "Name cannot be 'test'"}})
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
'''
    (app_dir / "models.py").write_text(models_content)
    
    # Create routes.py
    routes_content = f'''"""
API routes for {app_name} app.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

from fastjango.core.dependencies import get_current_user
from .schemas import {app_name_camel}Create, {app_name_camel}Read, {app_name_camel}Update
from .services import {app_name_camel}Service

router = APIRouter(prefix="/{app_name_snake}", tags=["{app_name}"])
service = {app_name_camel}Service()


@router.get("/", response_model=List[{app_name_camel}Read])
async def list_{app_name_snake}s(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    List all {app_name}s.
    """
    return await service.get_all(skip=skip, limit=limit)


@router.post("/", response_model={app_name_camel}Read, status_code=status.HTTP_201_CREATED)
async def create_{app_name_snake}(
    item: {app_name_camel}Create,
    current_user = Depends(get_current_user)
):
    """
    Create a new {app_name}.
    """
    return await service.create(item)


@router.get("/{{item_id}}", response_model={app_name_camel}Read)
async def read_{app_name_snake}(
    item_id: int,
    current_user = Depends(get_current_user)
):
    """
    Get a specific {app_name} by ID.
    """
    item = await service.get_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{app_name_camel} not found"
        )
    return item


@router.put("/{{item_id}}", response_model={app_name_camel}Read)
async def update_{app_name_snake}(
    item_id: int,
    item: {app_name_camel}Update,
    current_user = Depends(get_current_user)
):
    """
    Update a {app_name}.
    """
    updated_item = await service.update(item_id, item)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{app_name_camel} not found"
        )
    return updated_item


@router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{app_name_snake}(
    item_id: int,
    current_user = Depends(get_current_user)
):
    """
    Delete a {app_name}.
    """
    success = await service.delete(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{app_name_camel} not found"
        )
    return {{}}
'''
    (app_dir / "routes.py").write_text(routes_content)
    
    # Create schemas.py
    schemas_content = f'''"""
Pydantic schemas for {app_name} app.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class {app_name_camel}Base(BaseModel):
    """
    Base schema for {app_name_camel}.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=0, max_length=1000)


class {app_name_camel}Create({app_name_camel}Base):
    """
    Schema for creating a {app_name_camel}.
    """
    pass


class {app_name_camel}Update(BaseModel):
    """
    Schema for updating a {app_name_camel}.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=0, max_length=1000)


class {app_name_camel}Read({app_name_camel}Base):
    """
    Schema for reading a {app_name_camel}.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
'''
    (app_dir / "schemas.py").write_text(schemas_content)
    
    # Create services.py
    services_content = f'''"""
Services for {app_name} app.
"""

from typing import List, Optional
import logging

from fastjango.core.exceptions import ServiceError
from .models import {app_name_camel}Model
from .schemas import {app_name_camel}Create, {app_name_camel}Update

logger = logging.getLogger(__name__)


class {app_name_camel}Service:
    """
    Service for handling {app_name_camel} operations.
    """
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{app_name_camel}Model]:
        """
        Get all {app_name_camel} objects.
        """
        try:
            return {app_name_camel}Model.objects.all()[skip:skip+limit]
        except Exception as e:
            logger.error(f"Error fetching {app_name_camel} list: {{str(e)}}", exc_info=True)
            raise ServiceError(f"Failed to fetch {app_name_camel} list")
    
    async def get_by_id(self, item_id: int) -> Optional[{app_name_camel}Model]:
        """
        Get a {app_name_camel} by ID.
        """
        try:
            return {app_name_camel}Model.objects.filter(id=item_id).first()
        except Exception as e:
            logger.error(f"Error fetching {app_name_camel} with ID {{item_id}}: {{str(e)}}", exc_info=True)
            raise ServiceError(f"Failed to fetch {app_name_camel}")
    
    async def create(self, item: {app_name_camel}Create) -> {app_name_camel}Model:
        """
        Create a new {app_name_camel}.
        """
        try:
            return {app_name_camel}Model.objects.create(**item.dict())
        except Exception as e:
            logger.error(f"Error creating {app_name_camel}: {{str(e)}}", exc_info=True)
            raise ServiceError(f"Failed to create {app_name_camel}")
    
    async def update(self, item_id: int, item: {app_name_camel}Update) -> Optional[{app_name_camel}Model]:
        """
        Update a {app_name_camel}.
        """
        try:
            obj = await self.get_by_id(item_id)
            if not obj:
                return None
            
            # Update fields that are present in the request
            for field, value in item.dict(exclude_unset=True).items():
                setattr(obj, field, value)
            
            obj.save()
            return obj
        except Exception as e:
            logger.error(f"Error updating {app_name_camel} with ID {{item_id}}: {{str(e)}}", exc_info=True)
            raise ServiceError(f"Failed to update {app_name_camel}")
    
    async def delete(self, item_id: int) -> bool:
        """
        Delete a {app_name_camel}.
        """
        try:
            obj = await self.get_by_id(item_id)
            if not obj:
                return False
            
            obj.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting {app_name_camel} with ID {{item_id}}: {{str(e)}}", exc_info=True)
            raise ServiceError(f"Failed to delete {app_name_camel}")
'''
    (app_dir / "services.py").write_text(services_content)
    
    # Create tests directory and test files
    tests_dir = app_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create tests/__init__.py
    (tests_dir / "__init__.py").write_text("")
    
    # Create tests/test_models.py
    test_models_content = f'''"""
Tests for {app_name} models.
"""

import pytest
from django.test import TestCase
from fastjango.core.exceptions import ValidationError

from ..models import {app_name_camel}Model


class {app_name_camel}ModelTests(TestCase):
    """
    Tests for {app_name_camel}Model.
    """
    
    def test_create_{app_name_snake}(self):
        """
        Test creating a {app_name_camel}.
        """
        obj = {app_name_camel}Model.objects.create(
            name="Test {app_name_camel}",
            description="This is a test"
        )
        self.assertEqual(obj.name, "Test {app_name_camel}")
        self.assertEqual(obj.description, "This is a test")
        
    def test_validation(self):
        """
        Test validation logic.
        """
        obj = {app_name_camel}Model(name="test")
        with self.assertRaises(ValidationError):
            obj.save()
'''
    (tests_dir / "test_models.py").write_text(test_models_content)
    
    # Create tests/test_routes.py
    test_routes_content = f'''"""
Tests for {app_name} routes.
"""

import pytest
from fastapi.testclient import TestClient
from fastjango.test import TestCase

from ..routes import router


class {app_name_camel}RoutesTests(TestCase):
    """
    Tests for {app_name_camel} routes.
    """
    
    def setUp(self):
        """
        Set up test client.
        """
        self.client = TestClient(router)
        
    def test_list_{app_name_snake}s(self):
        """
        Test listing {app_name_camel}s.
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
    def test_create_{app_name_snake}(self):
        """
        Test creating a {app_name_camel}.
        """
        data = {{
            "name": "Test {app_name_camel}",
            "description": "This is a test"
        }}
        response = self.client.post("/", json=data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], data["name"])
'''
    (tests_dir / "test_routes.py").write_text(test_routes_content)


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
            target_path_str = target_path_str.replace(f"{{{{app_name}}}}", context["app_name"])
            target_path_str = target_path_str.replace(f"{{{{app_name_snake}}}}", context["app_name_snake"])
            target_path_str = target_path_str.replace(f"{{{{app_name_camel}}}}", context["app_name_camel"])
        
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
                dest_file_str = dest_file_str.replace(f"{{{{app_name}}}}", context["app_name"])
                dest_file_str = dest_file_str.replace(f"{{{{app_name_snake}}}}", context["app_name_snake"])
                dest_file_str = dest_file_str.replace(f"{{{{app_name_camel}}}}", context["app_name_camel"])
            
            dest_file = Path(dest_file_str)
            
            # Copy and process file content
            if file.endswith((".py", ".html", ".txt", ".md", ".ini", ".yml", ".yaml", ".json")):
                # Read source file
                content = src_file.read_text(encoding="utf-8")
                
                # Replace placeholders
                for key, value in context.items():
                    content = content.replace(f"{{{{app_name}}}}", context["app_name"])
                    content = content.replace(f"{{{{app_name_snake}}}}", context["app_name_snake"])
                    content = content.replace(f"{{{{app_name_camel}}}}", context["app_name_camel"])
                
                # Write processed content
                dest_file.write_text(content, encoding="utf-8")
            else:
                # Binary file, just copy
                shutil.copy2(src_file, dest_file) 