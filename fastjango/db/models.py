"""
Model classes for FastJango ORM.
"""

import inspect
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, Table, ForeignKey as SAForeignKey
from sqlalchemy.orm import Session, declarative_base, DeclarativeMeta

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
from .connection import get_session
from .exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned

# Delete behaviors
CASCADE = 'CASCADE'
PROTECT = 'PROTECT'
SET_NULL = 'SET_NULL'
SET_DEFAULT = 'SET_DEFAULT'
DO_NOTHING = 'DO_NOTHING'

# Create base class for all models
Base = declarative_base()

# Global metadata for all models
metadata = MetaData()


class Options:
    """
    Options class to mimic Django's _meta.
    """
    def __init__(self, meta=None, app_label=None):
        self.meta = meta
        self.app_label = getattr(meta, 'app_label', app_label)
        self.db_table = getattr(meta, 'db_table', getattr(meta, 'table_name', None))

    def __getattr__(self, name):
        if self.meta and hasattr(self.meta, name):
            return getattr(self.meta, name)
        raise AttributeError(f"'Options' object has no attribute '{name}'")


class Manager:
    """
    Manager class for model operations.
    """
    
    def __init__(self, model_class):
        """
        Initialize manager.
        
        Args:
            model_class: The model class this manager belongs to
        """
        self.model = model_class
    
    def get_queryset(self) -> QuerySet:
        """
        Get a new QuerySet.
        
        Returns:
            QuerySet for this model
        """
        return QuerySet(self.model)
    
    def all(self) -> QuerySet:
        """
        Get all objects.
        
        Returns:
            QuerySet with all objects
        """
        return self.get_queryset()
    
    def filter(self, **kwargs) -> QuerySet:
        """
        Filter objects.
        
        Args:
            **kwargs: Filter criteria
            
        Returns:
            Filtered QuerySet
        """
        return self.get_queryset().filter(**kwargs)
    
    def exclude(self, **kwargs) -> QuerySet:
        """
        Exclude objects.
        
        Args:
            **kwargs: Exclusion criteria
            
        Returns:
            Filtered QuerySet
        """
        return self.get_queryset().exclude(**kwargs)

    def order_by(self, *args, **kwargs) -> QuerySet:
        """
        Order objects.

        Args:
            *args: Fields to order by

        Returns:
            Ordered QuerySet
        """
        return self.get_queryset().order_by(*args, **kwargs)
    
    def get(self, **kwargs) -> Any:
        """
        Get a single object.
        
        Args:
            **kwargs: Lookup criteria
            
        Returns:
            Model instance
            
        Raises:
            ObjectDoesNotExist: If no object found
            MultipleObjectsReturned: If multiple objects found
        """
        return self.get_queryset().get(**kwargs)
    
    def create(self, **kwargs) -> Any:
        """
        Create a new object.
        
        Args:
            **kwargs: Field values
            
        Returns:
            Created model instance
        """
        return self.get_queryset().create(**kwargs)
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple:
        """
        Get an object or create it.
        
        Args:
            defaults: Default values for creation
            **kwargs: Lookup criteria
            
        Returns:
            Tuple of (object, created)
        """
        return self.get_queryset().get_or_create(defaults=defaults, **kwargs)
    
    def update_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple:
        """
        Update an object or create it.
        
        Args:
            defaults: Default values for creation/update
            **kwargs: Lookup criteria
            
        Returns:
            Tuple of (object, created)
        """
        return self.get_queryset().update_or_create(defaults=defaults, **kwargs)
    
    def bulk_create(self, objects: List[Any], batch_size: int = 100) -> List[Any]:
        """
        Create multiple objects.
        
        Args:
            objects: List of model instances
            batch_size: Number of objects per batch
            
        Returns:
            List of created objects
        """
        return self.get_queryset().bulk_create(objects, batch_size)
    
    def count(self) -> int:
        """
        Count objects.
        
        Returns:
            Number of objects
        """
        return self.get_queryset().count()
    
    def first(self) -> Optional[Any]:
        """
        Get first object.
        
        Returns:
            First model instance or None
        """
        return self.get_queryset().first()
    
    def last(self) -> Optional[Any]:
        """
        Get last object.
        
        Returns:
            Last model instance or None
        """
        return self.get_queryset().last()
    
    def exists(self) -> bool:
        """
        Check if any objects exist.
        
        Returns:
            True if objects exist
        """
        return self.get_queryset().exists()


class ModelMeta(DeclarativeMeta):
    """
    Metaclass for Model to set up SQLAlchemy table and fields.
    """
    
    def __init__(cls, name, bases, attrs):
        """
        Initialize the model class.
        """
        # Skip if this is the base Model class
        if name == 'Model':
            return super().__init__(name, bases, attrs)
        
        # Collect fields from the class
        fields = {}
        columns = {}
        relationships = {}
        
        for key, value in attrs.items():
            if isinstance(value, Field):
                # Set field name and model
                value.name = key
                value.model = name
                
                # Get SQLAlchemy column
                column = value.get_column()
                if column is not None:
                    columns[key] = column
                
                fields[key] = value
                
                # Handle relationship fields
                if hasattr(value, 'get_relationship'):
                    relationships[key] = value
        
        # Determine table name
        table_name = None
        if 'Meta' in attrs:
            meta = attrs['Meta']
            if hasattr(meta, 'db_table'):
                table_name = meta.db_table
            elif hasattr(meta, 'table_name'):
                table_name = meta.table_name

        if table_name is None:
             table_name = name.lower()

        # Set __tablename__ if not present, so DeclarativeMeta can do its job
        if not hasattr(cls, '__tablename__'):
            setattr(cls, '__tablename__', table_name)

        # Set _fields and _relationships
        setattr(cls, '_fields', fields)
        setattr(cls, '_relationships', relationships)

        # Set _meta
        meta_class = attrs.get('Meta', getattr(cls, 'Meta', None))
        setattr(cls, '_meta', Options(meta_class))
        
        # Add manager
        if 'objects' not in attrs:
            setattr(cls, 'objects', Manager(cls))
        
        # Add Meta class if not present
        if 'Meta' not in attrs:
            class Meta:
                pass
            setattr(cls, 'Meta', Meta)

        # Set manager's model
        if hasattr(cls, 'objects'):
            cls.objects.model = cls
        
        # Replace fields with SQLAlchemy columns on the class
        for field_name, column in columns.items():
            if field_name in relationships:
                # For relationships (ForeignKey, OneToOne), append _id to column name
                setattr(cls, f"{field_name}_id", column)
            else:
                setattr(cls, field_name, column)

        # Add properties for relationships
        for rel_name, rel_field in relationships.items():
            rel_property = rel_field.get_relationship(cls)
            setattr(cls, rel_name, rel_property)

            # Create M2M table if needed
            if isinstance(rel_field, ManyToManyField) and not rel_field.through:
                to_name = rel_field.to.lower() if isinstance(rel_field.to, str) else rel_field.to.__name__.lower()
                m2m_table_name = f"{name.lower()}_{to_name}"

                # Create association table if it doesn't exist
                # Use the class's metadata (from Base)
                if m2m_table_name not in cls.metadata.tables:
                    # We need column names. Usually model_id and other_id.
                    # We assume 'id' is PK for both.

                    # Target table name for ForeignKey
                    target_table = to_name
                    # Current table name
                    source_table = table_name

                    Table(
                        m2m_table_name,
                        cls.metadata,
                        Column('id', Integer, primary_key=True, autoincrement=True),
                        Column(f"{name.lower()}_id", Integer, SAForeignKey(f"{source_table}.id", ondelete="CASCADE")),
                        Column(f"{to_name}_id", Integer, SAForeignKey(f"{target_table}.id", ondelete="CASCADE"))
                    )

        # We need to call super().__init__
        super().__init__(name, bases, attrs)

        # Copy field metadata to InstrumentedAttributes to allow access like Model.field.max_length
        for field_name, field in fields.items():
            if hasattr(cls, field_name):
                attr = getattr(cls, field_name)
                # Copy common field attributes
                for metadata_attr in ['max_length', 'null', 'blank', 'default', 'choices', 'verbose_name', 'help_text']:
                    if hasattr(field, metadata_attr):
                        try:
                            # We can set attributes on the InstrumentedAttribute
                            setattr(attr, metadata_attr, getattr(field, metadata_attr))
                        except (AttributeError, TypeError):
                            pass


class Model(Base, metaclass=ModelMeta):
    """
    Base model class for FastJango ORM.
    """
    
    __abstract__ = True

    # Default primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Exception classes
    DoesNotExist = ObjectDoesNotExist
    MultipleObjectsReturned = MultipleObjectsReturned
    
    def __init__(self, **kwargs):
        """
        Initialize model instance.
        
        Args:
            **kwargs: Field values
        """
        # Set field values
        for field_name, value in kwargs.items():
            # Perform type conversion if field exists
            if field_name in self._fields:
                field = self._fields[field_name]
                try:
                    value = field.to_python(value)
                except ValidationError:
                    # If conversion fails, keep raw value? Or raise?
                    # Django raises on conversion failure during clean, but here we are in init.
                    # If we raise here, we break loose initialization.
                    # But if we don't convert, validation will fail later anyway.
                    # Let's allow raw value if conversion fails, assuming validation will catch it.
                    pass

            setattr(self, field_name, value)
        
        # Set auto_now_add fields
        for field_name, field in self._fields.items():
            if hasattr(field, 'auto_now_add') and field.auto_now_add:
                if not hasattr(self, field_name) or getattr(self, field_name) is None:
                    setattr(self, field_name, datetime.now())
    
    def save(self, using: Optional[str] = None) -> None:
        """
        Save the model instance.
        
        Args:
            using: Database to use (ignored for now)
        """
        session = get_session()
        
        # Set auto_now fields
        for field_name, field in self._fields.items():
            if hasattr(field, 'auto_now') and field.auto_now:
                setattr(self, field_name, datetime.now())
        
        # Validate the model
        self.full_clean()
        
        # Add to session and commit
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
    
    def refresh_from_db(self, using: Optional[str] = None, fields: Optional[List[str]] = None) -> None:
        """
        Refresh the model instance from database.
        
        Args:
            using: Database to use (ignored for now)
            fields: Specific fields to refresh
        """
        session = get_session()
        session.refresh(self)
    
    def full_clean(self, exclude: Optional[List[str]] = None) -> None:
        """
        Validate the model instance.
        
        Args:
            exclude: Fields to exclude from validation
            
        Raises:
            ValidationError: If validation fails
        """
        exclude = exclude or []
        errors = {}
        
        # Validate each field
        for field_name, field in self._fields.items():
            if field_name in exclude:
                continue
            
            value = getattr(self, field_name, None)
            try:
                validated_value = field.validate(value)
                setattr(self, field_name, validated_value)
            except ValidationError as e:
                errors[field_name] = str(e)
        
        # Call model's clean method
        try:
            self.clean()
        except ValidationError as e:
            if hasattr(e, 'message_dict'):
                errors.update(e.message_dict)
            else:
                errors['__all__'] = str(e)
        
        if errors:
            raise ValidationError(errors)
    
    def is_valid(self) -> bool:
        """
        Check if the model instance is valid.

        Returns:
            True if valid, False otherwise
        """
        try:
            self.full_clean()
            return True
        except ValidationError:
            return False

    def clean(self) -> None:
        """
        Custom validation method. Override in subclasses.
        """
        pass
    
    def __str__(self) -> str:
        """
        String representation of the model.
        
        Returns:
            String representation
        """
        # Try to use a meaningful field for string representation
        for field_name in ['name', 'title', 'id']:
            if hasattr(self, field_name):
                return str(getattr(self, field_name))
        return f"{self.__class__.__name__}(id={self.id})"
    
    def __repr__(self) -> str:
        """
        Representation of the model.
        
        Returns:
            Representation string
        """
        return f"<{self.__class__.__name__}: {self}>"
    
    @classmethod
    def _get_pk_field(cls) -> str:
        """
        Get the primary key field name.
        
        Returns:
            Primary key field name
        """
        for field_name, field in cls._fields.items():
            if field.primary_key:
                return field_name
        return 'id'
    
    @classmethod
    def _get_pk_value(cls, instance) -> Any:
        """
        Get the primary key value of an instance.
        
        Args:
            instance: Model instance
            
        Returns:
            Primary key value
        """
        pk_field = cls._get_pk_field()
        return getattr(instance, pk_field)
    
    @classmethod
    def _set_pk_value(cls, instance, value: Any) -> None:
        """
        Set the primary key value of an instance.
        
        Args:
            instance: Model instance
            value: Primary key value
        """
        pk_field = cls._get_pk_field()
        setattr(instance, pk_field, value)
    
    @property
    def pk(self) -> Any:
        """
        Get the primary key value.
        
        Returns:
            Primary key value
        """
        return self._get_pk_value(self)
    
    @pk.setter
    def pk(self, value: Any) -> None:
        """
        Set the primary key value.
        
        Args:
            value: Primary key value
        """
        self._set_pk_value(self, value)
    
    def get_absolute_url(self) -> str:
        """
        Get the absolute URL for this object.
        
        Returns:
            Absolute URL
        """
        # Default implementation - override in subclasses
        return f"/{self.__class__.__name__.lower()}/{self.pk}/"
    
    @classmethod
    def get_next_by_pk(cls, **kwargs) -> Optional['Model']:
        """
        Get the next object by primary key.
        
        Args:
            **kwargs: Additional filters
            
        Returns:
            Next model instance or None
        """
        pk_field = cls._get_pk_field()
        return cls.objects.filter(**kwargs).filter(**{f"{pk_field}__gt": cls.pk}).first()
    
    @classmethod
    def get_previous_by_pk(cls, **kwargs) -> Optional['Model']:
        """
        Get the previous object by primary key.
        
        Args:
            **kwargs: Additional filters
            
        Returns:
            Previous model instance or None
        """
        pk_field = cls._get_pk_field()
        return cls.objects.filter(**kwargs).filter(**{f"{pk_field}__lt": cls.pk}).order_by(f"-{pk_field}").first()