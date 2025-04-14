"""
Custom exceptions for FastJango.
"""


class FastJangoError(Exception):
    """Base exception for all FastJango errors."""
    pass


class CommandError(FastJangoError):
    """Exception for command-line errors."""
    pass


class ProjectCreationError(CommandError):
    """Exception for errors during project creation."""
    pass


class AppCreationError(CommandError):
    """Exception for errors during app creation."""
    pass


class ValidationError(FastJangoError):
    """Exception for validation errors."""
    
    def __init__(self, message_dict=None, message=None, *args, **kwargs):
        """
        Initialize ValidationError with either a message dictionary or a message.
        
        Args:
            message_dict: Dictionary mapping field names to error messages
            message: Error message
        """
        if message_dict is not None and message is not None:
            raise ValueError("Cannot specify both message_dict and message")
        
        self.message_dict = message_dict
        self.message = message
        
        if message_dict:
            message = ", ".join(f"{field}: {', '.join(msgs) if isinstance(msgs, list) else msgs}" 
                              for field, msgs in message_dict.items())
        
        super().__init__(message, *args, **kwargs)


class ConfigurationError(FastJangoError):
    """Exception for configuration errors."""
    pass


class ServiceError(FastJangoError):
    """Exception for service-layer errors."""
    pass


class DatabaseError(FastJangoError):
    """Base exception for database errors."""
    pass


class IntegrityError(DatabaseError):
    """Exception for database integrity errors."""
    pass


class ObjectDoesNotExist(FastJangoError):
    """Exception for when an object does not exist."""
    pass


class MultipleObjectsReturned(FastJangoError):
    """Exception for when multiple objects are returned when only one was expected."""
    pass


class ImproperlyConfigured(FastJangoError):
    """Exception for when FastJango is improperly configured."""
    pass


class PermissionDenied(FastJangoError):
    """Exception for permission denied errors."""
    pass


class SuspiciousOperation(FastJangoError):
    """Exception for suspicious operations."""
    pass 