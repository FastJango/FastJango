"""
FastJango Media Files - Django-like media file handling.

This module provides media file handling for FastJango, similar to Django's
media file handling but adapted for FastAPI.
"""

import os
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import uuid

from fastapi import UploadFile, File
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError


class MediaFile:
    """Media file object similar to Django's media file."""
    
    def __init__(self, name: str, file_path: str, size: int = 0, 
                 content_type: Optional[str] = None, created_at: Optional[datetime] = None):
        """
        Initialize a media file.
        
        Args:
            name: File name
            file_path: File path
            size: File size in bytes
            content_type: File content type
            created_at: File creation time
        """
        self.name = name
        self.file_path = file_path
        self.size = size
        self.content_type = content_type or self._guess_content_type()
        self.created_at = created_at or datetime.now()
    
    def _guess_content_type(self) -> str:
        """Guess content type from file extension."""
        return mimetypes.guess_type(self.name)[0] or "application/octet-stream"
    
    @property
    def url(self) -> str:
        """Get file URL."""
        from fastjango.media.utils import get_media_url
        return get_media_url(self.name)
    
    @property
    def exists(self) -> bool:
        """Check if file exists."""
        return Path(self.file_path).exists()
    
    def delete(self) -> bool:
        """Delete the file."""
        try:
            Path(self.file_path).unlink()
            return True
        except Exception:
            return False
    
    def save(self, content: bytes) -> bool:
        """Save file content."""
        try:
            Path(self.file_path).write_bytes(content)
            return True
        except Exception:
            return False
    
    def read(self) -> bytes:
        """Read file content."""
        return Path(self.file_path).read_bytes()


class MediaStorage:
    """Base class for media storage backends."""
    
    def __init__(self, media_root: str = "media", media_url: str = "/media/"):
        """
        Initialize media storage.
        
        Args:
            media_root: Media root directory
            media_url: Media URL prefix
        """
        self.media_root = Path(media_root)
        self.media_url = media_url.rstrip('/')
        
        # Ensure media root exists
        self.media_root.mkdir(parents=True, exist_ok=True)
    
    def get_available_name(self, name: str) -> str:
        """Get available file name."""
        path = self.media_root / name
        
        if not path.exists():
            return name
        
        # Generate unique name
        name_parts = name.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
            counter = 1
            while True:
                new_name = f"{base_name}_{counter}.{extension}"
                if not (self.media_root / new_name).exists():
                    return new_name
                counter += 1
        else:
            counter = 1
            while True:
                new_name = f"{name}_{counter}"
                if not (self.media_root / new_name).exists():
                    return new_name
                counter += 1
    
    def save(self, name: str, content: bytes) -> str:
        """Save file content."""
        available_name = self.get_available_name(name)
        file_path = self.media_root / available_name
        
        file_path.write_bytes(content)
        return available_name
    
    def delete(self, name: str) -> bool:
        """Delete file."""
        file_path = self.media_root / name
        try:
            file_path.unlink()
            return True
        except Exception:
            return False
    
    def exists(self, name: str) -> bool:
        """Check if file exists."""
        return (self.media_root / name).exists()
    
    def get_file(self, name: str) -> Optional[MediaFile]:
        """Get media file object."""
        file_path = self.media_root / name
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return MediaFile(
            name=name,
            file_path=str(file_path),
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime)
        )
    
    def list_files(self, path: str = "") -> List[str]:
        """List files in directory."""
        dir_path = self.media_root / path
        if not dir_path.exists():
            return []
        
        files = []
        for item in dir_path.iterdir():
            if item.is_file():
                files.append(str(item.relative_to(self.media_root)))
        
        return files


class MediaFileHandler:
    """Handler for media file operations."""
    
    def __init__(self, storage: Optional[MediaStorage] = None):
        """
        Initialize media file handler.
        
        Args:
            storage: Media storage backend
        """
        self.storage = storage or MediaStorage()
    
    async def handle_upload(self, file: UploadFile) -> MediaFile:
        """
        Handle file upload.
        
        Args:
            file: Uploaded file
            
        Returns:
            Media file object
        """
        content = await file.read()
        name = self.storage.save(file.filename, content)
        
        return self.storage.get_file(name)
    
    def get_file(self, name: str) -> Optional[MediaFile]:
        """Get media file by name."""
        return self.storage.get_file(name)
    
    def delete_file(self, name: str) -> bool:
        """Delete media file by name."""
        return self.storage.delete(name)
    
    def list_files(self, path: str = "") -> List[str]:
        """List media files in directory."""
        return self.storage.list_files(path)
    
    def serve_file(self, name: str) -> Response:
        """Serve media file."""
        media_file = self.get_file(name)
        if not media_file:
            from fastjango.http import HttpResponse
            return HttpResponse("File not found", status_code=404)
        
        content = media_file.read()
        return Response(
            content=content,
            media_type=media_file.content_type,
            headers={"Content-Length": str(media_file.size)}
        )


def generate_unique_filename(original_name: str) -> str:
    """Generate unique filename."""
    # Generate hash from original name and timestamp
    timestamp = str(datetime.now().timestamp())
    hash_input = f"{original_name}{timestamp}".encode()
    hash_value = hashlib.md5(hash_input).hexdigest()[:8]
    
    # Get file extension
    name_parts = original_name.rsplit('.', 1)
    if len(name_parts) == 2:
        base_name, extension = name_parts
        return f"{hash_value}.{extension}"
    else:
        return hash_value


def validate_file_type(file: UploadFile, allowed_types: List[str]) -> bool:
    """Validate file type."""
    content_type = file.content_type or ""
    return any(allowed_type in content_type for allowed_type in allowed_types)


def validate_file_size(file: UploadFile, max_size: int) -> bool:
    """Validate file size."""
    # Note: This is a basic check. For production, you'd want to check actual file size
    return True  # Simplified for now


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
            filename = base_name[:255-len(extension)-1] + '.' + extension
        else:
            filename = filename[:255]
    
    return filename
