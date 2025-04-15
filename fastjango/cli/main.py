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

from fastjango.cli.commands import startproject, startapp, runserver
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
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: Optional[bool] = typer.Option(None, "--version", help="Show the version and exit"),
):
    """
    FastJango command-line utility for administrative tasks.
    """
    if version:
        console.print(f"FastJango v{__version__}")
        raise typer.Exit()
        
    # Configure logging based on verbosity
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)
    if verbose:
        logger.debug("Verbose logging enabled")


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
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
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