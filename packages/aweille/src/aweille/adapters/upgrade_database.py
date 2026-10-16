"""Explicit, transactional upgrade of recognized Aweille SQLite files."""

import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from aweille.core import PlannedRun, StorageFailure, StorageUnavailable, ValidationError

_COLUMNS = [
    ("id", "TEXT", 1, 1),
    ("planned_date", "TEXT", 1, 0),
    ("planned_start_time", "TEXT", 0, 0),
    ("run_type", "TEXT", 1, 0),
    ("sections", "TEXT", 1, 0),
    ("user_note", "TEXT", 0, 0),
    ("trainer_note", "TEXT", 0, 0),
]


def validate_database(
    connection: sqlite3.Connection, *, version: int, check_data: bool = True
) -> None:
    """Reject unrecognized schema or invalid persisted runs without modifying them."""
    if (
        connection.execute("PRAGMA application_id").fetchone()[0] != 0x41574549
        or connection.execute("PRAGMA user_version").fetchone()[0] != version
    ):
        raise StorageFailure(
            "Database is incompatible; run aweille-upgrade-db if required."
        )
    names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }
    if names != ({"runs", "deleted_run_ids"} if version == 2 else {"runs"}):
        raise StorageFailure("Aweille database schema is incompatible.")
    if version == 2:
        reserved = [
            (row[1], row[2].upper(), row[3], row[5])
            for row in connection.execute("PRAGMA table_info(deleted_run_ids)")
        ]
        if reserved != [("id", "TEXT", 1, 1)]:
            raise StorageFailure("Aweille database schema is incompatible.")
    columns = [
        (row[1], row[2].upper(), row[3], row[5])
        for row in connection.execute("PRAGMA table_info(runs)")
    ]
    expected = _COLUMNS + ([("revision", "TEXT", 1, 0)] if version == 2 else [])
    if columns != expected:
        raise StorageFailure("Aweille database schema is incompatible.")
    indexes = list(connection.execute("PRAGMA index_list(runs)"))
    if not any(
        row[1] == "runs_planned_date"
        and [
            col[2] for col in connection.execute("PRAGMA index_info(runs_planned_date)")
        ]
        == ["planned_date"]
        for row in indexes
    ):
        raise StorageFailure("Aweille database schema is incompatible.")
    if not check_data:
        return
    try:
        for row in connection.execute("SELECT * FROM runs"):
            data = dict(
                zip(
                    (
                        column[0]
                        for column in connection.execute(
                            "SELECT * FROM runs LIMIT 0"
                        ).description
                    ),
                    row,
                    strict=True,
                )
            )
            data["sections"] = json.loads(data["sections"])
            if version == 1:
                data["revision"] = "1"
            PlannedRun.from_dict(data)
    except (ValueError, TypeError, ValidationError, UnicodeError, RecursionError):
        raise StorageFailure("Saved run data is invalid.") from None


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
