import multiprocessing
import sqlite3
from contextlib import closing
from dataclasses import replace
from datetime import date, time
from functools import partial
from multiprocessing.connection import Connection
from multiprocessing.synchronize import Barrier
from pathlib import Path
from types import TracebackType
from typing import Literal
from uuid import UUID

import pytest
from aweille.adapters import SQLitePlannedCourseStorage
from aweille.adapters.create_database import create_database
from aweille.core import (
    CourseType,
    Distance,
    Pace,
    PlannedCourse,
    Section,
    StorageFailure,
    StorageUnavailable,
)


def test_saved_planned_course_survives_reopening_with_exact_sections_and_notes(
    database_path: Path,
) -> None:
    planned_course = _planned_course()
    path = database_path
    storage = SQLitePlannedCourseStorage(path)

    assert storage.save(planned_course) == (planned_course, True)
    assert SQLitePlannedCourseStorage(path).get(
        date(2026, 10, 14), date(2026, 10, 15)
    ) == [planned_course]


def test_existing_id_returns_original_without_overwriting_changed_data(
    database_path: Path,
) -> None:
    planned_course = _planned_course()
    storage = SQLitePlannedCourseStorage(database_path)
    storage.save(planned_course)

    assert storage.save(planned_course) == (planned_course, False)
    assert storage.save(replace(planned_course, user_note="Changed")) == (
        planned_course,
        False,
    )
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [planned_course]


def test_huge_integer_targets_and_absent_optional_fields_round_trip(
    database_path: Path,
) -> None:
    planned_course = replace(
        _planned_course(),
        sections=(Section(Distance(10**5003), Pace(10**5000)),),
        planned_start_time=None,
        user_note=None,
        trainer_note=None,
    )
    path = database_path
    assert SQLitePlannedCourseStorage(path).save(planned_course) == (
        planned_course,
        True,
    )
    assert SQLitePlannedCourseStorage(path).get(
        date(2026, 10, 14), date(2026, 10, 15)
    ) == [planned_course]


@pytest.mark.parametrize("invalid_file", [False, True])
def test_unreadable_storage_fails_when_used_without_changing_the_file(
    tmp_path: Path, invalid_file: bool
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    if invalid_file:
        path.write_bytes(b"not a SQLite database; PRIVATE")
    else:
        with closing(sqlite3.connect(path)) as connection, connection:
            connection.execute("CREATE TABLE private_data (value TEXT)")
            connection.execute("INSERT INTO private_data VALUES ('PRIVATE')")
    before = path.read_bytes()
    storage = SQLitePlannedCourseStorage(path)

    with pytest.raises(StorageFailure) as failure:
        storage.get(date(2026, 10, 14), date(2026, 10, 15))

    assert path.read_bytes() == before
    assert str(path) not in str(failure.value)
    assert "PRIVATE" not in str(failure.value)


@pytest.mark.parametrize(
    "changes",
    [
        {"sections": "PRIVATE invalid JSON"},
        {"course_type": "PRIVATE"},
        {"planned_date": "2026-03-08", "planned_start_time": "02:30"},
    ],
)
def test_malformed_saved_planned_courses_fail_reads_and_existing_id_retrieval(
    database_path: Path, changes: dict[str, str]
) -> None:
    path = database_path
    planned_course = _planned_course()
    storage = SQLitePlannedCourseStorage(path)
    storage.save(planned_course)
    storage.save(replace(planned_course, id=UUID(int=1)))
    with closing(sqlite3.connect(path)) as connection, connection:
        assignments = ", ".join(f"{field} = ?" for field in changes)
        connection.execute(
            f"UPDATE planned_courses SET {assignments} WHERE id = ?",
            (*changes.values(), str(planned_course.id)),
        )

    reopened = SQLitePlannedCourseStorage(path)
    assert reopened.get(date(2027, 1, 1), date(2027, 1, 2)) == []
    for operation in (
        lambda: reopened.get(date(2026, 1, 1), date(2027, 1, 1)),
        lambda: reopened.save(planned_course),
    ):
        with pytest.raises(StorageFailure) as failure:
            operation()
        assert "PRIVATE" not in str(failure.value)
        assert str(path) not in str(failure.value)


@pytest.mark.parametrize("operation", ["save", "get"])
def test_lock_contention_is_retryable_and_leaves_saved_data_unchanged(
    database_path: Path, operation: str
) -> None:
    path = database_path
    planned_course = _planned_course()
    other = replace(planned_course, id=UUID(int=1))
    storage = SQLitePlannedCourseStorage(path, timeout=0.02)
    storage.save(planned_course)
    with closing(sqlite3.connect(path)) as blocker, blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(StorageUnavailable) as failure:
            if operation == "save":
                storage.save(other)
            else:
                storage.get(date(2026, 10, 14), date(2026, 10, 15))
        assert str(path) not in str(failure.value)

    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [planned_course]
    assert storage.save(other) == (other, True)


def test_failed_write_rolls_back_and_storage_can_be_used_again(
    database_path: Path,
) -> None:
    path = database_path
    storage = SQLitePlannedCourseStorage(path)
    planned_course = _planned_course()
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_run AFTER INSERT ON planned_courses "
            "BEGIN SELECT RAISE(ABORT, 'PRIVATE write failure'); END"
        )

    with pytest.raises(StorageFailure) as failure:
        storage.save(planned_course)
    assert "PRIVATE" not in str(failure.value)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == []

    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DROP TRIGGER reject_run")
    assert SQLitePlannedCourseStorage(path).save(planned_course) == (
        planned_course,
        True,
    )


def test_range_reads_are_half_open_and_see_committed_data_only(
    database_path: Path,
) -> None:
    path = database_path
    storage = SQLitePlannedCourseStorage(path)
    planned_courses = [
        replace(_planned_course(), id=UUID(int=index), planned_date=day)
        for index, day in enumerate(
            [
                date(2026, 10, 11),
                date(2026, 10, 12),
                date(2026, 10, 18),
                date(2026, 10, 19),
            ]
        )
    ]
    for planned_course in planned_courses:
        storage.save(planned_course)
    start, end = date(2026, 10, 12), date(2026, 10, 19)
    expected = planned_courses[1:3]
    with closing(sqlite3.connect(path)) as writer:
        writer.execute(
            "UPDATE planned_courses SET user_note = ? WHERE id = ?",
            ("Changed", str(expected[0].id)),
        )
        assert set(storage.get(start, end)) == set(expected)
        writer.commit()
        assert set(storage.get(start, end)) == {
            replace(expected[0], user_note="Changed"),
            expected[1],
        }
    assert storage.get(date(2027, 1, 1), date(2027, 1, 2)) == []


@pytest.mark.parametrize("committed_before_failure", [False, True])
def test_commit_failure_preserves_atomic_data_and_can_be_resolved_by_retry(
    database_path: Path, monkeypatch: pytest.MonkeyPatch, committed_before_failure: bool
) -> None:
    path = database_path
    storage = SQLitePlannedCourseStorage(path)
    planned_course = _planned_course()

    class CommitFailureConnection(sqlite3.Connection):
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> Literal[False]:
            if exc_type is None:
                if committed_before_failure:
                    super().__exit__(exc_type, exc, traceback)
                raise sqlite3.OperationalError("PRIVATE commit failure")
            return super().__exit__(exc_type, exc, traceback)

    with monkeypatch.context() as patch:
        patch.setattr(
            sqlite3,
            "connect",
            partial(sqlite3.connect, factory=CommitFailureConnection),
        )
        with pytest.raises(StorageFailure) as failure:
            storage.save(planned_course)
        assert "PRIVATE" not in str(failure.value)

    assert SQLitePlannedCourseStorage(path).get(
        date(2026, 10, 14), date(2026, 10, 15)
    ) == ([planned_course] if committed_before_failure else [])
    assert storage.save(planned_course) == (
        planned_course,
        not committed_before_failure,
    )


def test_independent_processes_insert_one_id_without_overwriting(
    database_path: Path,
) -> None:
    path = database_path
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    planned_courses = (
        _planned_course(),
        replace(_planned_course(), user_note="Different proposal"),
    )
    channels = [context.Pipe(duplex=False) for _ in planned_courses]
    workers = [
        context.Process(
            target=_save_from_process, args=(path, planned_course, barrier, sender)
        )
        for planned_course, (_, sender) in zip(planned_courses, channels, strict=True)
    ]
    try:
        for worker, (_, sender) in zip(workers, channels, strict=True):
            worker.start()
            sender.close()
        outcomes = []
        for receiver, _ in channels:
            assert receiver.poll(5), "SQLite worker did not finish"
            outcomes.append(receiver.recv())
        for worker in workers:
            worker.join(timeout=5)
            assert worker.exitcode == 0
        assert sorted(inserted for _, inserted in outcomes) == [False, True]
        winner = next(
            planned_course for planned_course, inserted in outcomes if inserted
        )
        assert winner in planned_courses
        assert all(stored == winner for stored, _ in outcomes)
        assert SQLitePlannedCourseStorage(path).get(
            date(2026, 10, 14), date(2026, 10, 15)
        ) == [winner]
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)
            worker.close()
        for receiver, sender in channels:
            receiver.close()
            sender.close()


def test_construction_does_not_open_create_or_initialize_storage(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing" / "planned-courses.sqlite"
    storage = SQLitePlannedCourseStorage(path)
    assert not path.parent.exists()
    with pytest.raises(StorageUnavailable) as failure:
        storage.get(date(2026, 10, 14), date(2026, 10, 15))
    assert not path.parent.exists()
    assert str(path) not in str(failure.value)

    path.parent.mkdir()
    create_database(path)
    assert storage.save(_planned_course()) == (_planned_course(), True)


def test_relative_path_keeps_the_original_file_after_working_directory_changes(
    database_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(database_path.parent)
    storage = SQLitePlannedCourseStorage("planned-courses.sqlite")
    other_directory = database_path.parent / "elsewhere"
    other_directory.mkdir()
    monkeypatch.chdir(other_directory)

    assert storage.save(_planned_course()) == (_planned_course(), True)
    assert SQLitePlannedCourseStorage(database_path).get(
        date(2026, 10, 14), date(2026, 10, 15)
    ) == [_planned_course()]


@pytest.mark.parametrize("operation", ["save", "get"])
def test_missing_database_is_not_recreated_by_an_operation(
    database_path: Path, operation: str
) -> None:
    path = database_path
    moved = database_path.with_name("moved.sqlite")
    storage = SQLitePlannedCourseStorage(path)
    storage.save(_planned_course())
    path.rename(moved)

    with pytest.raises(StorageUnavailable):
        if operation == "save":
            storage.save(_planned_course())
        else:
            storage.get(date(2026, 10, 14), date(2026, 10, 15))
    assert not path.exists()

    moved.rename(path)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [_planned_course()]


def test_text_encoding_failure_is_safe_and_leaves_storage_unchanged(
    database_path: Path,
) -> None:
    storage = SQLitePlannedCourseStorage(database_path)
    original = _planned_course()
    storage.save(original)
    unsupported = replace(
        original, id=UUID(int=1), user_note="before\ud800PRIVATEafter"
    )

    with pytest.raises(StorageFailure) as failure:
        storage.save(unsupported)

    assert "PRIVATE" not in str(failure.value)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [original]
    assert storage.save(replace(unsupported, user_note="Supported text"))[1] is True


def _save_from_process(
    path: Path, planned_course: PlannedCourse, barrier: Barrier, sender: Connection
) -> None:
    with sender:
        barrier.wait(timeout=5)
        sender.send(SQLitePlannedCourseStorage(path).save(planned_course))


def _planned_course() -> PlannedCourse:
    section = Section(Distance(1000), Pace(390))
    return PlannedCourse(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        planned_start_time=time(6, 30),
        course_type=CourseType.INTERVAL,
        sections=(section, Section(Distance(1200), Pace(345)), section),
        user_note="Keep it easy.\nThen finish strong; 'quoted'.",
        trainer_note="Finish relaxed.",
    )
