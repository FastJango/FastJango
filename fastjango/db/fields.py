"""
Model fields for FastJango ORM.
"""

import re
import uuid
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Any, Optional, Union, List, Dict
from pathlib import Path

from sqlalchemy import Column, String, Integer, BigInteger, SmallInteger, Float, \
    Boolean, Date, DateTime, Time, Text, Binary, Numeric, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.ext.hybrid import hybrid_property

from .exceptions import ValidationError


class Field:
    """
    Base field class for FastJango ORM.
    """
    
    def __init__(
        self,
        primary_key: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = None,
        unique: bool = False,
        db_index: bool = False,
        verbose_name: Optional[str] = None,
        help_text: Optional[str] = None,
        choices: Optional[List[tuple]] = None,
        db_column: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize a field.
        
        Args:
            primary_key: Whether this field is the primary key
            null: Whether this field can be null in database
            blank: Whether this field can be blank in forms
            default: Default value for this field
            unique: Whether this field should be unique
            db_index: Whether to create a database index
            verbose_name: Human-readable name for this field
            help_text: Help text for this field
            choices: List of choices for this field
            db_column: Database column name
        """
        self.primary_key = primary_key
        self.null = null
        self.blank = blank
        self.default = default
        self.unique = unique
        self.db_index = db_index
        self.verbose_name = verbose_name
        self.help_text = help_text
        self.choices = choices
        self.db_column = db_column
        self.name = None  # Set by Model
        self.model = None  # Set by Model
        
        # Store additional kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get_column(self) -> Column:
        """
        Get SQLAlchemy column for this field.
        
        Returns:
            SQLAlchemy Column
        """
        raise NotImplementedError("Subclasses must implement get_column()")
    
    def validate(self, value: Any) -> Any:
        """
        Validate a value for this field.
        
        Args:
            value: Value to validate
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if not self.null:
                raise ValidationError(f"{self.name} cannot be null")
            return None
        
        return value
    
    def to_python(self, value: Any) -> Any:
        """
        Convert value to Python type.
        
        Args:
            value: Value to convert
            
        Returns:
            Converted value
        """
        return value
    
    def get_prep_value(self, value: Any) -> Any:
        """
        Prepare value for database storage.
        
        Args:
            value: Value to prepare
            
        Returns:
            Prepared value
        """
        return value


class CharField(Field):
    """
    Character field for storing strings.
    """
    
    def __init__(self, max_length: int = 255, **kwargs):
        """
        Initialize CharField.
        
        Args:
            max_length: Maximum length of the string
        """
        super().__init__(**kwargs)
        self.max_length = max_length
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column."""
        return Column(
            String(self.max_length),
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate CharField value."""
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"{self.name} must be a string")
            if len(value) > self.max_length:
                raise ValidationError(f"{self.name} cannot be longer than {self.max_length} characters")
        return value


class TextField(Field):
    """
    Text field for storing long strings.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Text column."""
        return Column(
            Text,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate TextField value."""
        value = super().validate(value)
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"{self.name} must be a string")
        return value


class IntegerField(Field):
    """
    Integer field for storing whole numbers.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Integer column."""
        return Column(
            Integer,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate IntegerField value."""
        value = super().validate(value)
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be an integer")
        return value


class BigIntegerField(Field):
    """
    Big integer field for storing large whole numbers.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy BigInteger column."""
        return Column(
            BigInteger,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate BigIntegerField value."""
        value = super().validate(value)
        if value is not None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be an integer")
        return value


class SmallIntegerField(Field):
    """
    Small integer field for storing small whole numbers.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy SmallInteger column."""
        return Column(
            SmallInteger,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate SmallIntegerField value."""
        value = super().validate(value)
        if value is not None:
            try:
                value = int(value)
                if value < -32768 or value > 32767:
                    raise ValidationError(f"{self.name} must be between -32768 and 32767")
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be an integer")
        return value


class PositiveIntegerField(IntegerField):
    """
    Positive integer field.
    """
    
    def validate(self, value: Any) -> Any:
        """Validate PositiveIntegerField value."""
        value = super().validate(value)
        if value is not None and value < 0:
            raise ValidationError(f"{self.name} must be positive")
        return value


class PositiveSmallIntegerField(SmallIntegerField):
    """
    Positive small integer field.
    """
    
    def validate(self, value: Any) -> Any:
        """Validate PositiveSmallIntegerField value."""
        value = super().validate(value)
        if value is not None and value < 0:
            raise ValidationError(f"{self.name} must be positive")
        return value


class FloatField(Field):
    """
    Float field for storing decimal numbers.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Float column."""
        return Column(
            Float,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate FloatField value."""
        value = super().validate(value)
        if value is not None:
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be a number")
        return value


class DecimalField(Field):
    """
    Decimal field for storing precise decimal numbers.
    """
    
    def __init__(self, max_digits: int = 10, decimal_places: int = 2, **kwargs):
        """
        Initialize DecimalField.
        
        Args:
            max_digits: Maximum number of digits
            decimal_places: Number of decimal places
        """
        super().__init__(**kwargs)
        self.max_digits = max_digits
        self.decimal_places = decimal_places
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Numeric column."""
        return Column(
            Numeric(self.max_digits, self.decimal_places),
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate DecimalField value."""
        value = super().validate(value)
        if value is not None:
            try:
                value = Decimal(str(value))
                if len(str(value).replace('.', '')) > self.max_digits:
                    raise ValidationError(f"{self.name} cannot have more than {self.max_digits} digits")
            except (ValueError, TypeError):
                raise ValidationError(f"{self.name} must be a valid decimal number")
        return value


class BooleanField(Field):
    """
    Boolean field for storing true/false values.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Boolean column."""
        return Column(
            Boolean,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate BooleanField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                value = value.lower()
                if value in ('true', '1', 'yes', 'on'):
                    value = True
                elif value in ('false', '0', 'no', 'off'):
                    value = False
                else:
                    raise ValidationError(f"{self.name} must be True or False")
            elif not isinstance(value, bool):
                raise ValidationError(f"{self.name} must be True or False")
        return value


class NullBooleanField(BooleanField):
    """
    Nullable boolean field.
    """
    
    def __init__(self, **kwargs):
        kwargs['null'] = True
        super().__init__(**kwargs)


class DateField(Field):
    """
    Date field for storing dates.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Date column."""
        return Column(
            Date,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate DateField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError(f"{self.name} must be a valid date (YYYY-MM-DD)")
            elif not isinstance(value, date):
                raise ValidationError(f"{self.name} must be a date")
        return value


class DateTimeField(Field):
    """
    DateTime field for storing dates and times.
    """
    
    def __init__(self, auto_now: bool = False, auto_now_add: bool = False, **kwargs):
        """
        Initialize DateTimeField.
        
        Args:
            auto_now: Update on every save
            auto_now_add: Set on creation only
        """
        super().__init__(**kwargs)
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
    
    def get_column(self) -> Column:
        """Get SQLAlchemy DateTime column."""
        return Column(
            DateTime,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate DateTimeField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValidationError(f"{self.name} must be a valid datetime")
            elif not isinstance(value, datetime):
                raise ValidationError(f"{self.name} must be a datetime")
        return value


class TimeField(Field):
    """
    Time field for storing times.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Time column."""
        return Column(
            Time,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate TimeField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                try:
                    value = datetime.strptime(value, '%H:%M:%S').time()
                except ValueError:
                    raise ValidationError(f"{self.name} must be a valid time (HH:MM:SS)")
            elif not isinstance(value, time):
                raise ValidationError(f"{self.name} must be a time")
        return value


class DurationField(Field):
    """
    Duration field for storing time durations.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Interval column."""
        from sqlalchemy import Interval
        return Column(
            Interval,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate DurationField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, (int, float)):
                value = timedelta(seconds=value)
            elif not isinstance(value, timedelta):
                raise ValidationError(f"{self.name} must be a timedelta")
        return value


class BinaryField(Field):
    """
    Binary field for storing binary data.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy LargeBinary column."""
        return Column(
            LargeBinary,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate BinaryField value."""
        value = super().validate(value)
        if value is not None and not isinstance(value, bytes):
            raise ValidationError(f"{self.name} must be bytes")
        return value


class FileField(Field):
    """
    File field for storing file paths.
    """
    
    def __init__(self, upload_to: str = '', **kwargs):
        """
        Initialize FileField.
        
        Args:
            upload_to: Directory to upload files to
        """
        super().__init__(**kwargs)
        self.upload_to = upload_to
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column for file path."""
        return Column(
            String(255),
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate FileField value."""
        value = super().validate(value)
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"{self.name} must be a string")
        return value


class ImageField(FileField):
    """
    Image field for storing image file paths.
    """
    
    def validate(self, value: Any) -> Any:
        """Validate ImageField value."""
        value = super().validate(value)
        if value is not None:
            # Basic image extension check
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')
            if not any(value.lower().endswith(ext) for ext in image_extensions):
                raise ValidationError(f"{self.name} must be an image file")
        return value


class FilePathField(Field):
    """
    File path field for storing file system paths.
    """
    
    def __init__(self, path: str = '', match: str = None, recursive: bool = False, **kwargs):
        """
        Initialize FilePathField.
        
        Args:
            path: Directory path to scan
            match: Regex pattern to match files
            recursive: Whether to scan subdirectories
        """
        super().__init__(**kwargs)
        self.path = path
        self.match = match
        self.recursive = recursive
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column for file path."""
        return Column(
            String(255),
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate FilePathField value."""
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"{self.name} must be a string")
            if not Path(value).exists():
                raise ValidationError(f"{self.name} must be a valid file path")
        return value


class EmailField(CharField):
    """
    Email field for storing email addresses.
    """
    
    def __init__(self, max_length: int = 254, **kwargs):
        super().__init__(max_length=max_length, **kwargs)
    
    def validate(self, value: Any) -> Any:
        """Validate EmailField value."""
        value = super().validate(value)
        if value is not None:
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError(f"{self.name} must be a valid email address")
        return value


class URLField(CharField):
    """
    URL field for storing URLs.
    """
    
    def __init__(self, max_length: int = 200, **kwargs):
        super().__init__(max_length=max_length, **kwargs)
    
    def validate(self, value: Any) -> Any:
        """Validate URLField value."""
        value = super().validate(value)
        if value is not None:
            # Basic URL validation
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                raise ValidationError(f"{self.name} must be a valid URL")
        return value


class SlugField(CharField):
    """
    Slug field for storing URL-friendly strings.
    """
    
    def __init__(self, max_length: int = 50, **kwargs):
        super().__init__(max_length=max_length, **kwargs)
    
    def validate(self, value: Any) -> Any:
        """Validate SlugField value."""
        value = super().validate(value)
        if value is not None:
            # Slug validation (letters, numbers, hyphens, underscores)
            slug_pattern = r'^[a-z0-9_-]+$'
            if not re.match(slug_pattern, value):
                raise ValidationError(f"{self.name} must contain only letters, numbers, hyphens, and underscores")
        return value


class UUIDField(Field):
    """
    UUID field for storing UUIDs.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy UUID column."""
        return Column(
            PostgresUUID,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate UUIDField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                try:
                    value = uuid.UUID(value)
                except ValueError:
                    raise ValidationError(f"{self.name} must be a valid UUID")
            elif not isinstance(value, uuid.UUID):
                raise ValidationError(f"{self.name} must be a UUID")
        return value


class IPAddressField(Field):
    """
    IP address field for storing IPv4 addresses.
    """
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column for IP address."""
        return Column(
            String(15),  # IPv4 max length
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate IPAddressField value."""
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"{self.name} must be a string")
            # Basic IPv4 validation
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, value):
                raise ValidationError(f"{self.name} must be a valid IPv4 address")
            # Check each octet
            for octet in value.split('.'):
                if not 0 <= int(octet) <= 255:
                    raise ValidationError(f"{self.name} must be a valid IPv4 address")
        return value


class GenericIPAddressField(Field):
    """
    Generic IP address field for storing IPv4 and IPv6 addresses.
    """
    
    def __init__(self, protocol: str = 'both', **kwargs):
        """
        Initialize GenericIPAddressField.
        
        Args:
            protocol: 'both', 'IPv4', or 'IPv6'
        """
        super().__init__(**kwargs)
        self.protocol = protocol
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column for IP address."""
        return Column(
            String(45),  # IPv6 max length
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate GenericIPAddressField value."""
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"{self.name} must be a string")
            # Basic IP validation (simplified)
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
            if not re.match(ip_pattern, value):
                raise ValidationError(f"{self.name} must be a valid IP address")
        return value


class CommaSeparatedIntegerField(Field):
    """
    Comma-separated integer field.
    """
    
    def __init__(self, max_length: int = 255, **kwargs):
        super().__init__(max_length=max_length, **kwargs)
    
    def get_column(self) -> Column:
        """Get SQLAlchemy String column."""
        return Column(
            String(self.max_length),
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def validate(self, value: Any) -> Any:
        """Validate CommaSeparatedIntegerField value."""
        value = super().validate(value)
        if value is not None:
            if isinstance(value, str):
                try:
                    [int(x.strip()) for x in value.split(',')]
                except ValueError:
                    raise ValidationError(f"{self.name} must be comma-separated integers")
            elif not isinstance(value, list):
                raise ValidationError(f"{self.name} must be a list of integers")
        return value


class ForeignKey(Field):
    """
    Foreign key field for relationships.
    """
    
    def __init__(self, to: str, on_delete: str = 'CASCADE', **kwargs):
        """
        Initialize ForeignKey.
        
        Args:
            to: Target model (string or model class)
            on_delete: Delete behavior ('CASCADE', 'SET_NULL', 'SET_DEFAULT', 'PROTECT')
        """
        super().__init__(**kwargs)
        self.to = to
        self.on_delete = on_delete
    
    def get_column(self) -> Column:
        """Get SQLAlchemy Integer column for foreign key."""
        return Column(
            Integer,
            nullable=self.null,
            unique=self.unique,
            index=self.db_index,
            primary_key=self.primary_key,
            default=self.default
        )
    
    def get_relationship(self, model_class):
        """Get SQLAlchemy relationship."""
        return relationship(
            self.to,
            backref=f"{model_class.__name__.lower()}_set",
            cascade=self.on_delete.lower()
        )


class OneToOneField(ForeignKey):
    """
    One-to-one relationship field.
    """
    
    def __init__(self, to: str, **kwargs):
        kwargs['unique'] = True
        super().__init__(to, **kwargs)
    
    def get_relationship(self, model_class):
        """Get SQLAlchemy relationship for one-to-one."""
        return relationship(
            self.to,
            backref=f"{model_class.__name__.lower()}",
            uselist=False,
            cascade=self.on_delete.lower()
        )


class ManyToManyField(Field):
    """
    Many-to-many relationship field.
    """
    
    def __init__(self, to: str, through: Optional[str] = None, **kwargs):
        """
        Initialize ManyToManyField.
        
        Args:
            to: Target model
            through: Intermediate model for custom relationships
        """
        super().__init__(**kwargs)
        self.to = to
        self.through = through
    
    def get_column(self) -> Column:
        """ManyToManyField doesn't create a column directly."""
        return None
    
    def get_relationship(self, model_class):
        """Get SQLAlchemy relationship for many-to-many."""
        if self.through:
            return relationship(
                self.to,
                secondary=self.through,
                backref=f"{model_class.__name__.lower()}_set"
            )
        else:
            # Create association table automatically
            table_name = f"{model_class.__name__.lower()}_{self.to.lower()}"
            return relationship(
                self.to,
                secondary=table_name,
                backref=f"{model_class.__name__.lower()}_set"
            )
