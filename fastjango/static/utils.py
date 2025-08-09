"""
FastJango Static Files Utils - Django-like static file utilities.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from fastapi import Request


def static_url(filename: str, static_url: str = "/static/") -> str:
    """
    Get the URL for a static file (Django-like).
    
    Args:
        filename: The filename
        static_url: The static URL prefix
        
    Returns:
        The static file URL
    """
    return f"{static_url.rstrip('/')}/{filename.lstrip('/')}"


def static_root(settings: Dict[str, Any]) -> str:
    """
    Get the static root directory from settings.
    
    Args:
        settings: Settings dictionary
        
    Returns:
        The static root directory
    """
    return settings.get('STATIC_ROOT', 'staticfiles')


def staticfiles_urlpatterns(static_url: str = "/static/", static_dirs: List[str] = None) -> List[Dict[str, Any]]:
    """
    Generate URL patterns for static files (Django-like).
    
    Args:
        static_url: The static URL prefix
        static_dirs: List of static directories
        
    Returns:
        List of URL pattern dictionaries
    """
    static_dirs = static_dirs or ["static"]
    
    patterns = []
    for static_dir in static_dirs:
        patterns.append({
            'url': static_url,
            'directory': static_dir,
            'name': 'static'
        })
    
    return patterns


def get_static_path(filename: str, static_dirs: List[str] = None) -> Optional[Path]:
    """
    Get the full path to a static file.
    
    Args:
        filename: The filename
        static_dirs: List of static directories to search
        
    Returns:
        Path to the file or None if not found
    """
    static_dirs = static_dirs or ["static"]
    
    for static_dir in static_dirs:
        file_path = Path(static_dir) / filename.lstrip('/')
        if file_path.exists() and file_path.is_file():
            return file_path
    
    return None


def is_static_file(filename: str, static_dirs: List[str] = None) -> bool:
    """
    Check if a file is a static file.
    
    Args:
        filename: The filename
        static_dirs: List of static directories
        
    Returns:
        True if the file is a static file, False otherwise
    """
    return get_static_path(filename, static_dirs) is not None


def get_static_file_info(filename: str, static_dirs: List[str] = None) -> Dict[str, Any]:
    """
    Get information about a static file.
    
    Args:
        filename: The filename
        static_dirs: List of static directories
        
    Returns:
        Dictionary with file information
    """
    file_path = get_static_path(filename, static_dirs)
    
    if not file_path:
        return {}
    
    stat = file_path.stat()
    content_type, _ = mimetypes.guess_type(str(file_path))
    
    return {
        'name': filename,
        'path': str(file_path),
        'size': stat.st_size,
        'modified': stat.st_mtime,
        'content_type': content_type or 'application/octet-stream',
        'exists': True
    }


def find_static_files(directory: str, pattern: str = "*") -> List[str]:
    """
    Find static files matching a pattern.
    
    Args:
        directory: The directory to search
        pattern: The file pattern to match
        
    Returns:
        List of matching file paths
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []
    
    files = []
    for file_path in dir_path.rglob(pattern):
        if file_path.is_file():
            files.append(str(file_path.relative_to(dir_path)))
    
    return files


def get_static_hash(filename: str, static_dirs: List[str] = None) -> Optional[str]:
    """
    Get a hash of a static file for cache busting.
    
    Args:
        filename: The filename
        static_dirs: List of static directories
        
    Returns:
        Hash string or None if file not found
    """
    file_path = get_static_path(filename, static_dirs)
    
    if not file_path:
        return None
    
    # Create hash based on file content and modification time
    stat = file_path.stat()
    hash_data = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
    return hashlib.md5(hash_data.encode()).hexdigest()[:8]


def static_url_with_hash(filename: str, static_url: str = "/static/", 
                        static_dirs: List[str] = None) -> str:
    """
    Get the URL for a static file with hash for cache busting.
    
    Args:
        filename: The filename
        static_url: The static URL prefix
        static_dirs: List of static directories
        
    Returns:
        The static file URL with hash
    """
    base_url = static_url(filename, static_url)
    file_hash = get_static_hash(filename, static_dirs)
    
    if file_hash:
        # Add hash as query parameter
        return f"{base_url}?v={file_hash}"
    
    return base_url


def collect_static_files(source_dirs: List[str], destination: str,
                        ignore_patterns: List[str] = None) -> Dict[str, Any]:
    """
    Collect static files from multiple directories to a single location.
    
    Args:
        source_dirs: List of source directories
        destination: Destination directory
        ignore_patterns: Patterns to ignore
        
    Returns:
        Dictionary with collection results
    """
    import shutil
    
    destination_path = Path(destination)
    ignore_patterns = ignore_patterns or []
    
    destination_path.mkdir(parents=True, exist_ok=True)
    
    collected_files = []
    skipped_files = []
    
    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            continue
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(source_path)
                
                # Check ignore patterns
                should_ignore = False
                for pattern in ignore_patterns:
                    if pattern in str(rel_path):
                        should_ignore = True
                        break
                
                if should_ignore:
                    skipped_files.append(str(rel_path))
                    continue
                
                dest_file = destination_path / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_file)
                
                collected_files.append(str(rel_path))
    
    return {
        'collected_files': collected_files,
        'skipped_files': skipped_files,
        'total_collected': len(collected_files),
        'total_skipped': len(skipped_files)
    }


def get_static_manifest(static_dirs: List[str] = None) -> Dict[str, str]:
    """
    Generate a manifest of static files with their hashes.
    
    Args:
        static_dirs: List of static directories
        
    Returns:
        Dictionary mapping filenames to their hashes
    """
    static_dirs = static_dirs or ["static"]
    manifest = {}
    
    for static_dir in static_dirs:
        static_path = Path(static_dir)
        if not static_path.exists():
            continue
        
        for file_path in static_path.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(static_path))
                file_hash = get_static_hash(rel_path, [static_dir])
                if file_hash:
                    manifest[rel_path] = file_hash
    
    return manifest


def save_static_manifest(manifest: Dict[str, str], output_file: str):
    """
    Save a static file manifest to a file.
    
    Args:
        manifest: The manifest dictionary
        output_file: The output file path
    """
    import json
    
    with open(output_file, 'w') as f:
        json.dump(manifest, f, indent=2)


def load_static_manifest(manifest_file: str) -> Dict[str, str]:
    """
    Load a static file manifest from a file.
    
    Args:
        manifest_file: The manifest file path
        
    Returns:
        The manifest dictionary
    """
    import json
    
    with open(manifest_file, 'r') as f:
        return json.load(f)


# Template helpers (for use in Jinja2 templates)
def static_url_template(filename: str, static_url: str = "/static/") -> str:
    """
    Template helper for static URLs.
    
    Args:
        filename: The filename
        static_url: The static URL prefix
        
    Returns:
        The static file URL
    """
    return static_url(filename, static_url)


def static_url_with_hash_template(filename: str, static_url: str = "/static/",
                                static_dirs: List[str] = None) -> str:
    """
    Template helper for static URLs with hash.
    
    Args:
        filename: The filename
        static_url: The static URL prefix
        static_dirs: List of static directories
        
    Returns:
        The static file URL with hash
    """
    return static_url_with_hash(filename, static_url, static_dirs)


# Example usage:
def setup_static_utils(app, settings: Dict[str, Any]):
    """
    Set up static file utilities for a FastAPI app.
    
    Args:
        app: The FastAPI app
        settings: Settings dictionary
    """
    # Add static utilities to app state
    app.state.static_url = settings.get('STATIC_URL', '/static/')
    app.state.static_root = settings.get('STATIC_ROOT')
    app.state.staticfiles_dirs = settings.get('STATICFILES_DIRS', [])
    
    # Add template helpers
    if hasattr(app.state, 'template_globals'):
        app.state.template_globals.update({
            'static_url': static_url_template,
            'static_url_with_hash': static_url_with_hash_template,
        })
    
    # Add static file endpoints
    @app.get("/static-info/{filename:path}")
    async def get_static_file_info(filename: str):
        """Get information about a static file."""
        return get_static_file_info(filename, app.state.staticfiles_dirs)
    
    @app.get("/static-manifest/")
    async def get_static_manifest():
        """Get the static file manifest."""
        return get_static_manifest(app.state.staticfiles_dirs)
