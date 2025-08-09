"""
QuerySet for FastJango ORM - Django-like query operations.
"""

from typing import Any, List, Optional, Union, Dict, Tuple, Callable
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_, or_, not_, func, desc, asc
from sqlalchemy.sql import Select, Update, Delete

from .connection import get_session
from .exceptions import ValidationError


class QuerySet:
    """
    Django-like QuerySet for FastJango ORM.
    """
    
    def __init__(self, model_class, session: Optional[Session] = None):
        """
        Initialize QuerySet.
        
        Args:
            model_class: The model class
            session: SQLAlchemy session
        """
        self.model = model_class
        self.session = session or get_session()
        self._query = select(model_class)
        self._filters = []
        self._order_by = []
        self._limit = None
        self._offset = None
        self._distinct = False
        self._select_related = []
        self._prefetch_related = []
    
    def filter(self, **kwargs) -> 'QuerySet':
        """
        Filter queryset by field lookups.
        
        Args:
            **kwargs: Field lookups
            
        Returns:
            Filtered QuerySet
        """
        qs = self._clone()
        for field, value in kwargs.items():
            if '__' in field:
                field_name, lookup = field.split('__', 1)
                qs._filters.append(self._build_lookup_filter(field_name, lookup, value))
            else:
                qs._filters.append(getattr(self.model, field) == value)
        return qs
    
    def exclude(self, **kwargs) -> 'QuerySet':
        """
        Exclude objects matching criteria.
        
        Args:
            **kwargs: Field lookups
            
        Returns:
            Filtered QuerySet
        """
        qs = self._clone()
        for field, value in kwargs.items():
            if '__' in field:
                field_name, lookup = field.split('__', 1)
                qs._filters.append(not_(self._build_lookup_filter(field_name, lookup, value)))
            else:
                qs._filters.append(getattr(self.model, field) != value)
        return qs
    
    def order_by(self, *fields) -> 'QuerySet':
        """
        Order queryset by fields.
        
        Args:
            *fields: Field names (prefix with - for descending)
            
        Returns:
            Ordered QuerySet
        """
        qs = self._clone()
        for field in fields:
            if field.startswith('-'):
                field_name = field[1:]
                qs._order_by.append(desc(getattr(self.model, field_name)))
            else:
                qs._order_by.append(asc(getattr(self.model, field)))
        return qs
    
    def distinct(self) -> 'QuerySet':
        """
        Return distinct results.
        
        Returns:
            QuerySet with distinct results
        """
        qs = self._clone()
        qs._distinct = True
        return qs
    
    def values(self, *fields) -> List[Dict[str, Any]]:
        """
        Return dictionaries instead of model instances.
        
        Args:
            *fields: Field names to include
            
        Returns:
            List of dictionaries
        """
        if not fields:
            fields = [field.name for field in self.model.__table__.columns]
        
        query = select(*[getattr(self.model, field) for field in fields])
        query = self._apply_filters(query)
        query = self._apply_order_by(query)
        
        if self._distinct:
            query = query.distinct()
        
        if self._limit:
            query = query.limit(self._limit)
        
        if self._offset:
            query = query.offset(self._offset)
        
        result = self.session.execute(query)
        return [dict(zip(fields, row)) for row in result.fetchall()]
    
    def values_list(self, *fields, flat: bool = False) -> List[Union[Tuple, Any]]:
        """
        Return tuples of values instead of model instances.
        
        Args:
            *fields: Field names to include
            flat: If True and only one field, return flat list
            
        Returns:
            List of tuples or flat list
        """
        if not fields:
            fields = [field.name for field in self.model.__table__.columns]
        
        query = select(*[getattr(self.model, field) for field in fields])
        query = self._apply_filters(query)
        query = self._apply_order_by(query)
        
        if self._distinct:
            query = query.distinct()
        
        if self._limit:
            query = query.limit(self._limit)
        
        if self._offset:
            query = query.offset(self._offset)
        
        result = self.session.execute(query)
        rows = result.fetchall()
        
        if flat and len(fields) == 1:
            return [row[0] for row in rows]
        else:
            return list(rows)
    
    def get(self, **kwargs) -> Any:
        """
        Get a single object matching criteria.
        
        Args:
            **kwargs: Field lookups
            
        Returns:
            Model instance
            
        Raises:
            DoesNotExist: If no object found
            MultipleObjectsReturned: If multiple objects found
        """
        qs = self.filter(**kwargs)
        return qs.first()
    
    def first(self) -> Optional[Any]:
        """
        Get the first object.
        
        Returns:
            First model instance or None
        """
        query = self._build_query()
        query = query.limit(1)
        result = self.session.execute(query)
        row = result.fetchone()
        return row[0] if row else None
    
    def last(self) -> Optional[Any]:
        """
        Get the last object.
        
        Returns:
            Last model instance or None
        """
        # Get the primary key for ordering
        pk_field = None
        for field in self.model.__table__.columns:
            if field.primary_key:
                pk_field = field.name
                break
        
        if pk_field:
            qs = self.order_by(f'-{pk_field}')
        else:
            qs = self
        
        return qs.first()
    
    def count(self) -> int:
        """
        Count the number of objects.
        
        Returns:
            Number of objects
        """
        query = select(func.count(self.model.id))
        query = self._apply_filters(query)
        
        if self._distinct:
            query = select(func.count(func.distinct(self.model.id)))
            query = self._apply_filters(query)
        
        result = self.session.execute(query)
        return result.scalar()
    
    def exists(self) -> bool:
        """
        Check if any objects exist.
        
        Returns:
            True if objects exist
        """
        return self.count() > 0
    
    def all(self) -> List[Any]:
        """
        Get all objects.
        
        Returns:
            List of model instances
        """
        query = self._build_query()
        result = self.session.execute(query)
        return [row[0] for row in result.fetchall()]
    
    def create(self, **kwargs) -> Any:
        """
        Create and save a new object.
        
        Args:
            **kwargs: Field values
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        return instance
    
    def get_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[Any, bool]:
        """
        Get an object or create it if it doesn't exist.
        
        Args:
            defaults: Default values for creation
            **kwargs: Lookup parameters
            
        Returns:
            Tuple of (object, created)
        """
        defaults = defaults or {}
        
        try:
            obj = self.get(**kwargs)
            return obj, False
        except self.model.DoesNotExist:
            obj = self.model(**kwargs, **defaults)
            self.session.add(obj)
            self.session.commit()
            return obj, True
    
    def update_or_create(self, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> Tuple[Any, bool]:
        """
        Update an object or create it if it doesn't exist.
        
        Args:
            defaults: Default values for creation/update
            **kwargs: Lookup parameters
            
        Returns:
            Tuple of (object, created)
        """
        defaults = defaults or {}
        
        try:
            obj = self.get(**kwargs)
            for field, value in defaults.items():
                setattr(obj, field, value)
            self.session.commit()
            return obj, False
        except self.model.DoesNotExist:
            obj = self.model(**kwargs, **defaults)
            self.session.add(obj)
            self.session.commit()
            return obj, True
    
    def bulk_create(self, objects: List[Any], batch_size: int = 100) -> List[Any]:
        """
        Create multiple objects efficiently.
        
        Args:
            objects: List of model instances
            batch_size: Number of objects to create per batch
            
        Returns:
            List of created objects
        """
        created_objects = []
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            self.session.add_all(batch)
            self.session.commit()
            created_objects.extend(batch)
        
        return created_objects
    
    def update(self, **kwargs) -> int:
        """
        Update all objects in queryset.
        
        Args:
            **kwargs: Field updates
            
        Returns:
            Number of updated objects
        """
        query = update(self.model)
        query = self._apply_filters(query)
        query = query.values(**kwargs)
        
        result = self.session.execute(query)
        self.session.commit()
        return result.rowcount
    
    def delete(self) -> int:
        """
        Delete all objects in queryset.
        
        Returns:
            Number of deleted objects
        """
        query = delete(self.model)
        query = self._apply_filters(query)
        
        result = self.session.execute(query)
        self.session.commit()
        return result.rowcount
    
    def limit(self, limit: int) -> 'QuerySet':
        """
        Limit the number of results.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            Limited QuerySet
        """
        qs = self._clone()
        qs._limit = limit
        return qs
    
    def offset(self, offset: int) -> 'QuerySet':
        """
        Skip the first n results.
        
        Args:
            offset: Number of results to skip
            
        Returns:
            Offset QuerySet
        """
        qs = self._clone()
        qs._offset = offset
        return qs
    
    def select_related(self, *fields) -> 'QuerySet':
        """
        Follow foreign key relationships.
        
        Args:
            *fields: Related field names
            
        Returns:
            QuerySet with related objects
        """
        qs = self._clone()
        qs._select_related.extend(fields)
        return qs
    
    def prefetch_related(self, *fields) -> 'QuerySet':
        """
        Prefetch related objects.
        
        Args:
            *fields: Related field names
            
        Returns:
            QuerySet with prefetched objects
        """
        qs = self._clone()
        qs._prefetch_related.extend(fields)
        return qs
    
    def _clone(self) -> 'QuerySet':
        """Create a copy of this QuerySet."""
        qs = QuerySet(self.model, self.session)
        qs._query = self._query
        qs._filters = self._filters.copy()
        qs._order_by = self._order_by.copy()
        qs._limit = self._limit
        qs._offset = self._offset
        qs._distinct = self._distinct
        qs._select_related = self._select_related.copy()
        qs._prefetch_related = self._prefetch_related.copy()
        return qs
    
    def _build_query(self) -> Select:
        """Build the final SQLAlchemy query."""
        query = self._query
        query = self._apply_filters(query)
        query = self._apply_order_by(query)
        
        if self._distinct:
            query = query.distinct()
        
        if self._limit:
            query = query.limit(self._limit)
        
        if self._offset:
            query = query.offset(self._offset)
        
        return query
    
    def _apply_filters(self, query: Select) -> Select:
        """Apply filters to query."""
        if self._filters:
            query = query.where(and_(*self._filters))
        return query
    
    def _apply_order_by(self, query: Select) -> Select:
        """Apply ordering to query."""
        if self._order_by:
            query = query.order_by(*self._order_by)
        return query
    
    def _build_lookup_filter(self, field_name: str, lookup: str, value: Any):
        """Build filter for field lookups."""
        field = getattr(self.model, field_name)
        
        if lookup == 'exact':
            return field == value
        elif lookup == 'iexact':
            return func.lower(field) == func.lower(value)
        elif lookup == 'contains':
            return field.contains(value)
        elif lookup == 'icontains':
            return func.lower(field).contains(func.lower(value))
        elif lookup == 'in':
            return field.in_(value)
        elif lookup == 'gt':
            return field > value
        elif lookup == 'gte':
            return field >= value
        elif lookup == 'lt':
            return field < value
        elif lookup == 'lte':
            return field <= value
        elif lookup == 'startswith':
            return field.startswith(value)
        elif lookup == 'istartswith':
            return func.lower(field).startswith(func.lower(value))
        elif lookup == 'endswith':
            return field.endswith(value)
        elif lookup == 'iendswith':
            return func.lower(field).endswith(func.lower(value))
        elif lookup == 'range':
            return field.between(value[0], value[1])
        elif lookup == 'year':
            return func.extract('year', field) == value
        elif lookup == 'month':
            return func.extract('month', field) == value
        elif lookup == 'day':
            return func.extract('day', field) == value
        elif lookup == 'week':
            return func.extract('week', field) == value
        elif lookup == 'week_day':
            return func.extract('dow', field) == value
        elif lookup == 'quarter':
            return func.extract('quarter', field) == value
        elif lookup == 'time':
            return func.extract('time', field) == value
        elif lookup == 'hour':
            return func.extract('hour', field) == value
        elif lookup == 'minute':
            return func.extract('minute', field) == value
        elif lookup == 'second':
            return func.extract('second', field) == value
        elif lookup == 'isnull':
            if value:
                return field.is_(None)
            else:
                return field.is_not(None)
        elif lookup == 'regex':
            return field.op('REGEXP')(value)
        elif lookup == 'iregex':
            return func.lower(field).op('REGEXP')(func.lower(value))
        else:
            raise ValueError(f"Unknown lookup: {lookup}")
    
    def __iter__(self):
        """Iterate over QuerySet results."""
        return iter(self.all())
    
    def __len__(self):
        """Get the number of objects."""
        return self.count()
    
    def __getitem__(self, key):
        """Get item by index or slice."""
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop
            step = key.step or 1
            
            qs = self.offset(start)
            if stop is not None:
                qs = qs.limit(stop - start)
            
            return qs.all()[::step]
        else:
            return self.offset(key).limit(1).first()
    
    def __repr__(self):
        """String representation of QuerySet."""
        return f"<QuerySet [{self.model.__name__}]>"
