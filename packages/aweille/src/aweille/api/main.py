"""Local Uvicorn entry point with configured persistent SQLite storage."""

import os
import sqlite3
from pathlib import Path

from aweille.adapters import SQLiteRunStorage
from aweille.adapters.upgrade_database import validate_database
from aweille.core import StorageFailure

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
    try:
        with sqlite3.connect(path.as_uri() + "?mode=rw", uri=True) as connection:
            validate_database(connection, version=2)
    except (sqlite3.Error, StorageFailure) as error:
        raise ValueError(
            "Database is incompatible; run aweille-upgrade-db <path> if version 1."
        ) from error
    return path


app = create_app(storage=SQLiteRunStorage(_database_path()))
