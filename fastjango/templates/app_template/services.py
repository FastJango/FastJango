"""
Services for {{app_name}} app.
"""

from typing import List, Optional
import logging

from fastjango.core.exceptions import ServiceError
from .models import {{app_name_camel}}Model
from .schemas import {{app_name_camel}}Create, {{app_name_camel}}Update

logger = logging.getLogger(__name__)


class {{app_name_camel}}Service:
    """
    Service for handling {{app_name_camel}} operations.
    """
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{{app_name_camel}}Model]:
        """
        Get all {{app_name_camel}} objects.
        """
        try:
            return {{app_name_camel}}Model.objects.all()[skip:skip+limit]
        except Exception as e:
            logger.error(f"Error fetching {{app_name_camel}} list: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to fetch {{app_name_camel}} list")
    
    async def get_by_id(self, item_id: int) -> Optional[{{app_name_camel}}Model]:
        """
        Get a {{app_name_camel}} by ID.
        """
        try:
            return {{app_name_camel}}Model.objects.filter(id=item_id).first()
        except Exception as e:
            logger.error(f"Error fetching {{app_name_camel}} with ID {item_id}: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to fetch {{app_name_camel}}")
    
    async def create(self, item: {{app_name_camel}}Create) -> {{app_name_camel}}Model:
        """
        Create a new {{app_name_camel}}.
        """
        try:
            return {{app_name_camel}}Model.objects.create(**item.dict())
        except Exception as e:
            logger.error(f"Error creating {{app_name_camel}}: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to create {{app_name_camel}}")
    
    async def update(self, item_id: int, item: {{app_name_camel}}Update) -> Optional[{{app_name_camel}}Model]:
        """
        Update a {{app_name_camel}}.
        """
        try:
            obj = await self.get_by_id(item_id)
            if not obj:
                return None
            
            # Update fields that are present in the request
            for field, value in item.dict(exclude_unset=True).items():
                setattr(obj, field, value)
            
            obj.save()
            return obj
        except Exception as e:
            logger.error(f"Error updating {{app_name_camel}} with ID {item_id}: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to update {{app_name_camel}}")
    
    async def delete(self, item_id: int) -> bool:
        """
        Delete a {{app_name_camel}}.
        """
        try:
            obj = await self.get_by_id(item_id)
            if not obj:
                return False
            
            obj.delete()
            return True
        except Exception as e:
            logger.error(f"Error deleting {{app_name_camel}} with ID {item_id}: {str(e)}", exc_info=True)
            raise ServiceError(f"Failed to delete {{app_name_camel}}") 