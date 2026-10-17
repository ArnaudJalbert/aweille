"""Validate recognized Aweille SQLite schemas and persisted data."""

import json
import sqlite3
from uuid import UUID

from aweille.core import PlannedRun, StorageFailure, ValidationError

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
    """Reject incompatible schemas and invalid data without modifying storage.

    Args:
        connection: Open connection to the database being checked.
        version: Expected schema version, either 1 or 2.
        check_data: Also validate saved runs and reserved IDs when true.

    Raises:
        StorageFailure: The schema is incompatible or saved data is invalid.
        sqlite3.Error: SQLite cannot read the schema or saved data. Callers
            translate driver errors for their operation.
    """
    _validate_identity(connection, version=version)
    _validate_tables(connection, version=version)
    _validate_date_index(connection)
    if not check_data:
        return
    try:
        if version == 2:
            _validate_reserved_ids(connection)
        _validate_saved_runs(connection, version=version)
    except (ValueError, TypeError, ValidationError, UnicodeError, RecursionError):
        raise StorageFailure("Saved run data is invalid.") from None


def _validate_identity(connection: sqlite3.Connection, *, version: int) -> None:
    if (
        connection.execute("PRAGMA application_id").fetchone()[0] != 0x41574549
        or connection.execute("PRAGMA user_version").fetchone()[0] != version
    ):
        raise StorageFailure(
            "Database is incompatible; run aweille-upgrade-db if required."
        )


def _validate_tables(connection: sqlite3.Connection, *, version: int) -> None:
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


def _validate_date_index(connection: sqlite3.Connection) -> None:
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


def _validate_reserved_ids(connection: sqlite3.Connection) -> None:
    for (reserved_id,) in connection.execute("SELECT id FROM deleted_run_ids"):
        if not isinstance(reserved_id, str) or str(UUID(reserved_id)) != reserved_id:
            raise ValueError("Invalid reserved run ID")
    if connection.execute(
        "SELECT 1 FROM runs JOIN deleted_run_ids USING (id) LIMIT 1"
    ).fetchone():
        raise ValueError("Run ID is both live and reserved")


def _validate_saved_runs(connection: sqlite3.Connection, *, version: int) -> None:
    cursor = connection.execute("SELECT * FROM runs")
    columns = [column[0] for column in cursor.description]
    for row in cursor:
        data = dict(zip(columns, row, strict=True))
        data["sections"] = json.loads(data["sections"])
        if version == 1:
            data["revision"] = "1"
        PlannedRun.from_dict(data)
