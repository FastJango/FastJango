"""
API routes for {{app_name}} app.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional

from fastjango.core.dependencies import get_current_user
from .schemas import {{app_name_camel}}Create, {{app_name_camel}}Read, {{app_name_camel}}Update
from .services import {{app_name_camel}}Service

router = APIRouter(prefix="/{{app_name_snake}}", tags=["{{app_name}}"])
service = {{app_name_camel}}Service()


@router.get("/", response_model=List[{{app_name_camel}}Read])
async def list_{{app_name_snake}}s(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user)
):
    """
    List all {{app_name}}s.
    """
    return await service.get_all(skip=skip, limit=limit)


@router.post("/", response_model={{app_name_camel}}Read, status_code=status.HTTP_201_CREATED)
async def create_{{app_name_snake}}(
    item: {{app_name_camel}}Create,
    current_user = Depends(get_current_user)
):
    """
    Create a new {{app_name}}.
    """
    return await service.create(item)


@router.get("/{item_id}", response_model={{app_name_camel}}Read)
async def read_{{app_name_snake}}(
    item_id: int,
    current_user = Depends(get_current_user)
):
    """
    Get a specific {{app_name}} by ID.
    """
    item = await service.get_by_id(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{app_name_camel}} not found"
        )
    return item


@router.put("/{item_id}", response_model={{app_name_camel}}Read)
async def update_{{app_name_snake}}(
    item_id: int,
    item: {{app_name_camel}}Update,
    current_user = Depends(get_current_user)
):
    """
    Update a {{app_name}}.
    """
    updated_item = await service.update(item_id, item)
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{app_name_camel}} not found"
        )
    return updated_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{{app_name_snake}}(
    item_id: int,
    current_user = Depends(get_current_user)
):
    """
    Delete a {{app_name}}.
    """
    success = await service.delete(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="{{app_name_camel}} not found"
        )
    return {} 