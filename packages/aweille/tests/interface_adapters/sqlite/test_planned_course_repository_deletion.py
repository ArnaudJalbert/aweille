import multiprocessing
import sqlite3
from contextlib import closing
from dataclasses import replace
from functools import partial
from pathlib import Path

import pytest
from aweille.application import (
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseRevisionConflict,
    StorageFailure,
    StorageUnavailable,
)
from aweille.domain import PlannedCourse
from aweille.interface_adapters import SQLitePlannedCourseRepository


def test_atomic_deletion_persists_reservation_and_rejects_stale_or_missing(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    storage = SQLitePlannedCourseRepository(database_path)
    saved, _ = storage.save(planned_course)
    current = storage.replace(replace(saved, trainer_note="new"), expected_revision=1)
    with pytest.raises(PlannedCourseRevisionConflict):
        storage.delete(saved.id, expected_revision=1)
    assert storage.load(saved.id) == current
    assert storage.delete(saved.id, expected_revision=2) is None
    reopened = SQLitePlannedCourseRepository(database_path)
    assert reopened.load(saved.id) is None
    with pytest.raises(PlannedCourseNotFound):
        reopened.delete(saved.id, expected_revision=2)
    with pytest.raises(PlannedCourseNotFound):
        reopened.replace(current, expected_revision=2)
    with pytest.raises(PlannedCourseConflict):
        reopened.save(saved)


def test_failed_reservation_rolls_back_removal(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    storage = SQLitePlannedCourseRepository(database_path)
    saved, _ = storage.save(planned_course)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_reservation "
            "AFTER INSERT ON deleted_planned_course_ids "
            "BEGIN SELECT RAISE(ABORT, 'PRIVATE reservation failure'); END"
        )
    with pytest.raises(StorageFailure) as failure:
        storage.delete(saved.id, expected_revision=1)
    assert "PRIVATE" not in str(failure.value)
    assert storage.load(saved.id) == saved
    assert storage.save(saved) == (saved, False)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("DROP TRIGGER reject_reservation")
    storage.delete(saved.id, expected_revision=1)
    with pytest.raises(PlannedCourseConflict):
        storage.save(saved)


@pytest.mark.parametrize("committed", [False, True])
def test_uncertain_commit_requires_reading_current_state(
    database_path: Path,
    planned_course: PlannedCourse,
    monkeypatch,
    committed: bool,
) -> None:
    storage = SQLitePlannedCourseRepository(database_path)
    saved, _ = storage.save(planned_course)

    class CommitFailure(sqlite3.Connection):
        def __exit__(self, exc_type, exc, traceback):
            if exc_type is None:
                if committed:
                    super().__exit__(exc_type, exc, traceback)
                raise sqlite3.OperationalError("PRIVATE commit failure")
            return super().__exit__(exc_type, exc, traceback)

    with monkeypatch.context() as patch:
        patch.setattr(
            sqlite3, "connect", partial(sqlite3.connect, factory=CommitFailure)
        )
        with pytest.raises(StorageFailure) as failure:
            storage.delete(saved.id, expected_revision=1)
        assert "PRIVATE" not in str(failure.value)
    reopened = SQLitePlannedCourseRepository(database_path)
    assert reopened.load(saved.id) == (None if committed else saved)
    if committed:
        with pytest.raises(PlannedCourseNotFound):
            reopened.delete(saved.id, expected_revision=1)
        with pytest.raises(PlannedCourseConflict):
            reopened.save(saved)
    else:
        assert reopened.save(saved) == (saved, False)
        reopened.delete(saved.id, expected_revision=1)


def test_locked_or_corrupt_planned_course_cannot_be_deleted(
    database_path: Path, planned_course: PlannedCourse
) -> None:
    storage = SQLitePlannedCourseRepository(database_path, timeout=0.02)
    saved, _ = storage.save(planned_course)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("BEGIN EXCLUSIVE")
        with pytest.raises(StorageUnavailable):
            storage.delete(saved.id, expected_revision=1)
    assert storage.load(saved.id) == saved
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("UPDATE planned_courses SET revision='PRIVATE'")
    with pytest.raises(StorageFailure) as failure:
        storage.delete(saved.id, expected_revision=1)
    assert "PRIVATE" not in str(failure.value)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("UPDATE planned_courses SET revision='1'")
    assert storage.load(saved.id) == saved


def _competing_write(path, planned_course, action, start, outcomes):
    start.wait(timeout=5)
    storage = SQLitePlannedCourseRepository(path)
    try:
        if action == "delete":
            storage.delete(planned_course.id, expected_revision=1)
        elif action == "edit":
            storage.replace(
                replace(planned_course, user_note="new"), expected_revision=1
            )
        else:
            storage.save(planned_course)
        outcomes.put((action, "success"))
    except PlannedCourseNotFound:
        outcomes.put((action, "missing"))
    except PlannedCourseRevisionConflict:
        outcomes.put((action, "stale"))
    except PlannedCourseConflict:
        outcomes.put((action, "reserved"))


@pytest.mark.parametrize("other", ["edit", "delete", "post"])
def test_independent_process_writes_serialize_with_deletion(
    database_path: Path, planned_course: PlannedCourse, other: str
) -> None:
    storage = SQLitePlannedCourseRepository(database_path)
    planned_course, _ = storage.save(planned_course)
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    outcomes = context.Queue()
    workers = [
        context.Process(
            target=_competing_write,
            args=(database_path, planned_course, action, start, outcomes),
        )
        for action in ("delete", other)
    ]
    try:
        for worker in workers:
            worker.start()
        start.set()
        for worker in workers:
            worker.join(timeout=10)
            assert worker.exitcode == 0
        results = [outcomes.get(timeout=1) for _ in workers]
        saved = SQLitePlannedCourseRepository(database_path).load(planned_course.id)
        if other == "edit":
            assert sorted(results) in (
                [("delete", "success"), ("edit", "missing")],
                [("delete", "stale"), ("edit", "success")],
            )
            assert saved is None or (saved.revision == 2 and saved.user_note == "new")
        elif other == "delete":
            assert sorted(results) == [("delete", "missing"), ("delete", "success")]
            assert saved is None
        else:
            assert ("delete", "success") in results
            assert ("post", "success") in results or ("post", "reserved") in results
            assert saved is None
        if saved is None:
            with pytest.raises(PlannedCourseConflict):
                storage.save(planned_course)
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)
            worker.close()
        outcomes.close()
        outcomes.join_thread()
