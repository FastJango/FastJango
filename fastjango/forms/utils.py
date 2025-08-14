"""
Utility helpers for FastJango forms.
Minimal implementations to support tests; extend as needed.
"""
from typing import Any, Callable, List, Optional


def formset_factory(form_class: Any, extra: int = 0) -> Callable[..., List[Any]]:
    def factory(data_list: Optional[List[dict]] = None) -> List[Any]:
        items = data_list or [{} for _ in range(extra)]
        return [form_class(data=item) for item in items]
    return factory


def modelformset_factory(model: Any, form_class: Any, extra: int = 0) -> Callable[..., List[Any]]:
    return formset_factory(form_class, extra=extra)


def inlineformset_factory(parent_model: Any, model: Any, form_class: Any, extra: int = 0) -> Callable[..., List[Any]]:
    return formset_factory(form_class, extra=extra)


def render_form(form: Any) -> str:
    # Simple serializer for tests
    fields = getattr(form, 'model_fields', {})
    return "\n".join(str(name) for name in fields)


def render_field(field: Any) -> str:
    return str(getattr(field, 'name', 'field'))


def get_form_errors(form: Any) -> dict:
    return getattr(form, 'errors', {})