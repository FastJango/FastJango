"""
Pydantic schemas for {{app_name}} app.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class {{app_name_camel}}Base(BaseModel):
    """
    Base schema for {{app_name_camel}}.
    """
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=0, max_length=1000)


class {{app_name_camel}}Create({{app_name_camel}}Base):
    """
    Schema for creating a {{app_name_camel}}.
    """
    pass


class {{app_name_camel}}Update(BaseModel):
    """
    Schema for updating a {{app_name_camel}}.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=0, max_length=1000)


class {{app_name_camel}}Read({{app_name_camel}}Base):
    """
    Schema for reading a {{app_name_camel}}.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 