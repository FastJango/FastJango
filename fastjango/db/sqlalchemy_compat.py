"""
SQLAlchemy compatibility for FastJango ORM.

This module provides compatibility layers to use SQLAlchemy models and fields
directly in FastJango apps while maintaining Django-like patterns.
"""

from typing import Any, Optional, Type, Union, Dict
from sqlalchemy import Column, String, Integer, BigInteger, SmallInteger, Float, \
    Boolean, Date, DateTime, Time, Text, Binary, Numeric, LargeBinary, ForeignKey as SAForeignKey
from sqlalchemy.orm import relationship as SARelationship, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from .fields import Field
from .models import Model
from .connection import get_engine, get_session


# Create SQLAlchemy base
SQLAlchemyBase = declarative_base()


class SQLAlchemyField(Field):
    """
    Base class for SQLAlchemy-compatible fields.
    """
    
    def __init__(self, sa_column: Column, **kwargs):
        """
        Initialize SQLAlchemy field.
        
        Args:
            sa_column: SQLAlchemy Column object
            **kwargs: Field arguments
        """
        super().__init__(**kwargs)
        self.sa_column = sa_column
    
    def get_column(self) -> Column:
        """Get SQLAlchemy column."""
        return self.sa_column


class SQLAlchemyCharField(SQLAlchemyField):
    """SQLAlchemy CharField."""
    
    def __init__(self, max_length: int = 255, **kwargs):
        column = Column(String(max_length), **kwargs)
        super().__init__(column, max_length=max_length, **kwargs)


class SQLAlchemyTextField(SQLAlchemyField):
    """SQLAlchemy TextField."""
    
    def __init__(self, **kwargs):
        column = Column(Text, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyIntegerField(SQLAlchemyField):
    """SQLAlchemy IntegerField."""
    
    def __init__(self, **kwargs):
        column = Column(Integer, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyBigIntegerField(SQLAlchemyField):
    """SQLAlchemy BigIntegerField."""
    
    def __init__(self, **kwargs):
        column = Column(BigInteger, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyFloatField(SQLAlchemyField):
    """SQLAlchemy FloatField."""
    
    def __init__(self, **kwargs):
        column = Column(Float, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyBooleanField(SQLAlchemyField):
    """SQLAlchemy BooleanField."""
    
    def __init__(self, **kwargs):
        column = Column(Boolean, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyDateField(SQLAlchemyField):
    """SQLAlchemy DateField."""
    
    def __init__(self, **kwargs):
        column = Column(Date, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyDateTimeField(SQLAlchemyField):
    """SQLAlchemy DateTimeField."""
    
    def __init__(self, **kwargs):
        column = Column(DateTime, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyTimeField(SQLAlchemyField):
    """SQLAlchemy TimeField."""
    
    def __init__(self, **kwargs):
        column = Column(Time, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyBinaryField(SQLAlchemyField):
    """SQLAlchemy BinaryField."""
    
    def __init__(self, **kwargs):
        column = Column(LargeBinary, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyDecimalField(SQLAlchemyField):
    """SQLAlchemy DecimalField."""
    
    def __init__(self, precision: int = 10, scale: int = 2, **kwargs):
        column = Column(Numeric(precision, scale), **kwargs)
        super().__init__(column, precision=precision, scale=scale, **kwargs)


class SQLAlchemyUUIDField(SQLAlchemyField):
    """SQLAlchemy UUIDField."""
    
    def __init__(self, **kwargs):
        column = Column(PostgresUUID, **kwargs)
        super().__init__(column, **kwargs)


class SQLAlchemyForeignKey(SQLAlchemyField):
    """SQLAlchemy ForeignKey."""
    
    def __init__(self, target: Union[str, Type], **kwargs):
        column = SAForeignKey(target, **kwargs)
        super().__init__(column, target=target, **kwargs)


class SQLAlchemyModel(SQLAlchemyBase):
    """
    Base class for SQLAlchemy models in FastJango.
    
    This class provides Django-like functionality while using SQLAlchemy under the hood.
    """
    
    __abstract__ = True
    
    # Default primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    def __init__(self, **kwargs):
        """Initialize model with field values."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def save(self, using: Optional[str] = None) -> None:
        """
        Save the model instance.
        
        Args:
            using: Database to use (ignored for now)
        """
        session = get_session()
        session.add(self)
        session.commit()
    
    def delete(self, using: Optional[str] = None) -> None:
        """
        Delete the model instance.
        
        Args:
            using: Database to use (ignored for now)
        """
        session = get_session()
        session.delete(self)
        session.commit()
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        """Representation."""
        return f"<{self.__class__.__name__}: {self}>"
    
    @classmethod
    def objects(cls):
        """Get QuerySet for this model."""
        from .queryset import QuerySet
        return QuerySet(cls)


def create_sqlalchemy_model(name: str, fields: Dict[str, Column], **kwargs) -> Type[SQLAlchemyModel]:
    """
    Create a SQLAlchemy model dynamically.
    
    Args:
        name: Model name
        fields: Dictionary of field names to SQLAlchemy columns
        **kwargs: Additional model attributes
        
    Returns:
        Model class
    """
    attrs = {
        '__tablename__': kwargs.get('table_name', name.lower()),
        '__module__': kwargs.get('module', '__main__'),
    }
    
    # Add fields
    for field_name, column in fields.items():
        attrs[field_name] = column
    
    # Add Meta class if provided
    if 'Meta' in kwargs:
        attrs['Meta'] = kwargs['Meta']
    
    # Create the model class
    model_class = type(name, (SQLAlchemyModel,), attrs)
    
    return model_class


def register_sqlalchemy_model(model_class: Type[SQLAlchemyModel]) -> Type[SQLAlchemyModel]:
    """
    Register a SQLAlchemy model with FastJango.
    
    Args:
        model_class: SQLAlchemy model class
        
    Returns:
        The registered model class
    """
    # Add Django-like manager
    if not hasattr(model_class, 'objects'):
        model_class.objects = property(lambda cls: cls.objects())
    
    return model_class


# Convenience functions for creating fields
def CharField(max_length: int = 255, **kwargs) -> Column:
    """Create a CharField column."""
    return Column(String(max_length), **kwargs)


def TextField(**kwargs) -> Column:
    """Create a TextField column."""
    return Column(Text, **kwargs)


def IntegerField(**kwargs) -> Column:
    """Create an IntegerField column."""
    return Column(Integer, **kwargs)


def BigIntegerField(**kwargs) -> Column:
    """Create a BigIntegerField column."""
    return Column(BigInteger, **kwargs)


def SmallIntegerField(**kwargs) -> Column:
    """Create a SmallIntegerField column."""
    return Column(SmallInteger, **kwargs)


def FloatField(**kwargs) -> Column:
    """Create a FloatField column."""
    return Column(Float, **kwargs)


def BooleanField(**kwargs) -> Column:
    """Create a BooleanField column."""
    return Column(Boolean, **kwargs)


def DateField(**kwargs) -> Column:
    """Create a DateField column."""
    return Column(Date, **kwargs)


def DateTimeField(**kwargs) -> Column:
    """Create a DateTimeField column."""
    return Column(DateTime, **kwargs)


def TimeField(**kwargs) -> Column:
    """Create a TimeField column."""
    return Column(Time, **kwargs)


def BinaryField(**kwargs) -> Column:
    """Create a BinaryField column."""
    return Column(LargeBinary, **kwargs)


def DecimalField(precision: int = 10, scale: int = 2, **kwargs) -> Column:
    """Create a DecimalField column."""
    return Column(Numeric(precision, scale), **kwargs)


def UUIDField(**kwargs) -> Column:
    """Create a UUIDField column."""
    return Column(PostgresUUID, **kwargs)


def ForeignKey(target: Union[str, Type], **kwargs) -> Column:
    """Create a ForeignKey column."""
    return Column(SAForeignKey(target), **kwargs)


def relationship(*args, **kwargs):
    """Create a SQLAlchemy relationship."""
    return SARelationship(*args, **kwargs)


# Export commonly used SQLAlchemy types
from sqlalchemy import String, Integer, BigInteger, SmallInteger, Float, \
    Boolean, Date, DateTime, Time, Text, Binary, Numeric, LargeBinary

__all__ = [
    'SQLAlchemyModel', 'SQLAlchemyField', 'SQLAlchemyCharField', 'SQLAlchemyTextField',
    'SQLAlchemyIntegerField', 'SQLAlchemyBigIntegerField', 'SQLAlchemyFloatField',
    'SQLAlchemyBooleanField', 'SQLAlchemyDateField', 'SQLAlchemyDateTimeField',
    'SQLAlchemyTimeField', 'SQLAlchemyBinaryField', 'SQLAlchemyDecimalField',
    'SQLAlchemyUUIDField', 'SQLAlchemyForeignKey',
    'create_sqlalchemy_model', 'register_sqlalchemy_model',
    'CharField', 'TextField', 'IntegerField', 'BigIntegerField', 'SmallIntegerField',
    'FloatField', 'BooleanField', 'DateField', 'DateTimeField', 'TimeField',
    'BinaryField', 'DecimalField', 'UUIDField', 'ForeignKey', 'relationship',
    'String', 'Integer', 'BigInteger', 'SmallInteger', 'Float', 'Boolean',
    'Date', 'DateTime', 'Time', 'Text', 'Binary', 'Numeric', 'LargeBinary'
]