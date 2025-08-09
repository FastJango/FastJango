"""
Command execution for FastJango management commands.
"""

import os
import sys
import importlib
from typing import List, Optional

from fastjango.core.logging import Logger, setup_logging

# Setup logger
logger = Logger("fastjango.core.management")


def execute_from_command_line(argv: Optional[List[str]] = None) -> None:
    """
    Execute a command from the command line.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
    """
    # Setup logging
    setup_logging()
    
    # Get command line arguments
    if argv is None:
        argv = sys.argv
    
    # Parse command
    if len(argv) > 1:
        command = argv[1]
    else:
        # No command provided, show help
        command = "help"
    
    # Execute command
    try:
        if command == "help":
            show_help()
        elif command == "runserver":
            run_server(argv[2:])
        elif command == "startapp":
            start_app(argv[2:])
        elif command == "shell":
            run_shell()
        elif command == "migrate":
            run_migrate(argv[2:])
        elif command == "makemigrations":
            make_migrations(argv[2:])
        else:
            # Try to find a custom command
            try:
                run_custom_command(command, argv[2:])
            except ImportError:
                logger.error(f"Unknown command: {command}")
                show_help()
                sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {e}", exc_info=True)
        sys.exit(1)


def show_help() -> None:
    """Show help for available commands."""
    print("Available commands:")
    print("  runserver - Run the development server")
    print("  startapp - Create a new app")
    print("  shell - Run a Python shell")
    print("  migrate - Apply database migrations")
    print("  makemigrations - Create new migrations")
    print("  help - Show this help message")


def run_server(args: List[str]) -> None:
    """
    Run the development server.
    
    Args:
        args: Command line arguments
    """
    from fastjango.cli.commands.runserver import run_server as run_dev_server
    
    # Parse arguments
    host = "127.0.0.1"
    port = 8000
    reload = True
    
    # Parse host and port from args
    for arg in args:
        if arg.startswith("--host="):
            host = arg.split("=")[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=")[1])
        elif arg == "--noreload":
            reload = False
    
    # Run server
    run_dev_server(host, port, reload)


def start_app(args: List[str]) -> None:
    """
    Create a new app.
    
    Args:
        args: Command line arguments
    """
    from pathlib import Path
    from fastjango.cli.commands.startapp import create_app
    
    if not args:
        logger.error("App name is required")
        print("Usage: manage.py startapp <app_name>")
        sys.exit(1)
    
    app_name = args[0]
    target_dir = Path(os.getcwd())
    
    create_app(app_name, target_dir)


def run_shell(args: List[str] = None) -> None:
    """Run a Python shell with the FastJango environment."""
    if args is None:
        args = []
    
    try:
        from fastjango.cli.commands.shell import shell_command
        
        # Parse arguments
        plain = False
        command = None
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "--plain":
                plain = True
            elif arg == "--command" or arg == "-c":
                if i + 1 < len(args):
                    command = args[i + 1]
                    i += 1
            i += 1
        
        # Run shell
        shell_command(plain=plain, command=command)
    except Exception as e:
        logger.error(f"Error running shell: {e}")
        sys.exit(1)


def run_migrate(args: List[str]) -> None:
    """
    Apply database migrations.
    
    Args:
        args: Command line arguments
    """
    from fastjango.cli.commands.migrate import migrate
    
    # Parse arguments
    app_label = None
    fake = False
    show = False
    rollback = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--fake":
            fake = True
        elif arg == "--show":
            show = True
        elif arg == "--rollback":
            if i + 1 < len(args):
                rollback = args[i + 1]
                i += 1
        elif not arg.startswith("--"):
            app_label = arg
        i += 1
    
    # Run migration
    applied_count = migrate(app_label=app_label, fake=fake, show_status=show, rollback=rollback)
    print(f"Applied {applied_count} migrations")


def make_migrations(args: List[str]) -> None:
    """
    Create database migration files.
    
    Args:
        args: Command line arguments
    """
    from fastjango.cli.commands.makemigrations import make_migrations
    
    # Parse arguments
    app_label = None
    migration_name = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--name" or arg == "-n":
            if i + 1 < len(args):
                migration_name = args[i + 1]
                i += 1
        elif not arg.startswith("--"):
            app_label = arg
        i += 1
    
    if not app_label:
        print("Error: App label is required")
        return
    
    # Create migration
    migration_file = make_migrations(app_label, migration_name)
    if migration_file:
        print(f"Created migration: {migration_file}")
    else:
        print("No changes detected")





def run_custom_command(command: str, args: List[str]) -> None:
    """
    Run a custom command from an app.
    
    Args:
        command: The command name
        args: Command line arguments
        
    Raises:
        ImportError: If the command module could not be found
    """
    # Get settings module
    settings_module = os.environ.get("FASTJANGO_SETTINGS_MODULE")
    if not settings_module:
        raise ImportError("Settings module not found")
    
    # Import settings
    settings = importlib.import_module(settings_module)
    
    # Look for command in installed apps
    installed_apps = getattr(settings, "INSTALLED_APPS", [])
    
    for app in installed_apps:
        try:
            # Try to import the command module
            command_module = f"{app}.management.commands.{command}"
            module = importlib.import_module(command_module)
            
            # Execute command
            if hasattr(module, "Command"):
                cmd = module.Command()
                cmd.execute(*args)
                return
        except ImportError:
            # Command not found in this app, continue to next app
            continue
    
    # If we get here, command was not found
    raise ImportError(f"Command '{command}' not found in any installed app") 