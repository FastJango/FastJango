"""
FastJango API Serializers - DRF-like serialization using Pydantic.
"""

from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from datetime import datetime, date, time
from decimal import Decimal
import json
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from pydantic.fields import FieldInfo
from pydantic.types import StrictBool, StrictInt, StrictFloat, StrictStr

from fastjango.core.exceptions import ValidationError
from fastjango.db import Model


class SerializerError(Exception):
    """Base exception for serializer errors."""
    pass


class Serializer(BaseModel):
    """
    Base serializer class that mimics DRF's Serializer using Pydantic.
    
    This provides a familiar API for Django developers while leveraging
    Pydantic's powerful validation and serialization capabilities.
    """
    
    class Config:
        # Allow extra fields during validation
        extra = "allow"
        # Use enum values
        use_enum_values = True
        # Allow arbitrary types
        arbitrary_types_allowed = True
    
    def __init__(self, instance=None, data=None, **kwargs):
        """
        Initialize the serializer.
        
        Args:
            instance: The model instance to serialize
            data: Data to validate and deserialize
            **kwargs: Additional arguments
        """
        self.instance = instance
        self.initial_data = data
        self._validated_data = None
        
        if data is not None:
            # Validate and deserialize data
            validated_data = self.run_validation(data)
            super().__init__(**validated_data)
        else:
            # Serialize instance
            if instance is not None:
                data = self.to_representation(instance)
                super().__init__(**data)
            else:
                super().__init__(**kwargs)
    
    def run_validation(self, data: Any) -> Dict[str, Any]:
        """
        Validate and deserialize data.
        
        Args:
            data: Data to validate
            
        Returns:
            Validated data dictionary
        """
        try:
            if isinstance(data, dict):
                return data
            elif hasattr(data, 'dict'):
                return data.dict()
            else:
                raise ValidationError("Invalid data format")
        except Exception as e:
            raise ValidationError(str(e))
    
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """
        Convert instance to dictionary representation.
        
        Args:
            instance: The instance to serialize
            
        Returns:
            Dictionary representation
        """
        if hasattr(instance, 'dict'):
            return instance.dict()
        elif hasattr(instance, '__dict__'):
            return instance.__dict__
        else:
            return {}
    
    def is_valid(self, raise_exception=False) -> bool:
        """
        Check if the serializer is valid.
        
        Args:
            raise_exception: Whether to raise an exception on validation errors
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self._validated_data = self.run_validation(self.initial_data)
            return True
        except ValidationError as e:
            if raise_exception:
                raise
            return False
    
    @property
    def errors(self) -> Dict[str, List[str]]:
        """Get validation errors."""
        if not hasattr(self, '_errors'):
            self._errors = {}
        return self._errors
    
    @property
    def validated_data(self) -> Dict[str, Any]:
        """Get validated data."""
        if self._validated_data is None:
            raise SerializerError("Data has not been validated")
        return self._validated_data
    
    def save(self, **kwargs) -> Any:
        """
        Save the validated data.
        
        Args:
            **kwargs: Additional arguments
            
        Returns:
            The saved instance
        """
        if self.instance is None:
            self.instance = self.create(self.validated_data)
        else:
            self.instance = self.update(self.instance, self.validated_data)
        return self.instance
    
    def create(self, validated_data: Dict[str, Any]) -> Any:
        """
        Create a new instance.
        
        Args:
            validated_data: Validated data
            
        Returns:
            The created instance
        """
        raise NotImplementedError("Subclasses must implement create()")
    
    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """
        Update an existing instance.
        
        Args:
            instance: The instance to update
            validated_data: Validated data
            
        Returns:
            The updated instance
        """
        raise NotImplementedError("Subclasses must implement update()")


class ModelSerializer(Serializer):
    """
    Serializer for model instances.
    
    Automatically generates fields based on model attributes.
    """
    
    def __init__(self, instance=None, data=None, **kwargs):
        """
        Initialize the model serializer.
        
        Args:
            instance: The model instance to serialize
            data: Data to validate and deserialize
            **kwargs: Additional arguments
        """
        self.Meta = getattr(self, 'Meta', None)
        self.model = getattr(self.Meta, 'model', None) if self.Meta else None
        self.fields = getattr(self.Meta, 'fields', '__all__') if self.Meta else '__all__'
        self.read_only_fields = getattr(self.Meta, 'read_only_fields', ()) if self.Meta else ()
        
        super().__init__(instance=instance, data=data, **kwargs)
    
    def get_fields(self) -> Dict[str, Any]:
        """
        Get the fields for this serializer.
        
        Returns:
            Dictionary of field definitions
        """
        if not self.model:
            return {}
        
        fields = {}
        model_fields = {}
        
        # Get model fields if it's a FastJango model
        if hasattr(self.model, '_meta') and hasattr(self.model._meta, 'fields'):
            model_fields = self.model._meta.fields
        
        # Get all attributes of the model
        for attr_name in dir(self.model):
            if not attr_name.startswith('_'):
                attr = getattr(self.model, attr_name)
                if not callable(attr):
                    fields[attr_name] = self._get_field_type(attr)
        
        # Filter fields based on Meta.fields
        if self.fields != '__all__':
            fields = {k: v for k, v in fields.items() if k in self.fields}
        
        # Add read-only fields
        for field_name in self.read_only_fields:
            if field_name in fields:
                fields[field_name] = (fields[field_name], ...)  # Make it read-only
        
        return fields
    
    def _get_field_type(self, value: Any) -> Type:
        """
        Get the Pydantic field type for a value.
        
        Args:
            value: The value to get the type for
            
        Returns:
            The Pydantic field type
        """
        if isinstance(value, str):
            return str
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, datetime):
            return datetime
        elif isinstance(value, date):
            return date
        elif isinstance(value, time):
            return time
        elif isinstance(value, Decimal):
            return Decimal
        else:
            return Any
    
    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """
        Convert model instance to dictionary representation.
        
        Args:
            instance: The model instance to serialize
            
        Returns:
            Dictionary representation
        """
        if hasattr(instance, 'dict'):
            return instance.dict()
        elif hasattr(instance, '__dict__'):
            return instance.__dict__
        else:
            return {}
    
    def create(self, validated_data: Dict[str, Any]) -> Any:
        """
        Create a new model instance.
        
        Args:
            validated_data: Validated data
            
        Returns:
            The created model instance
        """
        if self.model:
            return self.model(**validated_data)
        else:
            raise NotImplementedError("Model not specified")
    
    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        """
        Update an existing model instance.
        
        Args:
            instance: The instance to update
            validated_data: Validated data
            
        Returns:
            The updated model instance
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        return instance


class ListSerializer(Serializer):
    """
    Serializer for lists of objects.
    """
    
    def __init__(self, child=None, **kwargs):
        """
        Initialize the list serializer.
        
        Args:
            child: The child serializer class
            **kwargs: Additional arguments
        """
        self.child = child
        super().__init__(**kwargs)
    
    def to_representation(self, instance: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert list of instances to list of dictionaries.
        
        Args:
            instance: List of instances to serialize
            
        Returns:
            List of dictionary representations
        """
        return [self.child.to_representation(item) for item in instance]


class SerializerMethodField:
    """
    A read-only field that gets its value by calling a method on the serializer.
    """
    
    def __init__(self, method_name=None):
        """
        Initialize the serializer method field.
        
        Args:
            method_name: The name of the method to call
        """
        self.method_name = method_name
    
    def __call__(self, serializer, obj):
        """
        Call the method and return the result.
        
        Args:
            serializer: The serializer instance
            obj: The object being serialized
            
        Returns:
            The result of the method call
        """
        if self.method_name:
            method = getattr(serializer, self.method_name)
            return method(obj)
        return None


class ReadOnlyField:
    """A read-only field."""
    pass


class HiddenField:
    """A hidden field that is not included in serialization."""
    pass


# Example usage:
class UserSerializer(ModelSerializer):
    """Example user serializer."""
    
    class Meta:
        model = None  # Would be set to actual User model
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class ProductSerializer(ModelSerializer):
    """Example product serializer."""
    
    class Meta:
        model = None  # Would be set to actual Product model
        fields = ['id', 'name', 'price', 'description', 'category']
        read_only_fields = ['id']
    
    def get_category_name(self, obj):
        """Custom method field."""
        return obj.category.name if obj.category else None