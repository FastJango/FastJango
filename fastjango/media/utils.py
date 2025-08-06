"""
FastJango Media Utils - Django-like media utility functions.

This module provides media utility functions for FastJango, similar to Django's
media utility functions but adapted for FastAPI.
"""

import os
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin, urlparse

from fastjango.core.exceptions import FastJangoError


def get_media_url(filename: str, settings: Optional[Dict[str, Any]] = None) -> str:
    """
    Get media URL for filename.
    
    Args:
        filename: File name
        settings: Settings dictionary
        
    Returns:
        Media URL
    """
    if settings is None:
        # Try to get settings from environment
        import os
        settings = {
            'MEDIA_URL': os.getenv('MEDIA_URL', '/media/')
        }
    
    media_url = settings.get('MEDIA_URL', '/media/')
    return urljoin(media_url, filename)


def get_media_path(filename: str, settings: Optional[Dict[str, Any]] = None) -> str:
    """
    Get media file path.
    
    Args:
        filename: File name
        settings: Settings dictionary
        
    Returns:
        Media file path
    """
    if settings is None:
        # Try to get settings from environment
        import os
        settings = {
            'MEDIA_ROOT': os.getenv('MEDIA_ROOT', 'media')
        }
    
    media_root = settings.get('MEDIA_ROOT', 'media')
    return str(Path(media_root) / filename)


def serve_media_file(filename: str, settings: Optional[Dict[str, Any]] = None):
    """
    Serve media file.
    
    Args:
        filename: File name
        settings: Settings dictionary
        
    Returns:
        FastAPI response
    """
    from fastapi.responses import FileResponse
    
    file_path = get_media_path(filename, settings)
    
    if not Path(file_path).exists():
        from fastjango.http import HttpResponse
        return HttpResponse("File not found", status_code=404)
    
    return FileResponse(file_path)


def get_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    Get file hash.
    
    Args:
        file_path: File path
        algorithm: Hash algorithm
        
    Returns:
        File hash
    """
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get file information.
    
    Args:
        file_path: File path
        
    Returns:
        File information dictionary
    """
    path = Path(file_path)
    
    if not path.exists():
        return {}
    
    stat = path.stat()
    
    return {
        'name': path.name,
        'size': stat.st_size,
        'created_at': datetime.fromtimestamp(stat.st_ctime),
        'modified_at': datetime.fromtimestamp(stat.st_mtime),
        'accessed_at': datetime.fromtimestamp(stat.st_atime),
        'content_type': mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        'hash': get_file_hash(file_path)
    }


def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """
    Validate file type.
    
    Args:
        filename: File name
        allowed_types: List of allowed file types
        
    Returns:
        True if file type is allowed
    """
    content_type = mimetypes.guess_type(filename)[0] or ""
    
    for allowed_type in allowed_types:
        if allowed_type in content_type:
            return True
    
    return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
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


def generate_unique_filename(original_name: str) -> str:
    """
    Generate unique filename.
    
    Args:
        original_name: Original filename
        
    Returns:
        Unique filename
    """
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


def get_file_extension(filename: str) -> str:
    """
    Get file extension.
    
    Args:
        filename: File name
        
    Returns:
        File extension
    """
    return Path(filename).suffix.lower()


def is_image_file(filename: str) -> bool:
    """
    Check if file is an image.
    
    Args:
        filename: File name
        
    Returns:
        True if file is an image
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    return get_file_extension(filename) in image_extensions


def is_video_file(filename: str) -> bool:
    """
    Check if file is a video.
    
    Args:
        filename: File name
        
    Returns:
        True if file is a video
    """
    video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
    return get_file_extension(filename) in video_extensions


def is_audio_file(filename: str) -> bool:
    """
    Check if file is an audio file.
    
    Args:
        filename: File name
        
    Returns:
        True if file is an audio file
    """
    audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']
    return get_file_extension(filename) in audio_extensions


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted file size
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_directory_size(directory_path: str) -> int:
    """
    Get total size of directory.
    
    Args:
        directory_path: Directory path
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    path = Path(directory_path)
    
    if not path.exists():
        return 0
    
    for file_path in path.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size


def cleanup_old_files(directory_path: str, max_age_days: int = 30) -> int:
    """
    Clean up old files in directory.
    
    Args:
        directory_path: Directory path
        max_age_days: Maximum age in days
        
    Returns:
        Number of files cleaned up
    """
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
    cleaned_count = 0
    path = Path(directory_path)
    
    if not path.exists():
        return 0
    
    for file_path in path.rglob("*"):
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                except Exception:
                    pass
    
    return cleaned_count


def create_media_directories(settings: Dict[str, Any]) -> None:
    """
    Create media directories from settings.
    
    Args:
        settings: Settings dictionary
    """
    media_root = settings.get("MEDIA_ROOT", "media")
    media_path = Path(media_root)
    
    # Create main media directory
    media_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories if specified
    subdirs = settings.get("MEDIA_SUBDIRECTORIES", [])
    for subdir in subdirs:
        (media_path / subdir).mkdir(parents=True, exist_ok=True)


def get_media_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get media-related settings.
    
    Args:
        settings: Settings dictionary
        
    Returns:
        Media settings dictionary
    """
    return {
        'MEDIA_ROOT': settings.get("MEDIA_ROOT", "media"),
        'MEDIA_URL': settings.get("MEDIA_URL", "/media/"),
        'MEDIA_STORAGE': settings.get("MEDIA_STORAGE", "filesystem"),
        'MEDIA_MAX_SIZE': settings.get("MEDIA_MAX_SIZE", 10 * 1024 * 1024),  # 10MB
        'MEDIA_ALLOWED_TYPES': settings.get("MEDIA_ALLOWED_TYPES", ["*/*"]),
        'MEDIA_SUBDIRECTORIES': settings.get("MEDIA_SUBDIRECTORIES", []),
        'MEDIA_CLEANUP_DAYS': settings.get("MEDIA_CLEANUP_DAYS", 30),
        'MEDIA_CHUNK_SIZE': settings.get("MEDIA_CHUNK_SIZE", 1024 * 1024),  # 1MB
        'MEDIA_TEMP_DIR': settings.get("MEDIA_TEMP_DIR")
    }