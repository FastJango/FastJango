"""
Model classes for FastJango ORM.
"""

import inspect
from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime

from sqlalchemy import Column, Integer, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from .fields import Field
from .queryset import QuerySet
from .connection import get_session
from .exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned

# Create base class for all models
Base = declarative_base()

# Global metadata for all models
metadata = MetaData()


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


class ModelMeta(type):
    """
    Metaclass for Model to set up SQLAlchemy table and fields.
    """
    
    def __new__(mcs, name, bases, attrs):
        """
        Create a new model class.
        
        Args:
            name: Class name
            bases: Base classes
            attrs: Class attributes
            
        Returns:
            New model class
        """
        # Skip if this is the base Model class
        if name == 'Model':
            return super().__new__(mcs, name, bases, attrs)
        
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
        
        # Create SQLAlchemy table
        table_name = attrs.get('Meta', {}).table_name if hasattr(attrs, 'Meta') else name.lower()
        table = Table(table_name, metadata, *columns.values())
        
        # Add table to attrs
        attrs['__table__'] = table
        attrs['_fields'] = fields
        attrs['_relationships'] = relationships
        
        # Add manager
        if 'objects' not in attrs:
            attrs['objects'] = Manager(None)  # Will be set after class creation
        
        # Add Meta class if not present
        if 'Meta' not in attrs:
            class Meta:
                pass
            attrs['Meta'] = Meta
        
        # Create the class
        cls = super().__new__(mcs, name, bases, attrs)
        
        # Set manager's model
        cls.objects.model = cls
        
        # Add properties for fields
        for field_name, field in fields.items():
            setattr(cls, field_name, field)
        
        # Add properties for relationships
        for rel_name, rel_field in relationships.items():
            rel_property = rel_field.get_relationship(cls)
            setattr(cls, rel_name, rel_property)
        
        return cls


class Model(Base, metaclass=ModelMeta):
    """
    Base model class for FastJango ORM.
    """
    
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
        # Validate and set field values
        for field_name, value in kwargs.items():
            if field_name in self._fields:
                field = self._fields[field_name]
                validated_value = field.validate(value)
                setattr(self, field_name, validated_value)
            else:
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