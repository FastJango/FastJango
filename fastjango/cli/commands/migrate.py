"""
Migrate command - Apply database migrations
"""

import os
import sys
import importlib
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from fastjango.core.logging import Logger
from fastjango.core.exceptions import CommandError
from fastjango.db.migrations import Migration, MigrationLoader, apply_migrations
from fastjango.db.connection import get_engine

logger = Logger("fastjango.cli.commands.migrate")


def load_migrations(app_label: str) -> List[Migration]:
    """
    Load migration files for an app.
    
    Args:
        app_label: The app label
        
    Returns:
        List of migration objects
    """
    migrations_dir = Path.cwd() / app_label / "migrations"
    
    if not migrations_dir.exists():
        logger.info(f"No migrations directory found for app '{app_label}'")
        return []
    
    loader = MigrationLoader(str(migrations_dir))
    migration_files = loader.get_migration_files(app_label)
    
    migrations = []
    for migration_name in migration_files:
        try:
            migration = loader.load_migration(app_label, migration_name)
            migrations.append(migration)
        except Exception as e:
            logger.error(f"Error loading migration {migration_name}: {e}")
            raise CommandError(f"Failed to load migration {migration_name}: {e}")
    
    return migrations


def get_applied_migrations() -> List[dict]:
    """
    Get list of applied migrations from database.
    
    Returns:
        List of applied migration records
    """
    from fastjango.db.migrations import MigrationRecorder
    
    engine = get_engine()
    recorder = MigrationRecorder(engine)
    return recorder.get_applied_migrations()


def get_pending_migrations(app_label: str) -> List[Migration]:
    """
    Get pending migrations for an app.
    
    Args:
        app_label: The app label
        
    Returns:
        List of pending migrations
    """
    all_migrations = load_migrations(app_label)
    applied_migrations = get_applied_migrations()
    
    # Create set of applied migrations for this app
    applied_set = {
        (m['app_label'], m['name']) 
        for m in applied_migrations 
        if m['app_label'] == app_label
    }
    
    # Filter out already applied migrations
    pending_migrations = []
    for migration in all_migrations:
        if (app_label, migration.name) not in applied_set:
            pending_migrations.append(migration)
    
    return pending_migrations


def migrate_app(app_label: str, fake: bool = False) -> int:
    """
    Apply migrations for an app.
    
    Args:
        app_label: The app label
        fake: Whether to fake the migration (mark as applied without running)
        
    Returns:
        Number of migrations applied
    """
    try:
        pending_migrations = get_pending_migrations(app_label)
        
        if not pending_migrations:
            logger.info(f"No pending migrations for app '{app_label}'")
            return 0
        
        logger.info(f"Found {len(pending_migrations)} pending migrations for app '{app_label}'")
        
        if fake:
            # Mark migrations as applied without running them
            from fastjango.db.migrations import MigrationRecorder
            engine = get_engine()
            recorder = MigrationRecorder(engine)
            
            for migration in pending_migrations:
                recorder.record_applied(app_label, migration.name)
                logger.info(f"Faked migration: {migration.name}")
            
            return len(pending_migrations)
        else:
            # Apply migrations
            engine = get_engine()
            apply_migrations(pending_migrations, engine)
            return len(pending_migrations)
            
    except Exception as e:
        logger.error(f"Error applying migrations for app '{app_label}': {e}")
        raise CommandError(f"Failed to apply migrations: {e}")


def migrate_all_apps(fake: bool = False) -> int:
    """
    Apply migrations for all apps.
    
    Args:
        fake: Whether to fake the migrations
        
    Returns:
        Total number of migrations applied
    """
    total_applied = 0
    
    # Find all app directories
    current_dir = Path.cwd()
    app_dirs = [d for d in current_dir.iterdir() if d.is_dir() and (d / "models.py").exists()]
    
    for app_dir in app_dirs:
        app_label = app_dir.name
        try:
            applied_count = migrate_app(app_label, fake)
            total_applied += applied_count
        except Exception as e:
            logger.error(f"Error migrating app '{app_label}': {e}")
            # Continue with other apps
    
    return total_applied


def show_migration_status(app_label: str = None):
    """
    Show migration status.
    
    Args:
        app_label: Optional app label to show status for
    """
    from fastjango.db.migrations import show_migrations
    
    engine = get_engine()
    migrations_dir = str(Path.cwd())
    
    if app_label:
        # Show status for specific app
        app_migrations_dir = Path.cwd() / app_label / "migrations"
        if app_migrations_dir.exists():
            show_migrations(engine, str(app_migrations_dir.parent))
        else:
            print(f"No migrations directory found for app '{app_label}'")
    else:
        # Show status for all apps
        show_migrations(engine, migrations_dir)


def rollback_migration(app_label: str, migration_name: str) -> bool:
    """
    Rollback a specific migration.
    
    Args:
        app_label: The app label
        migration_name: Name of the migration to rollback
        
    Returns:
        True if rollback was successful
    """
    try:
        # Load the specific migration
        migrations_dir = Path.cwd() / app_label / "migrations"
        loader = MigrationLoader(str(migrations_dir))
        
        migration = loader.load_migration(app_label, migration_name)
        
        # Check if migration is applied
        applied_migrations = get_applied_migrations()
        is_applied = any(
            m['app_label'] == app_label and m['name'] == migration_name
            for m in applied_migrations
        )
        
        if not is_applied:
            logger.warning(f"Migration '{migration_name}' is not applied")
            return False
        
        # Unapply the migration
        engine = get_engine()
        migration.unapply(engine)
        
        # Remove from applied migrations
        from fastjango.db.migrations import MigrationRecorder
        recorder = MigrationRecorder(engine)
        recorder.record_unapplied(app_label, migration_name)
        
        logger.info(f"Rolled back migration: {migration_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error rolling back migration: {e}")
        raise CommandError(f"Failed to rollback migration: {e}")


def migrate(app_label: str = None, fake: bool = False, show_status: bool = False, 
           rollback: str = None) -> int:
    """
    Main migrate function.
    
    Args:
        app_label: Optional app label to migrate
        fake: Whether to fake migrations
        show_status: Whether to show migration status
        rollback: Migration name to rollback
        
    Returns:
        Number of migrations applied
    """
    if show_status:
        show_migration_status(app_label)
        return 0
    
    if rollback:
        if not app_label:
            raise CommandError("App label is required for rollback")
        success = rollback_migration(app_label, rollback)
        return 1 if success else 0
    
    if app_label:
        # Migrate specific app
        return migrate_app(app_label, fake)
    else:
        # Migrate all apps
        return migrate_all_apps(fake)


def main():
    """Main function for migrate command."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply database migrations")
    parser.add_argument("app_label", nargs="?", help="App label (optional)")
    parser.add_argument("--fake", action="store_true", help="Mark migrations as applied without running them")
    parser.add_argument("--show", action="store_true", help="Show migration status")
    parser.add_argument("--rollback", help="Rollback specific migration")
    
    args = parser.parse_args()
    
    try:
        applied_count = migrate(
            app_label=args.app_label,
            fake=args.fake,
            show_status=args.show,
            rollback=args.rollback
        )
        
        if not args.show:
            print(f"Applied {applied_count} migrations")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
