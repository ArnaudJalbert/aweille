"""Explicit, transactional upgrade of recognized Aweille SQLite files."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path

from aweille.core import StorageFailure, StorageUnavailable

from .validate_database import validate_database


def upgrade_database(path: str | Path) -> None:
    """Upgrade valid v1 storage atomically; accept valid v2 unchanged.

    Args:
        path: Existing prepared Aweille SQLite file.

    Raises:
        StorageFailure: Missing, unrelated, invalid, or unsupported database.
        StorageUnavailable: File access or database lock temporarily fails.
    """
    path = Path(path).absolute()
    if not path.is_file():
        raise StorageFailure("Database file does not exist.")
    try:
        with closing(
            sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=1)
        ) as connection:
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            validate_database(connection, version=version if version in (1, 2) else -1)
            if version == 2:
                connection.rollback()
                return
            connection.execute(
                "ALTER TABLE runs ADD COLUMN revision TEXT NOT NULL DEFAULT '1'"
            )
            connection.execute(
                "CREATE TABLE deleted_run_ids (id TEXT NOT NULL PRIMARY KEY)"
            )
            connection.execute("PRAGMA user_version = 2")
            validate_database(connection, version=2)
            connection.commit()
    except sqlite3.Error as error:
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
        raise StorageFailure("Database upgrade failed.") from None


def main() -> None:
    """Run the explicit upgrade command and report failures without diagnostics."""
    parser = argparse.ArgumentParser(
        description="Upgrade an existing Aweille database."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        upgrade_database(args.path)
    except (StorageFailure, StorageUnavailable, OSError):
        parser.exit(1, "Database upgrade failed; no automatic repair was attempted.\n")


if __name__ == "__main__":
    main()
