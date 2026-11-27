import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date, time
from pathlib import Path
from uuid import UUID

import pytest
from aweille.application import (
    PlannedCourseReadModel,
    SectionReadModel,
    StorageFailure,
    StorageUnavailable,
)
from aweille.domain import Distance, Pace, PlannedCourse, Section
from aweille.interface_adapters import (
    SQLitePlannedCourseReader,
    SQLitePlannedCourseRepository,
)


def test_read_returns_saved_values_with_exact_targets(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    """A saved planned course reads back as plain values, including huge targets."""
    saved = replace(
        planned_course,
        planned_start_time=time(6, 30),
        sections=(Section(Distance(10**5003), Pace(10**5000)),),
    )
    SQLitePlannedCourseRepository(database_path).save(saved)

    assert SQLitePlannedCourseReader(database_path).read(saved.id) == (
        PlannedCourseReadModel(
            id=saved.id,
            planned_date=date(2026, 10, 14),
            planned_start_time=time(6, 30),
            course_type="interval",
            sections=(SectionReadModel(metres=10**5003, seconds_per_km=10**5000),),
            user_note="Keep the first section easy.",
            trainer_note="Finish relaxed.",
            revision=1,
        )
    )


def test_read_returns_none_for_absent_or_deleted_planned_course(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    """Absent and deleted IDs both read as None."""
    repository = SQLitePlannedCourseRepository(database_path)
    repository.save(planned_course)
    repository.delete(planned_course.id, expected_revision=1)
    reader = SQLitePlannedCourseReader(database_path)

    assert reader.read(planned_course.id) is None
    assert reader.read(UUID(int=1)) is None
    assert reader.read_range(date(2026, 1, 1), date(2027, 1, 1)) == []


def test_range_reads_are_half_open_and_see_committed_data_only(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    """The range includes start, excludes end, and ignores uncommitted writes."""
    repository = SQLitePlannedCourseRepository(database_path)
    days = [
        date(2026, 10, 11),
        date(2026, 10, 12),
        date(2026, 10, 18),
        date(2026, 10, 19),
    ]
    for index, day in enumerate(days):
        repository.save(replace(planned_course, id=UUID(int=index), planned_date=day))
    reader = SQLitePlannedCourseReader(database_path)
    start, end = date(2026, 10, 12), date(2026, 10, 19)

    with closing(sqlite3.connect(database_path)) as writer:
        writer.execute(
            "UPDATE planned_courses SET user_note = ? WHERE id = ?",
            ("Changed", str(UUID(int=1))),
        )
        assert _notes_by_id(reader, start, end) == {
            UUID(int=1): "Keep the first section easy.",
            UUID(int=2): "Keep the first section easy.",
        }
        writer.commit()
        assert _notes_by_id(reader, start, end) == {
            UUID(int=1): "Changed",
            UUID(int=2): "Keep the first section easy.",
        }
    assert reader.read_range(date(2027, 1, 1), date(2027, 1, 2)) == []


@pytest.mark.parametrize(
    "changes",
    [
        {"sections": "PRIVATE invalid JSON"},
        {"course_type": "PRIVATE"},
        {"revision": "PRIVATE"},
        {"revision": "1.5"},
        {"sections": '[{"distance_m": "12.5", "target_pace_seconds_per_km": "390"}]'},
    ],
)
def test_malformed_saved_planned_courses_fail_reads_safely(
    database_path: Path, planned_course: PlannedCourse, changes: dict[str, str]
) -> None:
    """Undecodable saved data fails the whole read without exposing it."""
    SQLitePlannedCourseRepository(database_path).save(planned_course)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        assignments = ", ".join(f"{field} = ?" for field in changes)
        connection.execute(
            f"UPDATE planned_courses SET {assignments}", tuple(changes.values())
        )
    reader = SQLitePlannedCourseReader(database_path)

    for read in (
        lambda: reader.read(planned_course.id),
        lambda: reader.read_range(date(2026, 1, 1), date(2027, 1, 1)),
    ):
        with pytest.raises(StorageFailure) as failure:
            read()
        assert "PRIVATE" not in str(failure.value)
        assert str(database_path) not in str(failure.value)


def test_lock_contention_is_retryable(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    """A locked database reports a retryable failure, then reads normally."""
    SQLitePlannedCourseRepository(database_path).save(planned_course)
    reader = SQLitePlannedCourseReader(database_path, timeout=0.02)

    with closing(sqlite3.connect(database_path)) as blocker, blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(StorageUnavailable) as failure:
            reader.read_range(date(2026, 10, 14), date(2026, 10, 15))
        assert str(database_path) not in str(failure.value)

    assert reader.read(planned_course.id) is not None


def _notes_by_id(
    reader: SQLitePlannedCourseReader, start: date, end: date
) -> dict[UUID, str | None]:
    return {
        planned_course.id: planned_course.user_note
        for planned_course in reader.read_range(start, end)
    }
