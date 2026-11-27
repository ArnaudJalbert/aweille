"""Local Uvicorn entry point with configured persistent SQLite storage."""

import os
import sqlite3
from pathlib import Path

from aweille.application import StorageFailure
from aweille.interface_adapters import (
    SQLitePlannedCourseReader,
    SQLitePlannedCourseRepository,
)
from aweille.interface_adapters.sqlite.validate_database import validate_database

from .create_app import create_app


def _database_path() -> Path:
    configured = os.environ.get(
        "AWEILLE_DB_PATH", "~/.local/share/aweille/aweille.sqlite3"
    )
    if not configured.strip() or configured.strip() == ":memory:":
        raise ValueError("AWEILLE_DB_PATH must name a persistent database file.")
    try:
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise ValueError(
                "AWEILLE_DB_PATH must name an existing database file. Prepare its "
                "parent directory and run aweille-init-db <path> before startup."
            )
    except (OSError, RuntimeError) as error:
        raise ValueError(
            "AWEILLE_DB_PATH could not be resolved to a database file."
        ) from error
    _validate_database_file(path)
    return path


def _validate_database_file(path: Path) -> None:
    try:
        with sqlite3.connect(path.as_uri() + "?mode=rw", uri=True) as connection:
            validate_database(connection)
    except StorageFailure as error:
        raise ValueError(str(error)) from error
    except sqlite3.Error as error:
        raise ValueError(
            "Database is incompatible; create a new database with aweille-init-db."
        ) from error


_path = _database_path()
app = create_app(
    repository=SQLitePlannedCourseRepository(_path),
    reader=SQLitePlannedCourseReader(_path),
)
