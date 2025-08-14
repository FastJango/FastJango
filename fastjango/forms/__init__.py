"""
FastJango Forms - Django-like form system using Pydantic.
"""

from .forms import (
    Form, ModelForm, BaseForm,
    CharField, TextField, IntegerField, FloatField, DecimalField,
    BooleanField, ChoiceField, MultipleChoiceField, DateField,
    DateTimeField, TimeField, EmailField, URLField, FileField,
    ImageField, PasswordField, HiddenField, SlugField,
    ValidationError, FormError
)

# Optional widgets shim for compatibility in tests
try:
    from .widgets import (
        Widget, TextInput, PasswordInput, HiddenInput, NumberInput,
        EmailInput, URLInput, DateInput, DateTimeInput, TimeInput,
        Textarea, Select, SelectMultiple, CheckboxInput, RadioSelect,
        FileInput, ClearableFileInput, ImageInput
    )
except Exception:  # pragma: no cover
    # Provide minimal stand-ins if widgets module is absent
    class Widget: ...
    class TextInput(Widget): ...
    class PasswordInput(Widget): ...
    class HiddenInput(Widget): ...
    class NumberInput(Widget): ...
    class EmailInput(Widget): ...
    class URLInput(Widget): ...
    class DateInput(Widget): ...
    class DateTimeInput(Widget): ...
    class TimeInput(Widget): ...
    class Textarea(Widget): ...
    class Select(Widget): ...
    class SelectMultiple(Widget): ...
    class CheckboxInput(Widget): ...
    class RadioSelect(Widget): ...
    class FileInput(Widget): ...
    class ClearableFileInput(Widget): ...
    class ImageInput(Widget): ...

from .csrf import CSRFProtection, csrf_token, csrf_protect
from .utils import (
    formset_factory, modelformset_factory, inlineformset_factory,
    render_form, render_field, get_form_errors
)

__all__ = [
    # Forms
    'Form', 'ModelForm', 'BaseForm',
    'CharField', 'TextField', 'IntegerField', 'FloatField', 'DecimalField',
    'BooleanField', 'ChoiceField', 'MultipleChoiceField', 'DateField',
    'DateTimeField', 'TimeField', 'EmailField', 'URLField', 'FileField',
    'ImageField', 'PasswordField', 'HiddenField', 'SlugField',
    'ValidationError', 'FormError',
    
    # Widgets
    'Widget', 'TextInput', 'PasswordInput', 'HiddenInput', 'NumberInput',
    'EmailInput', 'URLInput', 'DateInput', 'DateTimeInput', 'TimeInput',
    'Textarea', 'Select', 'SelectMultiple', 'CheckboxInput', 'RadioSelect',
    'FileInput', 'ClearableFileInput', 'ImageInput',
    
    # CSRF
    'CSRFProtection', 'csrf_token', 'csrf_protect',
    
    # Utils
    'formset_factory', 'modelformset_factory', 'inlineformset_factory',
    'render_form', 'render_field', 'get_form_errors',
]