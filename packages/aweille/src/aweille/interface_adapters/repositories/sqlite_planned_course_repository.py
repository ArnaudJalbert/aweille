import sqlite3
from contextlib import AbstractContextManager
from dataclasses import replace
from pathlib import Path
from uuid import UUID

from aweille.application import (
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseRepository,
    PlannedCourseRevisionConflict,
    StorageFailure,
)
from aweille.domain import PlannedCourse

from ..planned_course_row import decode_planned_course_row, encode_planned_course_row
from ..sqlite_connection import open_connection


class SQLitePlannedCourseRepository(PlannedCourseRepository):
    """Load and write planned courses in an existing SQLite database."""

    def __init__(self, path: str | Path, *, timeout: float = 1.0) -> None:
        """Remember connection settings without opening or initializing storage.

        Args:
            path: Existing database file with the schema created by the setup script.
            timeout: Maximum SQLite lock wait in seconds.
        """
        self._path = Path(path).absolute()
        self._timeout = timeout

    def save(self, planned_course: PlannedCourse) -> tuple[PlannedCourse, bool]:
        """Atomically insert a missing ID or return its unchanged saved planned course.

        Args:
            planned_course: Validated, normalized planned course.

        Returns:
            The stored planned course and insertion outcome. True means committed;
            False returns the existing planned course for the create use case to
            compare, without overwriting.

        Raises:
            StorageUnavailable: Contention or unavailability prevents saving.
            StorageFailure: Saved data is invalid or the write fails. Retry the
                same ID to resolve an uncertain commit outcome.
        """
        with self._connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            if (
                connection.execute(
                    "SELECT 1 FROM deleted_planned_course_ids WHERE id = ?",
                    (str(planned_course.id),),
                ).fetchone()
                is not None
            ):
                raise PlannedCourseConflict(
                    "The ID is reserved for a deleted planned course."
                )
            inserted = (
                connection.execute(
                    "INSERT INTO planned_courses (id, planned_date, "
                    "planned_start_time, course_type, sections, user_note, "
                    "trainer_note, revision) VALUES ("
                    ":id, :planned_date, :planned_start_time, :course_type, "
                    ":sections, :user_note, :trainer_note, :revision) "
                    "ON CONFLICT(id) DO NOTHING",
                    encode_planned_course_row(replace(planned_course, revision=1)),
                ).rowcount
                == 1
            )
            stored = self._decode_planned_course(
                connection.execute(
                    "SELECT * FROM planned_courses WHERE id = ?",
                    (str(planned_course.id),),
                ).fetchone()
            )
        return stored, inserted

    def load(self, id: UUID) -> PlannedCourse | None:
        """Load one planned course from the committed database state.

        Args:
            id: UUID of the saved planned course.

        Returns:
            The validated saved planned course, or None if the UUID is absent.

        Raises:
            StorageUnavailable: Contention or unavailability prevents reading.
            StorageFailure: Saved data is invalid or the read fails.
        """
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM planned_courses WHERE id = ?", (str(id),)
            ).fetchone()
            return self._decode_planned_course(row) if row is not None else None

    def replace(
        self, planned_course: PlannedCourse, *, expected_revision: int
    ) -> PlannedCourse:
        """Replace a planned course atomically when its saved revision matches.

        Args:
            planned_course: Validated candidate with the saved planned course's UUID.
            expected_revision: Revision the caller observed before editing.

        Returns:
            The committed planned course with its incremented revision, or the unchanged
            saved planned course and revision when the candidate is a no-op.

        Raises:
            PlannedCourseNotFound: The UUID is absent.
            PlannedCourseRevisionConflict: The saved revision differs from the expected
                one.
            StorageUnavailable: Contention or unavailability prevents replacing.
            StorageFailure: Saved data is invalid or the write fails; a failed
                response does not establish whether a commit occurred.
        """
        with self._connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            current = self._load_matching_revision(
                connection, planned_course.id, expected_revision=expected_revision
            )
            if replace(planned_course, revision=current.revision) == current:
                return current
            updated = replace(planned_course, revision=current.revision + 1)
            connection.execute(
                "UPDATE planned_courses SET planned_date=:planned_date, "
                "planned_start_time=:planned_start_time, "
                "course_type=:course_type, sections=:sections, user_note=:user_note, "
                "trainer_note=:trainer_note, revision=:revision WHERE id=:id",
                encode_planned_course_row(updated),
            )
        return updated

    def delete(self, id: UUID, *, expected_revision: int) -> None:
        """Remove a matching planned course and reserve only its UUID atomically.

        Args:
            id: UUID of the saved planned course.
            expected_revision: Revision observed by the caller.

        Raises:
            PlannedCourseNotFound: The UUID is absent or already deleted.
            PlannedCourseRevisionConflict: The live revision differs from the expected
                one.
            StorageUnavailable: Contention or unavailability prevents deletion.
            StorageFailure: Saved data is invalid or deletion fails; a failed
                response does not establish whether a commit occurred.
        """
        with self._connection() as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self._load_matching_revision(
                connection, id, expected_revision=expected_revision
            )
            connection.execute("DELETE FROM planned_courses WHERE id = ?", (str(id),))
            connection.execute(
                "INSERT INTO deleted_planned_course_ids (id) VALUES (?)", (str(id),)
            )

    def _load_matching_revision(
        self, connection: sqlite3.Connection, id: UUID, *, expected_revision: int
    ) -> PlannedCourse:
        row = connection.execute(
            "SELECT * FROM planned_courses WHERE id = ?", (str(id),)
        ).fetchone()
        if row is None:
            raise PlannedCourseNotFound
        current = self._decode_planned_course(row)
        if current.revision != expected_revision:
            raise PlannedCourseRevisionConflict
        return current

    def _connection(self) -> AbstractContextManager[sqlite3.Connection]:
        return open_connection(self._path, self._timeout)

    @staticmethod
    def _decode_planned_course(row: sqlite3.Row) -> PlannedCourse:
        try:
            return decode_planned_course_row(dict(row))
        except ValueError:
            raise StorageFailure("Saved planned course data is invalid.") from None
