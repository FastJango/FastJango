"""
FastJango CLI - Command-line interface for FastJango

This module provides a command-line interface similar to Django's django-admin.
It allows creating projects and apps with proper structure.
"""

import os
import sys
import logging
import typer
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler
from typing import Optional

from fastjango.core.logging import setup_logging
from fastjango import __version__

# Setup rich console
console = Console()

# Setup application
app = typer.Typer(
    name="fastjango-admin",
    help="FastJango command-line utility for administrative tasks",
    add_completion=False,
)

# Setup logging
logger = logging.getLogger("fastjango.cli")


@app.callback()
def callback():
    """FastJango command-line utility for administrative tasks."""
    # Minimal callback to avoid global parameter issues
    pass


@app.command()
def version():
    """Show the FastJango version and exit."""
    console.print(f"FastJango v{__version__}")


@app.command()
def startproject(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    directory: str = typer.Option(
        None, "--directory", "-d", help="Optional directory to create the project in"
    ),
):
    """
    Creates a new FastJango project with the given name.
    """
    try:
        # Lazy import to avoid loading heavy modules at CLI import time
        from fastjango.cli.commands.startproject import create_project

        target_dir = directory or os.getcwd()
        logger.info(f"Creating project '{project_name}' in {target_dir}")
        
        create_project(project_name, Path(target_dir))
        
        logger.info(f"Project '{project_name}' created successfully")
        logger.info(f"Run 'cd {project_name}' to navigate to your project")
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def startapp(
    app_name: str = typer.Argument(..., help="Name of the app to create"),
):
    """
    Creates a new app in the current FastJango project.
    """
    try:
        from fastjango.cli.commands.startapp import create_app
        
        logger.info(f"Creating app '{app_name}'")
        
        create_app(app_name, Path(os.getcwd()))
        
        logger.info(f"App '{app_name}' created successfully")
    except Exception as e:
        logger.error(f"Failed to create app: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def runserver(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(True, help="Enable auto-reload on code changes"),
):
    """
    Runs the FastJango development server.
    """
    try:
        from fastjango.cli.commands.runserver import run_server
        
        logger.info(f"Starting development server at {host}:{port}")
        
        run_server(host, port, reload)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def makemigrations(
    app_label: str = typer.Argument(..., help="App label"),
    name: str = typer.Option(None, "--name", "-n", help="Migration name"),
):
    """
    Create database migration files.
    """
    try:
        from fastjango.cli.commands.makemigrations import make_migrations
        
        logger.info(f"Creating migrations for app '{app_label}'")
        
        migration_file = make_migrations(app_label, name)
        
        if migration_file:
            logger.info(f"Created migration: {migration_file}")
        else:
            logger.info("No changes detected")
    except Exception as e:
        logger.error(f"Failed to create migrations: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def migrate(
    app_label: str = typer.Argument(None, help="App label (optional)"),
    fake: bool = typer.Option(False, "--fake", help="Mark migrations as applied without running them"),
    show: bool = typer.Option(False, "--show", help="Show migration status"),
    rollback: str = typer.Option(None, "--rollback", help="Rollback specific migration"),
):
    """
    Apply database migrations.
    """
    try:
        from fastjango.cli.commands.migrate import migrate as run_migrate
        
        if show:
            run_migrate(app_label=app_label, show_status=True)
        elif rollback:
            if not app_label:
                logger.error("App label is required for rollback")
                raise typer.Exit(code=1)
            success = run_migrate(app_label=app_label, rollback=rollback)
            if success:
                logger.info(f"Rolled back migration: {rollback}")
            else:
                logger.warning(f"Migration '{rollback}' is not applied")
        else:
            applied_count = run_migrate(app_label=app_label, fake=fake)
            logger.info(f"Applied {applied_count} migrations")
    except Exception as e:
        logger.error(f"Failed to apply migrations: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def shell(
    plain: bool = typer.Option(False, "--plain", help="Run a plain Python shell"),
    command: str = typer.Option(None, "--command", "-c", help="Execute a command and exit"),
):
    """
    Start an interactive Python shell with FastJango environment.
    """
    try:
        from fastjango.cli.commands.shell import shell_command
        
        logger.info("Starting FastJango interactive shell")
        
        shell_command(plain=plain, command=command)
    except Exception as e:
        logger.error(f"Failed to start shell: {str(e)}")
        raise typer.Exit(code=1)


def cli():
    """
    Entry point for the command-line interface.
    """
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli() 