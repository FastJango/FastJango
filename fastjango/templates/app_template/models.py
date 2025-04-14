"""
Models for {{app_name}} app.
"""

from fastjango.db import models
from fastjango.core.exceptions import ValidationError


class {{app_name_camel}}Model(models.Model):
    """
    Example model for {{app_name}} app.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "{{app_name_camel}}"
        verbose_name_plural = "{{app_name_camel}}s"
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """
        Custom validation logic.
        """
        if self.name.lower() == "test":
            raise ValidationError({"name": "Name cannot be 'test'"})
        
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs) 