"""Check an Aweille database file before the application starts using it."""

import sqlite3
from contextlib import closing
from pathlib import Path

from aweille.application import StorageFailure

from .validate_database import validate_database


def validate_database_file(path: Path) -> None:
    """Reject a database file whose schema or saved data Aweille cannot use.

    Args:
        path: Absolute path to an existing database file. It is opened
            read-write without creating it, and never modified.

    Raises:
        StorageFailure: The schema is incompatible, the file is not an SQLite
            database, or saved data is invalid. Messages name aweille-init-db.
    """
    try:
        with closing(
            sqlite3.connect(path.as_uri() + "?mode=rw", uri=True)
        ) as connection:
            validate_database(connection)
    except sqlite3.Error as error:
        raise StorageFailure(
            "Database is incompatible; create a new database with aweille-init-db."
        ) from error
