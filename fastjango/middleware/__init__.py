"""
FastJango Middleware - Django-like middleware system.

This module provides Django-like middleware components for FastJango,
including session management, authentication, security, and more.
"""

from .session import SessionMiddleware
from .authentication import AuthenticationMiddleware
from .security import SecurityMiddleware
from .cors import CORSMiddleware
from .common import CommonMiddleware
from .messages import MessageMiddleware
from .gzip import GZipMiddleware

__all__ = [
    # Session
    'SessionMiddleware',
    
    # Authentication
    'AuthenticationMiddleware',
    
    # Security
    'SecurityMiddleware',
    
    # CORS
    'CORSMiddleware',
    
    # Common
    'CommonMiddleware',
    
    # Messages
    'MessageMiddleware',
    
    # Compression
    'GZipMiddleware',
]
