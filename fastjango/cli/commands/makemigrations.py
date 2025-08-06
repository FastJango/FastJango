"""
MakeMigrations command - Create database migration files
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastjango.core.logging import Logger
from fastjango.core.exceptions import CommandError
from fastjango.db.migrations import (
    Migration, MigrationOperation, CreateTable, AddColumn, 
    DropColumn, AlterColumn, CreateIndex, DropIndex
)
from fastjango.db.connection import get_engine
from fastjango.db.models import Model

logger = Logger("fastjango.cli.commands.makemigrations")


def detect_model_changes(app_label: str, models_dir: Path) -> List[MigrationOperation]:
    """
    Detect changes in models and generate migration operations.
    
    Args:
        app_label: The app label
        models_dir: Directory containing model files
        
    Returns:
        List of migration operations
    """
    operations = []
    
    # Get existing tables from database
    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Import and analyze models
    model_classes = []
    
    # Look for models.py file
    models_file = models_dir / "models.py"
    if models_file.exists():
        try:
            # Add the app directory to Python path
            sys.path.insert(0, str(models_dir.parent))
            
            # Import the models module
            spec = importlib.util.spec_from_file_location(f"{app_label}.models", models_file)
            models_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(models_module)
            
            # Find all Model classes
            for name, obj in inspect.getmembers(models_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Model) and 
                    obj != Model):
                    model_classes.append(obj)
                    
        except Exception as e:
            logger.error(f"Error importing models from {models_file}: {e}")
    
    # Analyze each model
    for model_class in model_classes:
        table_name = getattr(model_class.Meta, 'table_name', model_class.__name__.lower())
        
        if table_name not in existing_tables:
            # New table - create it
            columns = []
            for field_name, field in model_class._fields.items():
                column_def = {
                    'name': field_name,
                    'type': _get_sql_type(field),
                    'nullable': field.null,
                    'primary_key': field.primary_key,
                    'unique': field.unique,
                    'default': field.default
                }
                columns.append(column_def)
            
            operations.append(CreateTable(table_name, columns))
            logger.info(f"Detected new table: {table_name}")
        
        else:
            # Existing table - check for column changes
            existing_columns = {col['name']: col for col in inspector.get_columns(table_name)}
            
            for field_name, field in model_class._fields.items():
                if field_name not in existing_columns:
                    # New column
                    operations.append(AddColumn(
                        table_name=table_name,
                        column_name=field_name,
                        column_type=_get_sql_type(field),
                        nullable=field.null,
                        unique=field.unique,
                        default=field.default
                    ))
                    logger.info(f"Detected new column: {table_name}.{field_name}")
                
                else:
                    # Check for column changes
                    existing_col = existing_columns[field_name]
                    new_type = _get_sql_type(field)
                    
                    if existing_col['type'] != new_type:
                        operations.append(AlterColumn(
                            table_name=table_name,
                            column_name=field_name,
                            type=new_type
                        ))
                        logger.info(f"Detected column type change: {table_name}.{field_name}")
            
            # Check for dropped columns (simplified - would need more sophisticated tracking)
            model_fields = set(model_class._fields.keys())
            for col_name in existing_columns:
                if col_name not in model_fields and col_name != 'id':
                    operations.append(DropColumn(
                        table_name=table_name,
                        column_name=col_name
                    ))
                    logger.info(f"Detected dropped column: {table_name}.{col_name}")
    
    return operations


def _get_sql_type(field) -> str:
    """
    Get SQL type for a field.
    
    Args:
        field: Model field
        
    Returns:
        SQL type string
    """
    field_type = type(field).__name__
    
    type_mapping = {
        'CharField': f'VARCHAR({field.max_length})',
        'TextField': 'TEXT',
        'IntegerField': 'INTEGER',
        'BigIntegerField': 'BIGINT',
        'SmallIntegerField': 'SMALLINT',
        'PositiveIntegerField': 'INTEGER',
        'PositiveSmallIntegerField': 'SMALLINT',
        'FloatField': 'FLOAT',
        'DecimalField': f'DECIMAL({field.max_digits},{field.decimal_places})',
        'BooleanField': 'BOOLEAN',
        'NullBooleanField': 'BOOLEAN',
        'DateField': 'DATE',
        'DateTimeField': 'DATETIME',
        'TimeField': 'TIME',
        'DurationField': 'INTERVAL',
        'BinaryField': 'BLOB',
        'FileField': 'VARCHAR(255)',
        'ImageField': 'VARCHAR(255)',
        'FilePathField': 'VARCHAR(255)',
        'EmailField': f'VARCHAR({field.max_length})',
        'URLField': f'VARCHAR({field.max_length})',
        'SlugField': f'VARCHAR({field.max_length})',
        'UUIDField': 'UUID',
        'IPAddressField': 'VARCHAR(15)',
        'GenericIPAddressField': 'VARCHAR(45)',
        'CommaSeparatedIntegerField': f'VARCHAR({field.max_length})',
        'ForeignKey': 'INTEGER',
        'OneToOneField': 'INTEGER',
    }
    
    return type_mapping.get(field_type, 'TEXT')


def create_migration_file(app_label: str, migration_name: str, operations: List[MigrationOperation]) -> Path:
    """
    Create a migration file.
    
    Args:
        app_label: The app label
        migration_name: Name of the migration
        operations: List of migration operations
        
    Returns:
        Path to the created migration file
    """
    # Create migrations directory
    migrations_dir = Path.cwd() / app_label / "migrations"
    migrations_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py if it doesn't exist
    init_file = migrations_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")
    
    # Generate migration file content
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{migration_name}.py"
    migration_file = migrations_dir / filename
    
    # Create migration content
    content = f'''"""
Migration {migration_name} for {app_label}.
"""

from fastjango.db.migrations import Migration, {', '.join(op.__class__.__name__ for op in operations)}

# Migration operations
operations = [
{chr(10).join(f'    {op.__class__.__name__}(' + _operation_to_code(op) + '),' for op in operations)}
]

# Create migration
migration = Migration(
    name="{migration_name}",
    app_label="{app_label}",
    operations=operations
)
'''
    
    migration_file.write_text(content)
    logger.info(f"Created migration file: {migration_file}")
    
    return migration_file


def _operation_to_code(operation) -> str:
    """
    Convert operation to code string.
    
    Args:
        operation: Migration operation
        
    Returns:
        Code string representation
    """
    if isinstance(operation, CreateTable):
        columns_str = ',\n        '.join([
            f"{{'name': '{col['name']}', 'type': '{col['type']}', "
            f"'nullable': {col['nullable']}, 'primary_key': {col['primary_key']}, "
            f"'unique': {col['unique']}, 'default': {col['default']}}}"
            for col in operation.columns
        ])
        return f"table_name='{operation.table_name}', columns=[\n        {columns_str}\n    ]"
    
    elif isinstance(operation, AddColumn):
        return (f"table_name='{operation.table_name}', "
                f"column_name='{operation.column_name}', "
                f"column_type='{operation.column_type}', "
                f"nullable={operation.kwargs.get('nullable', True)}, "
                f"unique={operation.kwargs.get('unique', False)}, "
                f"default={operation.kwargs.get('default', None)}")
    
    elif isinstance(operation, DropColumn):
        return f"table_name='{operation.table_name}', column_name='{operation.column_name}'"
    
    elif isinstance(operation, AlterColumn):
        kwargs_str = ', '.join([f"'{k}': {repr(v)}" for k, v in operation.kwargs.items()])
        return f"table_name='{operation.table_name}', column_name='{operation.column_name}', {kwargs_str}"
    
    elif isinstance(operation, CreateIndex):
        columns_str = ', '.join([f"'{col}'" for col in operation.columns])
        return (f"table_name='{operation.table_name}', "
                f"index_name='{operation.index_name}', "
                f"columns=[{columns_str}], "
                f"unique={operation.unique}")
    
    elif isinstance(operation, DropIndex):
        return f"index_name='{operation.index_name}'"
    
    else:
        return ""


def make_migrations(app_label: str, migration_name: str = None) -> Optional[Path]:
    """
    Create migration files for an app.
    
    Args:
        app_label: The app label
        migration_name: Optional migration name
        
    Returns:
        Path to created migration file or None
    """
    try:
        # Find the app directory
        app_dir = Path.cwd() / app_label
        if not app_dir.exists():
            raise CommandError(f"App directory not found: {app_dir}")
        
        # Detect model changes
        operations = detect_model_changes(app_label, app_dir)
        
        if not operations:
            logger.info(f"No changes detected for app '{app_label}'")
            return None
        
        # Generate migration name if not provided
        if not migration_name:
            migration_name = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create migration file
        migration_file = create_migration_file(app_label, migration_name, operations)
        
        logger.info(f"Created migration '{migration_name}' for app '{app_label}'")
        return migration_file
        
    except Exception as e:
        logger.error(f"Error creating migration: {e}")
        raise CommandError(f"Failed to create migration: {e}")


def main():
    """Main function for makemigrations command."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Create database migration files")
    parser.add_argument("app_label", help="App label")
    parser.add_argument("--name", help="Migration name")
    
    args = parser.parse_args()
    
    try:
        migration_file = make_migrations(args.app_label, args.name)
        if migration_file:
            print(f"Migration created: {migration_file}")
        else:
            print("No changes detected")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()