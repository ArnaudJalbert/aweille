import json
import sqlite3
from datetime import date, time
from pathlib import Path
from uuid import UUID

from aweille.application import (
    PlannedCourseReader,
    PlannedCourseReadModel,
    SectionReadModel,
    StorageFailure,
)
from aweille.domain import CourseType

from ..planned_course_row import decode_integer, decode_positive_integer
from ..sqlite_connection import open_connection


class SQLitePlannedCourseReader(PlannedCourseReader):
    """Read planned courses from an existing SQLite database as read models."""

    def __init__(self, path: str | Path, *, timeout: float = 1.0) -> None:
        """Remember connection settings without opening or initializing storage.

        Args:
            path: Existing database file with the schema created by the setup script.
            timeout: Maximum SQLite lock wait in seconds.
        """
        self._path = Path(path).absolute()
        self._timeout = timeout

    def read(self, id: UUID) -> PlannedCourseReadModel | None:
        """Read one planned course from the committed database state.

        Args:
            id: UUID of the saved planned course.

        Returns:
            The saved planned course, or None if the UUID is absent.

        Raises:
            StorageUnavailable: Contention or unavailability prevents reading.
            StorageFailure: Saved data cannot be decoded or the read fails.
        """
        with open_connection(self._path, self._timeout) as connection:
            row = connection.execute(
                "SELECT * FROM planned_courses WHERE id = ?", (str(id),)
            ).fetchone()
        return self._read_model(row) if row is not None else None

    def read_range(self, start: date, end: date) -> list[PlannedCourseReadModel]:
        """Read planned courses in a half-open local-date range.

        Args:
            start: First included Montreal date.
            end: First excluded Montreal date.

        Returns:
            All matching planned courses from one committed snapshot, in unspecified
            order.

        Raises:
            StorageUnavailable: Contention or unavailability prevents reading.
            StorageFailure: Saved data cannot be decoded or the read fails. No
                partial results are returned.
        """
        with open_connection(self._path, self._timeout) as connection:
            rows = connection.execute(
                "SELECT * FROM planned_courses "
                "WHERE planned_date >= ? AND planned_date < ?",
                (start.isoformat(), end.isoformat()),
            ).fetchall()
        return [self._read_model(row) for row in rows]

    @classmethod
    def _read_model(cls, row: sqlite3.Row) -> PlannedCourseReadModel:
        try:
            return cls._map_row(row)
        except (
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            RecursionError,
        ):
            raise StorageFailure("Saved planned course data is invalid.") from None

    @classmethod
    def _map_row(cls, row: sqlite3.Row) -> PlannedCourseReadModel:
        return PlannedCourseReadModel(
            id=UUID(row["id"]),
            planned_date=date.fromisoformat(row["planned_date"]),
            planned_start_time=time.fromisoformat(row["planned_start_time"])
            if row["planned_start_time"] is not None
            else None,
            course_type=CourseType(row["course_type"]).value,
            sections=tuple(
                cls._section(section) for section in json.loads(row["sections"])
            ),
            user_note=row["user_note"],
            trainer_note=row["trainer_note"],
            revision=decode_positive_integer(row["revision"]),
        )

    @staticmethod
    def _section(section: dict[str, str]) -> SectionReadModel:
        return SectionReadModel(
            metres=decode_integer(section["distance_m"]),
            seconds_per_km=decode_integer(section["target_pace_seconds_per_km"]),
        )
