"""
Database exceptions for FastJango ORM.
"""

from fastjango.core.exceptions import FastJangoError


class DatabaseError(FastJangoError):
    """Base exception for database errors."""
    pass


class IntegrityError(DatabaseError):
    """Exception for database integrity errors."""
    pass


class OperationalError(DatabaseError):
    """Exception for database operational errors."""
    pass


class ProgrammingError(DatabaseError):
    """Exception for database programming errors."""
    pass


class DataError(DatabaseError):
    """Exception for database data errors."""
    pass


class NotSupportedError(DatabaseError):
    """Exception for unsupported database operations."""
    pass


class ValidationError(FastJangoError):
    """Exception for model validation errors."""
    
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
