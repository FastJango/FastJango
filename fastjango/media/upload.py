"""
FastJango Media Upload - Django-like file upload handling.

This module provides file upload handling for FastJango, similar to Django's
file upload handling but adapted for FastAPI.
"""

import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime

from fastapi import UploadFile, File, Form
from PIL import Image
import io

from fastjango.core.exceptions import FastJangoError
from .files import MediaFile, MediaStorage, MediaFileHandler


class FileUploadHandler:
    """Handler for general file uploads."""
    
    def __init__(self, storage: Optional[MediaStorage] = None,
                 max_size: int = 10 * 1024 * 1024,  # 10MB
                 allowed_types: Optional[List[str]] = None):
        """
        Initialize file upload handler.
        
        Args:
            storage: Media storage backend
            max_size: Maximum file size in bytes
            allowed_types: Allowed file types
        """
        self.storage = storage or MediaStorage()
        self.handler = MediaFileHandler(self.storage)
        self.max_size = max_size
        self.allowed_types = allowed_types or ["*/*"]
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file."""
        # Check file size (basic check)
        if file.size and file.size > self.max_size:
            return False
        
        # Check file type
        if self.allowed_types != ["*/*"]:
            content_type = file.content_type or ""
            if not any(allowed_type in content_type for allowed_type in self.allowed_types):
                return False
        
        return True
    
    async def handle_upload(self, file: UploadFile) -> MediaFile:
        """
        Handle file upload.
        
        Args:
            file: Uploaded file
            
        Returns:
            Media file object
        """
        if not self.validate_file(file):
            raise FastJangoError("Invalid file")
        
        return await self.handler.handle_upload(file)
    
    async def handle_multiple_uploads(self, files: List[UploadFile]) -> List[MediaFile]:
        """
        Handle multiple file uploads.
        
        Args:
            files: List of uploaded files
            
        Returns:
            List of media file objects
        """
        media_files = []
        
        for file in files:
            if self.validate_file(file):
                media_file = await self.handler.handle_upload(file)
                media_files.append(media_file)
        
        return media_files


class ImageUploadHandler(FileUploadHandler):
    """Handler for image uploads with processing."""
    
    def __init__(self, storage: Optional[MediaStorage] = None,
                 max_size: int = 5 * 1024 * 1024,  # 5MB
                 allowed_formats: Optional[List[str]] = None,
                 max_width: Optional[int] = None,
                 max_height: Optional[int] = None,
                 quality: int = 85):
        """
        Initialize image upload handler.
        
        Args:
            storage: Media storage backend
            max_size: Maximum file size in bytes
            allowed_formats: Allowed image formats
            max_width: Maximum image width
            max_height: Maximum image height
            quality: JPEG quality (1-100)
        """
        super().__init__(storage, max_size, ["image/*"])
        
        self.allowed_formats = allowed_formats or ["JPEG", "PNG", "GIF", "WEBP"]
        self.max_width = max_width
        self.max_height = max_height
        self.quality = max(1, min(100, quality))
    
    def validate_image(self, file: UploadFile) -> bool:
        """Validate uploaded image."""
        if not super().validate_file(file):
            return False
        
        # Check file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                return False
        
        return True
    
    def process_image(self, content: bytes) -> bytes:
        """Process image content."""
        try:
            # Open image
            image = Image.open(io.BytesIO(content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if necessary
            if self.max_width or self.max_height:
                width, height = image.size
                
                if self.max_width and width > self.max_width:
                    ratio = self.max_width / width
                    height = int(height * ratio)
                    width = self.max_width
                
                if self.max_height and height > self.max_height:
                    ratio = self.max_height / height
                    width = int(width * ratio)
                    height = self.max_height
                
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            
            # Save processed image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=self.quality, optimize=True)
            output.seek(0)
            
            return output.getvalue()
        
        except Exception as e:
            raise FastJangoError(f"Failed to process image: {e}")
    
    async def handle_upload(self, file: UploadFile) -> MediaFile:
        """
        Handle image upload with processing.
        
        Args:
            file: Uploaded image file
            
        Returns:
            Media file object
        """
        if not self.validate_image(file):
            raise FastJangoError("Invalid image file")
        
        # Read file content
        content = await file.read()
        
        # Process image
        processed_content = self.process_image(content)
        
        # Save processed image
        name = self.storage.save(file.filename, processed_content)
        
        return self.storage.get_file(name)


class FormFileUploadHandler:
    """Handler for form-based file uploads."""
    
    def __init__(self, storage: Optional[MediaStorage] = None):
        """
        Initialize form file upload handler.
        
        Args:
            storage: Media storage backend
        """
        self.storage = storage or MediaStorage()
        self.handler = MediaFileHandler(self.storage)
    
    async def handle_form_upload(self, file: UploadFile, 
                               additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle form-based file upload.
        
        Args:
            file: Uploaded file
            additional_data: Additional form data
            
        Returns:
            Upload result dictionary
        """
        try:
            media_file = await self.handler.handle_upload(file)
            
            result = {
                'success': True,
                'file': {
                    'name': media_file.name,
                    'url': media_file.url,
                    'size': media_file.size,
                    'content_type': media_file.content_type,
                    'created_at': media_file.created_at.isoformat()
                }
            }
            
            if additional_data:
                result['form_data'] = additional_data
            
            return result
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_multipart_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle multipart form data with files.
        
        Args:
            form_data: Form data dictionary
            
        Returns:
            Upload result dictionary
        """
        results = {
            'success': True,
            'files': [],
            'form_data': {}
        }
        
        for key, value in form_data.items():
            if isinstance(value, UploadFile):
                # Handle file upload
                file_result = await self.handle_form_upload(value)
                if file_result['success']:
                    results['files'].append(file_result['file'])
                else:
                    results['success'] = False
                    results['errors'] = results.get('errors', [])
                    results['errors'].append(file_result['error'])
            else:
                # Store form data
                results['form_data'][key] = value
        
        return results


def create_upload_endpoint(app, upload_path: str = "/upload/", 
                          max_size: int = 10 * 1024 * 1024,
                          allowed_types: Optional[List[str]] = None):
    """
    Create a file upload endpoint.
    
    Args:
        app: FastAPI application
        upload_path: Upload endpoint path
        max_size: Maximum file size
        allowed_types: Allowed file types
    """
    handler = FileUploadHandler(max_size=max_size, allowed_types=allowed_types)
    
    @app.post(upload_path)
    async def upload_file(file: UploadFile = File(...)):
        """Upload a file."""
        try:
            media_file = await handler.handle_upload(file)
            return {
                'success': True,
                'file': {
                    'name': media_file.name,
                    'url': media_file.url,
                    'size': media_file.size,
                    'content_type': media_file.content_type
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    return upload_file


def create_image_upload_endpoint(app, upload_path: str = "/upload/image/",
                               max_size: int = 5 * 1024 * 1024,
                               max_width: Optional[int] = None,
                               max_height: Optional[int] = None):
    """
    Create an image upload endpoint.
    
    Args:
        app: FastAPI application
        upload_path: Upload endpoint path
        max_size: Maximum file size
        max_width: Maximum image width
        max_height: Maximum image height
    """
    handler = ImageUploadHandler(
        max_size=max_size,
        max_width=max_width,
        max_height=max_height
    )
    
    @app.post(upload_path)
    async def upload_image(file: UploadFile = File(...)):
        """Upload an image."""
        try:
            media_file = await handler.handle_upload(file)
            return {
                'success': True,
                'file': {
                    'name': media_file.name,
                    'url': media_file.url,
                    'size': media_file.size,
                    'content_type': media_file.content_type
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    return upload_image
