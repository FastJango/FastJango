"""
FastJango Database ORM - SQLAlchemy-based Django-like ORM
"""

from .models import Model, Manager
from .fields import (
    Field, CharField, TextField, IntegerField, BigIntegerField, 
    SmallIntegerField, PositiveIntegerField, PositiveSmallIntegerField,
    FloatField, DecimalField, BooleanField, NullBooleanField,
    DateField, DateTimeField, TimeField, DurationField,
    BinaryField, FileField, ImageField, FilePathField,
    EmailField, URLField, SlugField, UUIDField, IPAddressField,
    GenericIPAddressField, CommaSeparatedIntegerField,
    ForeignKey, OneToOneField, ManyToManyField
)
from .queryset import QuerySet
from .migrations import Migration, MigrationOperation
from .connection import get_engine, get_session, close_connections
from .exceptions import (
    DatabaseError, IntegrityError, OperationalError,
    ProgrammingError, DataError, NotSupportedError
)
from .sqlalchemy_compat import (
    SQLAlchemyModel, SQLAlchemyField, SQLAlchemyCharField, SQLAlchemyTextField,
    SQLAlchemyIntegerField, SQLAlchemyBigIntegerField, SQLAlchemyFloatField,
    SQLAlchemyBooleanField, SQLAlchemyDateField, SQLAlchemyDateTimeField,
    SQLAlchemyTimeField, SQLAlchemyBinaryField, SQLAlchemyDecimalField,
    SQLAlchemyUUIDField, SQLAlchemyForeignKey,
    create_sqlalchemy_model, register_sqlalchemy_model,
    CharField as SACharField, TextField as SATextField, IntegerField as SAIntegerField,
    BigIntegerField as SABigIntegerField, SmallIntegerField as SASmallIntegerField,
    FloatField as SAFloatField, BooleanField as SABooleanField, DateField as SADateField,
    DateTimeField as SADateTimeField, TimeField as SATimeField, BinaryField as SABinaryField,
    DecimalField as SADecimalField, UUIDField as SAUUIDField, ForeignKey as SAForeignKey,
    relationship
)

__all__ = [
    'Model', 'Manager', 'QuerySet',
    'Field', 'CharField', 'TextField', 'IntegerField', 'BigIntegerField',
    'SmallIntegerField', 'PositiveIntegerField', 'PositiveSmallIntegerField',
    'FloatField', 'DecimalField', 'BooleanField', 'NullBooleanField',
    'DateField', 'DateTimeField', 'TimeField', 'DurationField',
    'BinaryField', 'FileField', 'ImageField', 'FilePathField',
    'EmailField', 'URLField', 'SlugField', 'UUIDField', 'IPAddressField',
    'GenericIPAddressField', 'CommaSeparatedIntegerField',
    'ForeignKey', 'OneToOneField', 'ManyToManyField',
    'Migration', 'MigrationOperation',
    'get_engine', 'get_session', 'close_connections',
    'DatabaseError', 'IntegrityError', 'OperationalError',
    'ProgrammingError', 'DataError', 'NotSupportedError',
    # SQLAlchemy compatibility
    'SQLAlchemyModel', 'SQLAlchemyField', 'SQLAlchemyCharField', 'SQLAlchemyTextField',
    'SQLAlchemyIntegerField', 'SQLAlchemyBigIntegerField', 'SQLAlchemyFloatField',
    'SQLAlchemyBooleanField', 'SQLAlchemyDateField', 'SQLAlchemyDateTimeField',
    'SQLAlchemyTimeField', 'SQLAlchemyBinaryField', 'SQLAlchemyDecimalField',
    'SQLAlchemyUUIDField', 'SQLAlchemyForeignKey',
    'create_sqlalchemy_model', 'register_sqlalchemy_model',
    'SACharField', 'SATextField', 'SAIntegerField', 'SABigIntegerField',
    'SASmallIntegerField', 'SAFloatField', 'SABooleanField', 'SADateField',
    'SADateTimeField', 'SATimeField', 'SABinaryField', 'SADecimalField',
    'SAUUIDField', 'SAForeignKey', 'relationship'
]