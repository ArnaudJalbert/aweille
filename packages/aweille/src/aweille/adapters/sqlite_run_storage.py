import json
import sqlite3
from collections.abc import Generator
from contextlib import closing, contextmanager
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from aweille.core import (
    PlannedRun,
    RunConflict,
    RunNotFound,
    RunRevisionConflict,
    StorageFailure,
    StorageUnavailable,
)


class SQLiteRunStorage:
    """Read and write planned runs in an existing SQLite database."""

    def __init__(self, path: str | Path, *, timeout: float = 1.0) -> None:
        """Remember connection settings without opening or initializing storage.

        Args:
            path: Existing database file with the schema created by the setup script.
            timeout: Maximum SQLite lock wait in seconds.
        """
        self._path = Path(path).absolute()
        self._timeout = timeout

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
            connection.execute("BEGIN IMMEDIATE")
            if (
                connection.execute(
                    "SELECT 1 FROM deleted_run_ids WHERE id = ?", (str(run.id),)
                ).fetchone()
                is not None
            ):
                raise RunConflict("The ID is reserved for a deleted planned run.")
            inserted = (
                connection.execute(
                    "INSERT INTO runs (id, planned_date, planned_start_time, run_type, "
                    "sections, user_note, trainer_note, revision) VALUES ("
                    ":id, :planned_date, :planned_start_time, :run_type, "
                    ":sections, :user_note, :trainer_note, :revision) "
                    "ON CONFLICT(id) DO NOTHING",
                    self._encode_run(replace(run, revision=1)),
                ).rowcount
                == 1
            )
            stored = self._decode_run(
                connection.execute(
                    "SELECT * FROM runs WHERE id = ?", (str(run.id),)
                ).fetchone()
            )
        return stored, inserted

    def load(self, id: UUID) -> PlannedRun | None:
        """Read one committed run without changing the database."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM runs WHERE id = ?", (str(id),)
            ).fetchone()
            return self._decode_run(row) if row is not None else None

    def replace(self, run: PlannedRun, *, expected_revision: int) -> PlannedRun:
        """Atomically check the current revision and replace changed fields."""
        with self._connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM runs WHERE id = ?", (str(run.id),)
            ).fetchone()
            if row is None:
                raise RunNotFound
            current = self._decode_run(row)
            if current.revision != expected_revision:
                raise RunRevisionConflict
            if current.to_dict() | {"revision": "1"} == run.to_dict() | {
                "revision": "1"
            }:
                return current
            updated = replace(run, revision=current.revision + 1)
            connection.execute(
                "UPDATE runs SET planned_date=:planned_date, "
                "planned_start_time=:planned_start_time, "
                "run_type=:run_type, sections=:sections, user_note=:user_note, "
                "trainer_note=:trainer_note, revision=:revision WHERE id=:id",
                self._encode_run(updated),
            )
        return updated

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
        return [self._decode_run(row) for row in rows]

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection]:
        try:
            with closing(
                sqlite3.connect(
                    self._path.as_uri() + "?mode=rw", timeout=self._timeout, uri=True
                )
            ) as connection:
                connection.row_factory = sqlite3.Row
                from .upgrade_database import validate_database

                validate_database(connection, version=2, check_data=False)
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

    @staticmethod
    def _encode_run(run: PlannedRun) -> dict[str, Any]:
        data = run.to_dict()
        data["sections"] = json.dumps(data["sections"])
        return data

    @staticmethod
    def _decode_run(row: sqlite3.Row) -> PlannedRun:
        try:
            data = dict(row)
            data["sections"] = json.loads(data["sections"])
            return PlannedRun.from_dict(data)
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            RecursionError,
        ):
            raise StorageFailure("Saved run data is invalid.") from None
