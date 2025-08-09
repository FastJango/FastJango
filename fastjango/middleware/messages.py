"""
FastJango Messages Middleware - Django-like user messages.

This module provides messages middleware for FastJango, similar to Django's
messages middleware but adapted for FastAPI.
"""

import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastjango.core.exceptions import FastJangoError
from fastjango.middleware.session import get_session_data, set_session_data


class MessageLevel(Enum):
    """Message levels similar to Django's message levels."""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40


@dataclass
class Message:
    """Message object similar to Django's message."""
    
    message: str
    level: MessageLevel
    tags: Optional[str] = None
    extra_tags: Optional[str] = None
    
    def __post_init__(self):
        """Set default tags based on level."""
        if self.tags is None:
            self.tags = self.level.name.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'message': self.message,
            'level': self.level.value,
            'level_name': self.level.name,
            'tags': self.tags,
            'extra_tags': self.extra_tags
        }


class MessageStorage:
    """Base class for message storage backends."""
    
    def get(self, request: Request) -> List[Message]:
        """Get messages for request."""
        raise NotImplementedError
    
    def add(self, request: Request, message: Message) -> None:
        """Add message to storage."""
        raise NotImplementedError
    
    def clear(self, request: Request) -> None:
        """Clear all messages."""
        raise NotImplementedError


class SessionMessageStorage(MessageStorage):
    """Session-based message storage."""
    
    def __init__(self, session_key: str = "_messages"):
        self.session_key = session_key
    
    def get(self, request: Request) -> List[Message]:
        """Get messages from session."""
        messages_data = get_session_data(request, self.session_key, [])
        messages = []
        
        for msg_data in messages_data:
            if isinstance(msg_data, dict):
                level = MessageLevel(msg_data.get('level', MessageLevel.INFO.value))
                message = Message(
                    message=msg_data.get('message', ''),
                    level=level,
                    tags=msg_data.get('tags'),
                    extra_tags=msg_data.get('extra_tags')
                )
                messages.append(message)
        
        return messages
    
    def add(self, request: Request, message: Message) -> None:
        """Add message to session."""
        messages_data = get_session_data(request, self.session_key, [])
        messages_data.append(message.to_dict())
        set_session_data(request, self.session_key, messages_data)
    
    def clear(self, request: Request) -> None:
        """Clear messages from session."""
        from fastjango.middleware.session import delete_session_data
        delete_session_data(request, self.session_key)


class MessageMiddleware(BaseHTTPMiddleware):
    """
    Django-like messages middleware for FastJango.
    
    This middleware provides user messages similar to Django's
    messages middleware, with support for different storage backends.
    """
    
    def __init__(self, app,
                 storage_class: Optional[MessageStorage] = None,
                 session_key: str = "_messages",
                 default_level: MessageLevel = MessageLevel.INFO):
        """
        Initialize the messages middleware.
        
        Args:
            app: The FastAPI application
            storage_class: Message storage backend
            session_key: Session key for messages
            default_level: Default message level
        """
        super().__init__(app)
        
        self.storage = storage_class or SessionMessageStorage(session_key)
        self.default_level = default_level
    
    async def dispatch(self, request: Request, call_next):
        """
        Process the request through messages middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware/endpoint
            
        Returns:
            The response
        """
        # Attach messages to request
        request.state.messages = self.storage.get(request)
        
        # Process request
        response = await call_next(request)
        
        return response


def get_messages(request: Request) -> List[Message]:
    """
    Get all messages for the request.
    
    Args:
        request: The request object
        
    Returns:
        List of messages
    """
    return getattr(request.state, 'messages', [])


def add_message(request: Request, message: str, level: MessageLevel = MessageLevel.INFO, 
                tags: Optional[str] = None, extra_tags: Optional[str] = None) -> None:
    """
    Add a message to the request.
    
    Args:
        request: The request object
        message: The message text
        level: The message level
        tags: Message tags
        extra_tags: Extra message tags
    """
    msg = Message(message=message, level=level, tags=tags, extra_tags=extra_tags)
    
    # Get storage from request state or create default
    storage = getattr(request.state, '_message_storage', None)
    if storage is None:
        storage = SessionMessageStorage()
        request.state._message_storage = storage
    
    storage.add(request, msg)


def debug(request: Request, message: str, tags: Optional[str] = None, 
          extra_tags: Optional[str] = None) -> None:
    """Add a debug message."""
    add_message(request, message, MessageLevel.DEBUG, tags, extra_tags)


def info(request: Request, message: str, tags: Optional[str] = None, 
         extra_tags: Optional[str] = None) -> None:
    """Add an info message."""
    add_message(request, message, MessageLevel.INFO, tags, extra_tags)


def success(request: Request, message: str, tags: Optional[str] = None, 
           extra_tags: Optional[str] = None) -> None:
    """Add a success message."""
    add_message(request, message, MessageLevel.SUCCESS, tags, extra_tags)


def warning(request: Request, message: str, tags: Optional[str] = None, 
           extra_tags: Optional[str] = None) -> None:
    """Add a warning message."""
    add_message(request, message, MessageLevel.WARNING, tags, extra_tags)


def error(request: Request, message: str, tags: Optional[str] = None, 
         extra_tags: Optional[str] = None) -> None:
    """Add an error message."""
    add_message(request, message, MessageLevel.ERROR, tags, extra_tags)


def get_messages_with_tags(request: Request, tags: Optional[str] = None) -> List[Message]:
    """
    Get messages with specific tags.
    
    Args:
        request: The request object
        tags: Tags to filter by
        
    Returns:
        List of filtered messages
    """
    messages = get_messages(request)
    
    if tags is None:
        return messages
    
    if isinstance(tags, str):
        tags = [tags]
    
    filtered_messages = []
    for message in messages:
        message_tags = message.tags.split() if message.tags else []
        if any(tag in message_tags for tag in tags):
            filtered_messages.append(message)
    
    return filtered_messages


def clear_messages(request: Request) -> None:
    """
    Clear all messages for the request.
    
    Args:
        request: The request object
    """
    storage = getattr(request.state, '_message_storage', None)
    if storage is None:
        storage = SessionMessageStorage()
        request.state._message_storage = storage
    
    storage.clear(request)
    request.state.messages = []


def get_messages_json(request: Request) -> str:
    """
    Get messages as JSON string.
    
    Args:
        request: The request object
        
    Returns:
        JSON string of messages
    """
    messages = get_messages(request)
    return json.dumps([msg.to_dict() for msg in messages])


def render_messages_html(request: Request, template: str = None) -> str:
    """
    Render messages as HTML.
    
    Args:
        request: The request object
        template: Custom template (optional)
        
    Returns:
        HTML string of messages
    """
    messages = get_messages(request)
    
    if not messages:
        return ""
    
    if template:
        # Use custom template
        from fastjango.templates import render_to_string
        return render_to_string(template, {'messages': messages})
    
    # Default HTML template
    html_parts = []
    for message in messages:
        css_class = f"alert alert-{message.level.name.lower()}"
        if message.tags:
            css_class += f" {message.tags}"
        
        html_parts.append(f'<div class="{css_class}">{message.message}</div>')
    
    return "\n".join(html_parts)
