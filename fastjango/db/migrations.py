"""
Migrations for FastJango ORM.
"""

import os
import json
import importlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from .connection import get_engine
from .exceptions import DatabaseError


class MigrationOperation:
    """
    Base class for migration operations.
    """
    
    def __init__(self, **kwargs):
        """Initialize migration operation."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def forward(self, engine: Engine) -> None:
        """
        Apply the migration operation.
        
        Args:
            engine: SQLAlchemy engine
        """
        raise NotImplementedError("Subclasses must implement forward()")
    
    def reverse(self, engine: Engine) -> None:
        """
        Reverse the migration operation.
        
        Args:
            engine: SQLAlchemy engine
        """
        raise NotImplementedError("Subclasses must implement reverse()")
    
    def describe(self) -> str:
        """
        Get a description of the operation.
        
        Returns:
            Operation description
        """
        return f"{self.__class__.__name__}()"


class CreateTable(MigrationOperation):
    """
    Create a new table.
    """
    
    def __init__(self, table_name: str, columns: List[Dict[str, Any]]):
        """
        Initialize CreateTable operation.
        
        Args:
            table_name: Name of the table to create
            columns: List of column definitions
        """
        super().__init__()
        self.table_name = table_name
        self.columns = columns
    
    def forward(self, engine: Engine) -> None:
        """Create the table."""
        with engine.connect() as conn:
            # Build CREATE TABLE statement
            column_defs = []
            for column in self.columns:
                col_def = f"{column['name']} {column['type']}"
                if not column.get('nullable', True):
                    col_def += " NOT NULL"
                if column.get('primary_key'):
                    col_def += " PRIMARY KEY"
                if column.get('unique'):
                    col_def += " UNIQUE"
                if column.get('default') is not None:
                    col_def += f" DEFAULT {column['default']}"
                column_defs.append(col_def)
            
            create_sql = f"CREATE TABLE {self.table_name} ({', '.join(column_defs)})"
            conn.execute(text(create_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Drop the table."""
        with engine.connect() as conn:
            drop_sql = f"DROP TABLE {self.table_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Create table {self.table_name}"


class DropTable(MigrationOperation):
    """
    Drop a table.
    """
    
    def __init__(self, table_name: str):
        """
        Initialize DropTable operation.
        
        Args:
            table_name: Name of the table to drop
        """
        super().__init__()
        self.table_name = table_name
    
    def forward(self, engine: Engine) -> None:
        """Drop the table."""
        with engine.connect() as conn:
            drop_sql = f"DROP TABLE {self.table_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Recreate the table (basic implementation)."""
        # This would need the original table definition
        # For now, just log that we can't reverse this
        print(f"Warning: Cannot reverse DropTable for {self.table_name}")
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Drop table {self.table_name}"


class AddColumn(MigrationOperation):
    """
    Add a column to a table.
    """
    
    def __init__(self, table_name: str, column_name: str, column_type: str, **kwargs):
        """
        Initialize AddColumn operation.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to add
            column_type: SQL type of the column
            **kwargs: Additional column properties
        """
        super().__init__()
        self.table_name = table_name
        self.column_name = column_name
        self.column_type = column_type
        self.kwargs = kwargs
    
    def forward(self, engine: Engine) -> None:
        """Add the column."""
        with engine.connect() as conn:
            col_def = f"{self.column_name} {self.column_type}"
            if not self.kwargs.get('nullable', True):
                col_def += " NOT NULL"
            if self.kwargs.get('unique'):
                col_def += " UNIQUE"
            if self.kwargs.get('default') is not None:
                col_def += f" DEFAULT {self.kwargs['default']}"
            
            add_sql = f"ALTER TABLE {self.table_name} ADD COLUMN {col_def}"
            conn.execute(text(add_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Drop the column."""
        with engine.connect() as conn:
            drop_sql = f"ALTER TABLE {self.table_name} DROP COLUMN {self.column_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Add column {self.column_name} to {self.table_name}"


class DropColumn(MigrationOperation):
    """
    Drop a column from a table.
    """
    
    def __init__(self, table_name: str, column_name: str):
        """
        Initialize DropColumn operation.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to drop
        """
        super().__init__()
        self.table_name = table_name
        self.column_name = column_name
    
    def forward(self, engine: Engine) -> None:
        """Drop the column."""
        with engine.connect() as conn:
            drop_sql = f"ALTER TABLE {self.table_name} DROP COLUMN {self.column_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Recreate the column (basic implementation)."""
        # This would need the original column definition
        print(f"Warning: Cannot reverse DropColumn for {self.table_name}.{self.column_name}")
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Drop column {self.column_name} from {self.table_name}"


class AlterColumn(MigrationOperation):
    """
    Alter a column in a table.
    """
    
    def __init__(self, table_name: str, column_name: str, **kwargs):
        """
        Initialize AlterColumn operation.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column to alter
            **kwargs: Column properties to change
        """
        super().__init__()
        self.table_name = table_name
        self.column_name = column_name
        self.kwargs = kwargs
    
    def forward(self, engine: Engine) -> None:
        """Alter the column."""
        with engine.connect() as conn:
            # This is a simplified implementation
            # Real implementation would need to handle different database types
            if 'type' in self.kwargs:
                alter_sql = f"ALTER TABLE {self.table_name} ALTER COLUMN {self.column_name} TYPE {self.kwargs['type']}"
                conn.execute(text(alter_sql))
            
            if 'nullable' in self.kwargs:
                if self.kwargs['nullable']:
                    alter_sql = f"ALTER TABLE {self.table_name} ALTER COLUMN {self.column_name} DROP NOT NULL"
                else:
                    alter_sql = f"ALTER TABLE {self.table_name} ALTER COLUMN {self.column_name} SET NOT NULL"
                conn.execute(text(alter_sql))
            
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Reverse the column alteration."""
        # This would need to store the original column definition
        print(f"Warning: Cannot reverse AlterColumn for {self.table_name}.{self.column_name}")
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Alter column {self.column_name} in {self.table_name}"


class CreateIndex(MigrationOperation):
    """
    Create an index.
    """
    
    def __init__(self, table_name: str, index_name: str, columns: List[str], unique: bool = False):
        """
        Initialize CreateIndex operation.
        
        Args:
            table_name: Name of the table
            index_name: Name of the index
            columns: List of column names
            unique: Whether the index is unique
        """
        super().__init__()
        self.table_name = table_name
        self.index_name = index_name
        self.columns = columns
        self.unique = unique
    
    def forward(self, engine: Engine) -> None:
        """Create the index."""
        with engine.connect() as conn:
            unique_str = "UNIQUE" if self.unique else ""
            create_sql = f"CREATE {unique_str} INDEX {self.index_name} ON {self.table_name} ({', '.join(self.columns)})"
            conn.execute(text(create_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Drop the index."""
        with engine.connect() as conn:
            drop_sql = f"DROP INDEX {self.index_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def describe(self) -> str:
        """Get operation description."""
        unique_str = "unique " if self.unique else ""
        return f"Create {unique_str}index {self.index_name} on {self.table_name}"


class DropIndex(MigrationOperation):
    """
    Drop an index.
    """
    
    def __init__(self, index_name: str):
        """
        Initialize DropIndex operation.
        
        Args:
            index_name: Name of the index to drop
        """
        super().__init__()
        self.index_name = index_name
    
    def forward(self, engine: Engine) -> None:
        """Drop the index."""
        with engine.connect() as conn:
            drop_sql = f"DROP INDEX {self.index_name}"
            conn.execute(text(drop_sql))
            conn.commit()
    
    def reverse(self, engine: Engine) -> None:
        """Recreate the index (basic implementation)."""
        print(f"Warning: Cannot reverse DropIndex for {self.index_name}")
    
    def describe(self) -> str:
        """Get operation description."""
        return f"Drop index {self.index_name}"


class Migration:
    """
    Migration class for FastJango ORM.
    """
    
    def __init__(self, name: str, app_label: str, operations: List[MigrationOperation]):
        """
        Initialize migration.
        
        Args:
            name: Migration name
            app_label: App label
            operations: List of migration operations
        """
        self.name = name
        self.app_label = app_label
        self.operations = operations
        self.dependencies = []
    
    def apply(self, engine: Engine) -> None:
        """
        Apply the migration.
        
        Args:
            engine: SQLAlchemy engine
        """
        for operation in self.operations:
            try:
                operation.forward(engine)
                print(f"Applied: {operation.describe()}")
            except Exception as e:
                print(f"Error applying {operation.describe()}: {e}")
                raise
    
    def unapply(self, engine: Engine) -> None:
        """
        Unapply the migration.
        
        Args:
            engine: SQLAlchemy engine
        """
        for operation in reversed(self.operations):
            try:
                operation.reverse(engine)
                print(f"Reversed: {operation.describe()}")
            except Exception as e:
                print(f"Error reversing {operation.describe()}: {e}")
                raise
    
    def describe(self) -> str:
        """
        Get migration description.
        
        Returns:
            Migration description
        """
        return f"Migration {self.name} for {self.app_label}"


class MigrationRecorder:
    """
    Record applied migrations in database.
    """
    
    def __init__(self, engine: Engine):
        """
        Initialize migration recorder.
        
        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine
        self._ensure_migration_table()
    
    def _ensure_migration_table(self) -> None:
        """Ensure the migration table exists."""
        with self.engine.connect() as conn:
            # Check if table exists
            inspector = inspect(self.engine)
            if 'fastjango_migrations' not in inspector.get_table_names():
                create_sql = """
                CREATE TABLE fastjango_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_label VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                conn.execute(text(create_sql))
                conn.commit()
    
    def record_applied(self, app_label: str, name: str) -> None:
        """
        Record that a migration was applied.
        
        Args:
            app_label: App label
            name: Migration name
        """
        with self.engine.connect() as conn:
            insert_sql = """
            INSERT INTO fastjango_migrations (app_label, name)
            VALUES (:app_label, :name)
            """
            conn.execute(text(insert_sql), {"app_label": app_label, "name": name})
            conn.commit()
    
    def record_unapplied(self, app_label: str, name: str) -> None:
        """
        Record that a migration was unapplied.
        
        Args:
            app_label: App label
            name: Migration name
        """
        with self.engine.connect() as conn:
            delete_sql = """
            DELETE FROM fastjango_migrations
            WHERE app_label = :app_label AND name = :name
            """
            conn.execute(text(delete_sql), {"app_label": app_label, "name": name})
            conn.commit()
    
    def get_applied_migrations(self) -> List[Dict[str, str]]:
        """
        Get list of applied migrations.
        
        Returns:
            List of applied migration records
        """
        with self.engine.connect() as conn:
            select_sql = """
            SELECT app_label, name FROM fastjango_migrations
            ORDER BY app_label, name
            """
            result = conn.execute(text(select_sql))
            return [{"app_label": row[0], "name": row[1]} for row in result.fetchall()]


class MigrationLoader:
    """
    Load migrations from files.
    """
    
    def __init__(self, migrations_dir: str):
        """
        Initialize migration loader.
        
        Args:
            migrations_dir: Directory containing migration files
        """
        self.migrations_dir = Path(migrations_dir)
    
    def load_migration(self, app_label: str, name: str) -> Migration:
        """
        Load a migration from file.
        
        Args:
            app_label: App label
            name: Migration name
            
        Returns:
            Migration object
        """
        migration_file = self.migrations_dir / app_label / f"{name}.py"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        # Load the migration module
        spec = importlib.util.spec_from_file_location(f"{app_label}.{name}", migration_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get the migration object
        migration = getattr(module, 'migration')
        if not isinstance(migration, Migration):
            raise ValueError(f"Invalid migration in {migration_file}")
        
        return migration
    
    def get_migration_files(self, app_label: str) -> List[str]:
        """
        Get list of migration files for an app.
        
        Args:
            app_label: App label
            
        Returns:
            List of migration names
        """
        app_dir = self.migrations_dir / app_label
        if not app_dir.exists():
            return []
        
        migration_files = []
        for file in app_dir.glob("*.py"):
            if file.name != "__init__.py":
                migration_files.append(file.stem)
        
        return sorted(migration_files)


def create_migration(app_label: str, name: str, operations: List[MigrationOperation]) -> Migration:
    """
    Create a new migration.
    
    Args:
        app_label: App label
        name: Migration name
        operations: List of migration operations
        
    Returns:
        Migration object
    """
    return Migration(name, app_label, operations)


def apply_migrations(migrations: List[Migration], engine: Engine) -> None:
    """
    Apply a list of migrations.
    
    Args:
        migrations: List of migrations to apply
        engine: SQLAlchemy engine
    """
    recorder = MigrationRecorder(engine)
    
    for migration in migrations:
        # Check if already applied
        applied = recorder.get_applied_migrations()
        already_applied = any(
            m['app_label'] == migration.app_label and m['name'] == migration.name
            for m in applied
        )
        
        if not already_applied:
            migration.apply(engine)
            recorder.record_applied(migration.app_label, migration.name)
            print(f"Applied migration: {migration.name}")


def unapply_migrations(migrations: List[Migration], engine: Engine) -> None:
    """
    Unapply a list of migrations.
    
    Args:
        migrations: List of migrations to unapply
        engine: SQLAlchemy engine
    """
    recorder = MigrationRecorder(engine)
    
    for migration in reversed(migrations):
        # Check if applied
        applied = recorder.get_applied_migrations()
        is_applied = any(
            m['app_label'] == migration.app_label and m['name'] == migration.name
            for m in applied
        )
        
        if is_applied:
            migration.unapply(engine)
            recorder.record_unapplied(migration.app_label, migration.name)
            print(f"Unapplied migration: {migration.name}")


def show_migrations(engine: Engine, migrations_dir: str) -> None:
    """
    Show migration status.
    
    Args:
        engine: SQLAlchemy engine
        migrations_dir: Directory containing migration files
    """
    recorder = MigrationRecorder(engine)
    loader = MigrationLoader(migrations_dir)
    
    applied = recorder.get_applied_migrations()
    applied_set = {(m['app_label'], m['name']) for m in applied}
    
    print("Migration Status:")
    print("=" * 50)
    
    # Get all apps with migrations
    apps_dir = Path(migrations_dir)
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "__init__.py").exists():
            app_label = app_dir.name
            migration_files = loader.get_migration_files(app_label)
            
            print(f"\nApp: {app_label}")
            for migration_name in migration_files:
                status = "[X]" if (app_label, migration_name) in applied_set else "[ ]"
                print(f"  {status} {migration_name}")
