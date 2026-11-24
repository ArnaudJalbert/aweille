"""Validate the Aweille SQLite schema and persisted data."""

import sqlite3
from uuid import UUID

from aweille.application import StorageFailure

from .planned_course_row import decode_planned_course_row

SCHEMA_VERSION = 3
_INCOMPATIBLE = (
    "Aweille database schema is incompatible; "
    "create a new database with aweille-init-db."
)
_COLUMNS = [
    ("id", "TEXT", 1, 1),
    ("planned_date", "TEXT", 1, 0),
    ("planned_start_time", "TEXT", 0, 0),
    ("course_type", "TEXT", 1, 0),
    ("sections", "TEXT", 1, 0),
    ("user_note", "TEXT", 0, 0),
    ("trainer_note", "TEXT", 0, 0),
    ("revision", "TEXT", 1, 0),
]


def validate_database(
    connection: sqlite3.Connection, *, check_data: bool = True
) -> None:
    """Reject incompatible schemas and invalid data without modifying storage.

    Args:
        connection: Open connection to the database being checked.
        check_data: Also validate saved planned courses and reserved IDs when true.

    Raises:
        StorageFailure: The schema is not version 3, including version 1 and 2
            files from before planned courses, or saved data is invalid.
        sqlite3.Error: SQLite cannot read the schema or saved data. Callers
            translate driver errors for their operation.
    """
    _validate_identity(connection)
    _validate_tables(connection)
    _validate_date_index(connection)
    if not check_data:
        return
    try:
        _validate_reserved_ids(connection)
        _validate_saved_planned_courses(connection)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise StorageFailure("Saved planned course data is invalid.") from None


def _validate_identity(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA application_id").fetchone()[0] != 0x41574549:
        raise StorageFailure(_INCOMPATIBLE)
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if version in (1, 2):
        raise StorageFailure(
            f"Database uses schema version {version} from before planned courses; "
            "create a new database with aweille-init-db."
        )
    if version != SCHEMA_VERSION:
        raise StorageFailure(_INCOMPATIBLE)


def _validate_tables(connection: sqlite3.Connection) -> None:
    names = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
    }
    if names != {"planned_courses", "deleted_planned_course_ids"}:
        raise StorageFailure(_INCOMPATIBLE)
    if _read_table_columns(connection, "deleted_planned_course_ids") != [
        ("id", "TEXT", 1, 1)
    ]:
        raise StorageFailure(_INCOMPATIBLE)
    if _read_table_columns(connection, "planned_courses") != _COLUMNS:
        raise StorageFailure(_INCOMPATIBLE)


def _read_table_columns(
    connection: sqlite3.Connection, table: str
) -> list[tuple[str, str, int, int]]:
    return [
        (row[1], row[2].upper(), row[3], row[5])
        for row in connection.execute(f"PRAGMA table_info({table})")
    ]


def _validate_date_index(connection: sqlite3.Connection) -> None:
    indexes = list(connection.execute("PRAGMA index_list(planned_courses)"))
    if not any(
        row[1] == "planned_courses_planned_date"
        and [
            col[2]
            for col in connection.execute(
                "PRAGMA index_info(planned_courses_planned_date)"
            )
        ]
        == ["planned_date"]
        for row in indexes
    ):
        raise StorageFailure(_INCOMPATIBLE)


def _validate_reserved_ids(connection: sqlite3.Connection) -> None:
    for (reserved_id,) in connection.execute(
        "SELECT id FROM deleted_planned_course_ids"
    ):
        if not isinstance(reserved_id, str) or str(UUID(reserved_id)) != reserved_id:
            raise ValueError("Invalid reserved planned course ID")
    if connection.execute(
        "SELECT 1 FROM planned_courses JOIN deleted_planned_course_ids USING (id) "
        "LIMIT 1"
    ).fetchone():
        raise ValueError("Planned course ID is both live and reserved")


def _validate_saved_planned_courses(connection: sqlite3.Connection) -> None:
    cursor = connection.execute("SELECT * FROM planned_courses")
    columns = [column[0] for column in cursor.description]
    for row in cursor:
        decode_planned_course_row(dict(zip(columns, row, strict=True)))
