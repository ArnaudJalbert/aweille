"""Open checked SQLite connections and translate driver failures."""

import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from pathlib import Path

from aweille.application import StorageFailure, StorageUnavailable

from .validate_database import validate_database


@contextmanager
def open_connection(path: Path, timeout: float) -> Generator[sqlite3.Connection]:
    """Open an existing database read-write and check its schema.

    Args:
        path: Absolute path to an existing Aweille database file.
        timeout: Maximum SQLite lock wait in seconds.

    Yields:
        A connection returning sqlite3.Row rows, closed on exit.

    Raises:
        StorageUnavailable: Contention or unavailability prevents the operation.
        StorageFailure: The schema is incompatible or SQLite fails. Messages
            omit SQL, paths, and stored values.
    """
    try:
        with closing(
            sqlite3.connect(path.as_uri() + "?mode=rw", timeout=timeout, uri=True)
        ) as connection:
            connection.row_factory = sqlite3.Row
            validate_database(connection, check_data=False)
            yield connection
    except (sqlite3.Error, UnicodeError) as error:
        code = getattr(error, "sqlite_errorcode", 0) & 0xFF
        if code in {
            sqlite3.SQLITE_BUSY,
            sqlite3.SQLITE_LOCKED,
            sqlite3.SQLITE_CANTOPEN,
            sqlite3.SQLITE_IOERR,
        }:
            raise StorageUnavailable(
                "SQLite storage is temporarily unavailable."
            ) from None
        raise StorageFailure("SQLite storage failed.") from None
