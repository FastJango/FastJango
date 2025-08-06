"""
FastJango Media Storage - Django-like media storage backends.

This module provides media storage backends for FastJango, similar to Django's
media storage backends but adapted for FastAPI.
"""

import os
import shutil
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime

from fastjango.core.exceptions import FastJangoError
from .files import MediaFile, MediaStorage


class FileSystemStorage(MediaStorage):
    """File system storage backend."""
    
    def __init__(self, media_root: str = "media", media_url: str = "/media/",
                 base_url: Optional[str] = None):
        """
        Initialize file system storage.
        
        Args:
            media_root: Media root directory
            media_url: Media URL prefix
            base_url: Base URL for file serving
        """
        super().__init__(media_root, media_url)
        self.base_url = base_url or media_url
    
    def url(self, name: str) -> str:
        """Get file URL."""
        return f"{self.base_url.rstrip('/')}/{name}"
    
    def size(self, name: str) -> int:
        """Get file size."""
        file_path = self.media_root / name
        if file_path.exists():
            return file_path.stat().st_size
        return 0
    
    def get_accessed_time(self, name: str) -> datetime:
        """Get file accessed time."""
        file_path = self.media_root / name
        if file_path.exists():
            return datetime.fromtimestamp(file_path.stat().st_atime)
        return datetime.now()
    
    def get_created_time(self, name: str) -> datetime:
        """Get file created time."""
        file_path = self.media_root / name
        if file_path.exists():
            return datetime.fromtimestamp(file_path.stat().st_ctime)
        return datetime.now()
    
    def get_modified_time(self, name: str) -> datetime:
        """Get file modified time."""
        file_path = self.media_root / name
        if file_path.exists():
            return datetime.fromtimestamp(file_path.stat().st_mtime)
        return datetime.now()


class MemoryStorage(MediaStorage):
    """In-memory storage backend for testing."""
    
    def __init__(self):
        """Initialize memory storage."""
        super().__init__("memory", "/memory/")
        self._files: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
    
    def save(self, name: str, content: bytes) -> str:
        """Save file content to memory."""
        available_name = self.get_available_name(name)
        self._files[available_name] = content
        self._metadata[available_name] = {
            'size': len(content),
            'created_at': datetime.now(),
            'content_type': self._guess_content_type(name)
        }
        return available_name
    
    def delete(self, name: str) -> bool:
        """Delete file from memory."""
        if name in self._files:
            del self._files[name]
            del self._metadata[name]
            return True
        return False
    
    def exists(self, name: str) -> bool:
        """Check if file exists in memory."""
        return name in self._files
    
    def get_file(self, name: str) -> Optional[MediaFile]:
        """Get media file object from memory."""
        if name not in self._files:
            return None
        
        metadata = self._metadata[name]
        return MediaFile(
            name=name,
            file_path=f"memory://{name}",
            size=metadata['size'],
            content_type=metadata['content_type'],
            created_at=metadata['created_at']
        )
    
    def list_files(self, path: str = "") -> List[str]:
        """List files in memory."""
        return list(self._files.keys())
    
    def _guess_content_type(self, name: str) -> str:
        """Guess content type from filename."""
        import mimetypes
        return mimetypes.guess_type(name)[0] or "application/octet-stream"


class TemporaryStorage(MediaStorage):
    """Temporary storage backend for temporary files."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize temporary storage.
        
        Args:
            temp_dir: Temporary directory path
        """
        import tempfile
        temp_dir = temp_dir or tempfile.gettempdir()
        super().__init__(temp_dir, "/temp/")
    
    def cleanup(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files cleaned up
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        for file_path in self.media_root.rglob("*"):
            if file_path.is_file():
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                    except Exception:
                        pass
        
        return cleaned_count


class ChunkedStorage(MediaStorage):
    """Storage backend for handling large files in chunks."""
    
    def __init__(self, media_root: str = "media", media_url: str = "/media/",
                 chunk_size: int = 1024 * 1024):  # 1MB chunks
        """
        Initialize chunked storage.
        
        Args:
            media_root: Media root directory
            media_url: Media URL prefix
            chunk_size: Size of each chunk in bytes
        """
        super().__init__(media_root, media_url)
        self.chunk_size = chunk_size
    
    def save_chunk(self, name: str, chunk_data: bytes, chunk_index: int) -> bool:
        """
        Save a chunk of file data.
        
        Args:
            name: File name
            chunk_data: Chunk data
            chunk_index: Chunk index
            
        Returns:
            True if chunk saved successfully
        """
        chunk_dir = self.media_root / f"{name}_chunks"
        chunk_dir.mkdir(exist_ok=True)
        
        chunk_file = chunk_dir / f"chunk_{chunk_index:06d}"
        chunk_file.write_bytes(chunk_data)
        
        return True
    
    def assemble_file(self, name: str, total_chunks: int) -> bool:
        """
        Assemble file from chunks.
        
        Args:
            name: File name
            total_chunks: Total number of chunks
            
        Returns:
            True if file assembled successfully
        """
        chunk_dir = self.media_root / f"{name}_chunks"
        if not chunk_dir.exists():
            return False
        
        # Assemble file from chunks
        file_path = self.media_root / name
        with open(file_path, 'wb') as output_file:
            for i in range(total_chunks):
                chunk_file = chunk_dir / f"chunk_{i:06d}"
                if chunk_file.exists():
                    output_file.write(chunk_file.read_bytes())
        
        # Clean up chunks
        shutil.rmtree(chunk_dir)
        
        return True
    
    def get_chunk_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about file chunks.
        
        Args:
            name: File name
            
        Returns:
            Chunk information dictionary
        """
        chunk_dir = self.media_root / f"{name}_chunks"
        if not chunk_dir.exists():
            return {}
        
        chunk_files = sorted(chunk_dir.glob("chunk_*"))
        return {
            'total_chunks': len(chunk_files),
            'chunk_size': self.chunk_size,
            'chunks_exist': [f.name for f in chunk_files]
        }


def get_storage_class(storage_class_name: str):
    """
    Get storage class by name.
    
    Args:
        storage_class_name: Storage class name
        
    Returns:
        Storage class
    """
    storage_classes = {
        'filesystem': FileSystemStorage,
        'memory': MemoryStorage,
        'temporary': TemporaryStorage,
        'chunked': ChunkedStorage
    }
    
    return storage_classes.get(storage_class_name, FileSystemStorage)


def create_storage(settings: Dict[str, Any]) -> MediaStorage:
    """
    Create storage instance from settings.
    
    Args:
        settings: Settings dictionary
        
    Returns:
        Media storage instance
    """
    storage_class_name = settings.get("MEDIA_STORAGE", "filesystem")
    storage_class = get_storage_class(storage_class_name)
    
    storage_kwargs = {
        'media_root': settings.get("MEDIA_ROOT", "media"),
        'media_url': settings.get("MEDIA_URL", "/media/")
    }
    
    if storage_class_name == "temporary":
        storage_kwargs['temp_dir'] = settings.get("MEDIA_TEMP_DIR")
    elif storage_class_name == "chunked":
        storage_kwargs['chunk_size'] = settings.get("MEDIA_CHUNK_SIZE", 1024 * 1024)
    
    return storage_class(**storage_kwargs)