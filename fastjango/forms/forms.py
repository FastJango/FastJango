"""
FastJango Forms - Django-like form classes using Pydantic.
"""

import re
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError
from pydantic.fields import FieldInfo

from fastjango.core.exceptions import ValidationError
from fastjango.db import Model


class FormError(Exception):
    """Base exception for form errors."""
    pass


class BaseForm(BaseModel):
    """
    Base form class that mimics Django's Form using Pydantic.
    
    This provides a familiar API for Django developers while leveraging
    Pydantic's powerful validation capabilities.
    """
    
    class Config:
        # Allow extra fields during validation
        extra = "allow"
        # Use enum values
        use_enum_values = True
        # Allow arbitrary types
        arbitrary_types_allowed = True
    
    def __init__(self, data=None, files=None, **kwargs):
        """
        Initialize the form.
        
        Args:
            data: Form data dictionary
            files: Uploaded files
            **kwargs: Additional arguments
        """
        self.data = data or {}
        self.files = files or {}
        self.errors = {}
        self.cleaned_data = {}
        
        if data:
            self._validate_data()
        else:
            super().__init__(**kwargs)
    
    def _validate_data(self):
        """Validate form data."""
        try:
            # Convert data to Pydantic model
            validated_data = self._clean_data()
            super().__init__(**validated_data)
            self.cleaned_data = validated_data
        except PydanticValidationError as e:
            self._handle_validation_errors(e)
    
    def _clean_data(self) -> Dict[str, Any]:
        """
        Clean and validate form data.
        
        Returns:
            Cleaned data dictionary
        """
        cleaned_data = {}
        
        for field_name, field_info in self.model_fields.items():
            if field_name in self.data:
                value = self.data[field_name]
                cleaned_data[field_name] = self._clean_field(field_name, value, field_info)
        
        return cleaned_data
    
    def _clean_field(self, field_name: str, value: Any, field_info: FieldInfo) -> Any:
        """
        Clean a single field value.
        
        Args:
            field_name: The field name
            value: The field value
            field_info: The field info
            
        Returns:
            Cleaned field value
        """
        # Basic cleaning
        if isinstance(value, str):
            value = value.strip()
        
        # Type conversion
        field_type = field_info.annotation
        if field_type and value is not None:
            try:
                if field_type == int:
                    value = int(value)
                elif field_type == float:
                    value = float(value)
                elif field_type == bool:
                    value = bool(value)
                elif field_type == Decimal:
                    value = Decimal(str(value))
                elif field_type == date:
                    if isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                elif field_type == datetime:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif field_type == time:
                    if isinstance(value, str):
                        value = datetime.strptime(value, '%H:%M:%S').time()
            except (ValueError, TypeError):
                raise ValidationError(f"Invalid value for {field_name}")
        
        return value
    
    def _handle_validation_errors(self, e: PydanticValidationError):
        """Handle Pydantic validation errors."""
        for error in e.errors():
            field_name = error['loc'][0] if error['loc'] else 'non_field_errors'
            message = error['msg']
            
            if field_name not in self.errors:
                self.errors[field_name] = []
            
            self.errors[field_name].append(message)
    
    def is_valid(self) -> bool:
        """
        Check if the form is valid.
        
        Returns:
            True if valid, False otherwise
        """
        return len(self.errors) == 0
    
    def save(self, commit=True):
        """
        Save the form data.
        
        Args:
            commit: Whether to commit the save
            
        Returns:
            The saved instance
        """
        if commit:
            return self._save()
        else:
            return self._save_m2m()
    
    def _save(self):
        """Save the form data."""
        raise NotImplementedError("Subclasses must implement _save()")
    
    def _save_m2m(self):
        """Save many-to-many relationships."""
        pass


class Form(BaseForm):
    """
    Basic form class for simple forms.
    """
    
    def _save(self):
        """Save the form data."""
        return self.cleaned_data


class ModelForm(BaseForm):
    """
    Form class for model instances.
    """
    
    class Meta:
        model = None
        fields = '__all__'
        exclude = []
    
    def __init__(self, instance=None, data=None, files=None, **kwargs):
        """
        Initialize the model form.
        
        Args:
            instance: The model instance to edit
            data: Form data
            files: Uploaded files
            **kwargs: Additional arguments
        """
        self.instance = instance
        super().__init__(data=data, files=files, **kwargs)
    
    def _save(self):
        """Save the form data to the model instance."""
        if self.instance is None:
            self.instance = self.Meta.model(**self.cleaned_data)
        else:
            for field, value in self.cleaned_data.items():
                setattr(self.instance, field, value)
        
        if hasattr(self.instance, 'save'):
            self.instance.save()
        
        return self.instance


# Form fields
class CharField:
    """Character field for forms."""
    
    def __init__(self, max_length=None, min_length=None, required=True, initial=None, help_text=None):
        self.max_length = max_length
        self.min_length = min_length
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            value = str(value).strip()
            
            if self.min_length and len(value) < self.min_length:
                raise ValidationError(f"Ensure this value has at least {self.min_length} characters.")
            
            if self.max_length and len(value) > self.max_length:
                raise ValidationError(f"Ensure this value has at most {self.max_length} characters.")
        
        return value


class TextField(CharField):
    """Text field for forms."""
    pass


class IntegerField:
    """Integer field for forms."""
    
    def __init__(self, min_value=None, max_value=None, required=True, initial=None, help_text=None):
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            try:
                value = int(value)
                
                if self.min_value is not None and value < self.min_value:
                    raise ValidationError(f"Ensure this value is greater than or equal to {self.min_value}.")
                
                if self.max_value is not None and value > self.max_value:
                    raise ValidationError(f"Ensure this value is less than or equal to {self.max_value}.")
            except (ValueError, TypeError):
                raise ValidationError("Enter a valid integer.")
        
        return value


class FloatField:
    """Float field for forms."""
    
    def __init__(self, min_value=None, max_value=None, required=True, initial=None, help_text=None):
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            try:
                value = float(value)
                
                if self.min_value is not None and value < self.min_value:
                    raise ValidationError(f"Ensure this value is greater than or equal to {self.min_value}.")
                
                if self.max_value is not None and value > self.max_value:
                    raise ValidationError(f"Ensure this value is less than or equal to {self.max_value}.")
            except (ValueError, TypeError):
                raise ValidationError("Enter a valid number.")
        
        return value


class DecimalField:
    """Decimal field for forms."""
    
    def __init__(self, max_digits=None, decimal_places=None, min_value=None, max_value=None, required=True, initial=None, help_text=None):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            try:
                value = Decimal(str(value))
                
                if self.min_value is not None and value < self.min_value:
                    raise ValidationError(f"Ensure this value is greater than or equal to {self.min_value}.")
                
                if self.max_value is not None and value > self.max_value:
                    raise ValidationError(f"Ensure this value is less than or equal to {self.max_value}.")
            except (ValueError, TypeError):
                raise ValidationError("Enter a valid decimal number.")
        
        return value


class BooleanField:
    """Boolean field for forms."""
    
    def __init__(self, required=True, initial=None, help_text=None):
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'yes', 'on')
            else:
                value = bool(value)
        
        return value


class ChoiceField:
    """Choice field for forms."""
    
    def __init__(self, choices=None, required=True, initial=None, help_text=None):
        self.choices = choices or []
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            valid_choices = [choice[0] for choice in self.choices]
            if value not in valid_choices:
                raise ValidationError("Select a valid choice.")
        
        return value


class MultipleChoiceField(ChoiceField):
    """Multiple choice field for forms."""
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            if not isinstance(value, list):
                value = [value]
            
            valid_choices = [choice[0] for choice in self.choices]
            for v in value:
                if v not in valid_choices:
                    raise ValidationError("Select a valid choice.")
        
        return value


class DateField:
    """Date field for forms."""
    
    def __init__(self, required=True, initial=None, help_text=None, input_formats=None):
        self.required = required
        self.initial = initial
        self.help_text = help_text
        self.input_formats = input_formats or ['%Y-%m-%d']
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            if isinstance(value, str):
                for fmt in self.input_formats:
                    try:
                        value = datetime.strptime(value, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    raise ValidationError("Enter a valid date.")
            elif isinstance(value, datetime):
                value = value.date()
        
        return value


class DateTimeField:
    """DateTime field for forms."""
    
    def __init__(self, required=True, initial=None, help_text=None, input_formats=None):
        self.required = required
        self.initial = initial
        self.help_text = help_text
        self.input_formats = input_formats or ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            if isinstance(value, str):
                for fmt in self.input_formats:
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValidationError("Enter a valid date/time.")
        
        return value


class TimeField:
    """Time field for forms."""
    
    def __init__(self, required=True, initial=None, help_text=None, input_formats=None):
        self.required = required
        self.initial = initial
        self.help_text = help_text
        self.input_formats = input_formats or ['%H:%M:%S', '%H:%M']
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            if isinstance(value, str):
                for fmt in self.input_formats:
                    try:
                        value = datetime.strptime(value, fmt).time()
                        break
                    except ValueError:
                        continue
                else:
                    raise ValidationError("Enter a valid time.")
            elif isinstance(value, datetime):
                value = value.time()
        
        return value


class EmailField(CharField):
    """Email field for forms."""
    
    def clean(self, value):
        """Clean the field value."""
        value = super().clean(value)
        
        if value:
            # Basic email validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                raise ValidationError("Enter a valid email address.")
        
        return value


class URLField(CharField):
    """URL field for forms."""
    
    def clean(self, value):
        """Clean the field value."""
        value = super().clean(value)
        
        if value:
            # Basic URL validation
            url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(url_pattern, value):
                raise ValidationError("Enter a valid URL.")
        
        return value


class FileField:
    """File field for forms."""
    
    def __init__(self, max_length=None, allow_empty_file=False, required=True, initial=None, help_text=None):
        self.max_length = max_length
        self.allow_empty_file = allow_empty_file
        self.required = required
        self.initial = initial
        self.help_text = help_text
    
    def clean(self, value):
        """Clean the field value."""
        if value is None and self.required:
            raise ValidationError("This field is required.")
        
        if value is not None:
            # Basic file validation
            if hasattr(value, 'size') and value.size == 0 and not self.allow_empty_file:
                raise ValidationError("The submitted file is empty.")
            
            if self.max_length and hasattr(value, 'size') and value.size > self.max_length:
                raise ValidationError(f"File too large. Size should not exceed {self.max_length} bytes.")
        
        return value


class ImageField(FileField):
    """Image field for forms."""
    
    def clean(self, value):
        """Clean the field value."""
        value = super().clean(value)
        
        if value:
            # Basic image validation
            if hasattr(value, 'content_type'):
                if not value.content_type.startswith('image/'):
                    raise ValidationError("Upload a valid image.")
        
        return value


class PasswordField(CharField):
    """Password field for forms."""
    
    def __init__(self, render_value=False, **kwargs):
        self.render_value = render_value
        super().__init__(**kwargs)


class HiddenField(CharField):
    """Hidden field for forms."""
    pass


class SlugField(CharField):
    """Slug field for forms."""
    
    def clean(self, value):
        """Clean the field value."""
        value = super().clean(value)
        
        if value:
            # Basic slug validation
            slug_pattern = r'^[a-z0-9-]+$'
            if not re.match(slug_pattern, value):
                raise ValidationError("Enter a valid slug consisting of letters, numbers, underscores or hyphens.")
        
        return value


# Example usage:
class UserRegistrationForm(Form):
    """Example user registration form."""
    
    username: str = Field(..., min_length=3, max_length=30)
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    
    def clean(self):
        """Custom form validation."""
        cleaned_data = super().clean()
        
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords don't match.")
        
        return cleaned_data


class ProductForm(ModelForm):
    """Example product form."""
    
    class Meta:
        model = None  # Would be set to actual Product model
        fields = ['name', 'description', 'price', 'category']
    
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    price: Decimal = Field(..., ge=0)
    category: str = Field(..., min_length=1)
