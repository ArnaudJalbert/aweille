import json
import re
import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from datetime import date, time
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from aweille.core import (
    Distance,
    Pace,
    PlannedRun,
    RunType,
    Section,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
)

_APPLICATION_ID = 0x41574549
_SCHEMA_VERSION = 1
_SCHEMA = {
    "runs": (
        "CREATE TABLE runs ("
        "id TEXT NOT NULL PRIMARY KEY, planned_date TEXT NOT NULL, "
        "planned_start_time TEXT, run_type TEXT NOT NULL, "
        "sections TEXT NOT NULL, user_note TEXT, trainer_note TEXT)"
    ),
    "runs_planned_date": "CREATE INDEX runs_planned_date ON runs(planned_date)",
}


class SQLiteRunStorage:
    """Persist planned runs in a local SQLite file."""

    def __init__(self, path: str | Path, *, timeout: float = 1.0) -> None:
        """Open storage and initialize its schema.

        Args:
            path: Database file, with an existing parent directory.
            timeout: Maximum SQLite lock wait in seconds.

        Raises:
            StorageUnavailable: Contention or unavailability prevents opening.
            StorageFailure: Storage is incompatible or initialization fails.
        """
        self._path = Path(path).absolute()
        self._timeout = timeout
        with self._connection(create=True) as connection, connection:
            _initialize_schema(connection)

    def save(self, run: PlannedRun) -> tuple[PlannedRun, bool]:
        """Atomically insert a missing ID or return its unchanged saved run.

        Args:
            run: Validated, normalized planned run.

        Returns:
            The stored run and insertion outcome. True means committed; False
            returns the existing run for core to compare, without overwriting.

        Raises:
            StorageUnavailable: Contention or unavailability prevents saving.
            StorageFailure: Saved data is invalid or the write fails. Retry the
                same ID to resolve an uncertain commit outcome.
        """
        with self._connection() as connection, connection:
            inserted = (
                connection.execute(
                    "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?) "
                    "ON CONFLICT(id) DO NOTHING",
                    _encode_run(run),
                ).rowcount
                == 1
            )
            stored = _decode_run(
                connection.execute(
                    "SELECT * FROM runs WHERE id = ?", (str(run.id),)
                ).fetchone()
            )
        return stored, inserted

    def get(self, start: date, end: date) -> list[PlannedRun]:
        """Read runs in a half-open local-date range.

        Args:
            start: First included Montreal date.
            end: First excluded Montreal date.

        Returns:
            All matching runs from one committed snapshot, in unspecified order.

        Raises:
            StorageUnavailable: Contention or unavailability prevents reading.
            StorageFailure: Saved data is invalid or the read fails. No partial
                results are returned.
        """
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM runs WHERE planned_date >= ? AND planned_date < ?",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [_decode_run(row) for row in rows]

    @contextmanager
    def _connection(self, *, create: bool = False) -> Generator[sqlite3.Connection]:
        uri = self._path.as_uri() + ("?mode=rwc" if create else "?mode=rw")
        try:
            with closing(
                sqlite3.connect(uri, timeout=self._timeout, uri=True)
            ) as connection:
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


def _initialize_schema(connection: sqlite3.Connection) -> None:
    connection.execute("BEGIN IMMEDIATE")
    application_id = connection.execute("PRAGMA application_id").fetchone()[0]
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    schema = dict(
        connection.execute(
            "SELECT name, sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*'"
        ).fetchall()
    )
    if not schema and application_id == 0 and version == 0:
        for statement in _SCHEMA.values():
            connection.execute(statement)
        connection.execute(f"PRAGMA application_id = {_APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
    elif (
        application_id != _APPLICATION_ID
        or version != _SCHEMA_VERSION
        or schema != _SCHEMA
    ):
        raise StorageFailure("SQLite storage schema is incompatible.")


def _encode_run(run: PlannedRun) -> tuple[str | None, ...]:
    sections = [
        {
            "distance_m": str(Decimal(section.distance.metres)),
            "target_pace_seconds_per_km": str(
                Decimal(section.target_pace.seconds_per_km)
            ),
        }
        for section in run.sections
    ]
    return (
        str(run.id),
        run.planned_date.isoformat(),
        run.planned_start_time.isoformat(timespec="minutes")
        if run.planned_start_time is not None
        else None,
        run.run_type.value,
        json.dumps(sections),
        run.user_note,
        run.trainer_note,
    )


def _decode_run(row: tuple) -> PlannedRun:
    try:
        sections = json.loads(row[4])
        if not isinstance(sections, list):
            raise ValueError
        run = PlannedRun(
            id=UUID(row[0]),
            planned_date=date.fromisoformat(row[1]),
            planned_start_time=time.fromisoformat(row[2])
            if row[2] is not None
            else None,
            run_type=RunType(row[3]),
            sections=tuple(_decode_section(value) for value in sections),
            user_note=row[5],
            trainer_note=row[6],
        )
        encoded = _encode_run(run)
        # Reject noncanonical fields rather than silently normalizing saved data.
        if encoded[:4] + encoded[5:] != row[:4] + row[5:]:
            raise ValueError
        return run
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        RecursionError,
        ValidationError,
    ):
        raise StorageFailure("Saved run data is invalid.") from None


def _decode_section(value: object) -> Section:
    if not isinstance(value, dict) or value.keys() != {
        "distance_m",
        "target_pace_seconds_per_km",
    }:
        raise ValueError
    return Section(
        Distance(_decode_integer(value["distance_m"])),
        Pace(_decode_integer(value["target_pace_seconds_per_km"])),
    )


def _decode_integer(value: object) -> int:
    if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError
    # Decimal conversion is exact and avoids Python's int/str digit threshold.
    return int(Decimal(value))
