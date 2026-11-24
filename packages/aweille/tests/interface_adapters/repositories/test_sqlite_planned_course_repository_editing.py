import multiprocessing
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from aweille.application import (
    PlannedCourseConflict,
    PlannedCourseRevisionConflict,
    StorageFailure,
    create_planned_course,
    read_planned_course,
    update_planned_course,
)
from aweille.domain import PlannedCourse
from aweille.interface_adapters import SQLitePlannedCourseRepository
from aweille.interface_adapters.create_database import create_database


def test_atomic_edit_persists_and_rejects_stale_writer(
    tmp_path: Path, planned_course_input: dict[str, Any]
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    writer = SQLitePlannedCourseRepository(path)
    saved, _ = create_planned_course(writer, **planned_course_input)
    revised = update_planned_course(
        writer, id=saved.id, expected_revision=1, trainer_note="new"
    )
    assert revised.revision == 2
    reader = SQLitePlannedCourseRepository(path)
    assert read_planned_course(reader, id=saved.id) == revised
    with pytest.raises(PlannedCourseRevisionConflict):
        update_planned_course(
            reader, id=saved.id, expected_revision=1, user_note="lost"
        )
    assert read_planned_course(writer, id=saved.id) == revised


def test_new_database_schema_is_version_three(tmp_path: Path) -> None:
    """A new database uses the planned-course schema at version 3."""
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 3
        columns = connection.execute("PRAGMA table_info(planned_courses)").fetchall()
        assert [column[1] for column in columns] == [
            "id",
            "planned_date",
            "planned_start_time",
            "course_type",
            "sections",
            "user_note",
            "trainer_note",
            "revision",
        ]


@pytest.mark.parametrize("version", [1, 2])
def test_pre_rename_database_fails_safely_without_changes(
    tmp_path: Path, planned_course_input: dict[str, Any], version: int
) -> None:
    """A version 1 or 2 file from before the rename is rejected unchanged."""
    path = tmp_path / "runs.sqlite"
    with sqlite3.connect(path) as connection:
        connection.executescript(
            "CREATE TABLE runs (id TEXT NOT NULL PRIMARY KEY, "
            "planned_date TEXT NOT NULL, planned_start_time TEXT, "
            "run_type TEXT NOT NULL, sections TEXT NOT NULL, user_note TEXT, "
            "trainer_note TEXT, revision TEXT NOT NULL);"
            "CREATE INDEX runs_planned_date ON runs(planned_date);"
            "CREATE TABLE deleted_run_ids (id TEXT NOT NULL PRIMARY KEY);"
            "PRAGMA application_id = 0x41574549;"
            f"PRAGMA user_version = {version};"
        )
    before = path.read_bytes()
    with pytest.raises(StorageFailure, match="aweille-init-db"):
        create_planned_course(
            SQLitePlannedCourseRepository(path), **planned_course_input
        )
    assert path.read_bytes() == before


def test_incompatible_schema_fails_safely(
    tmp_path: Path, planned_course_input: dict[str, Any]
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    sqlite3.connect(path).close()
    with pytest.raises(StorageFailure):
        create_planned_course(
            SQLitePlannedCourseRepository(path), **planned_course_input
        )


def test_save_rejects_reserved_identity_without_resurrection(
    tmp_path: Path, planned_course_input: dict[str, Any]
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO deleted_planned_course_ids (id) VALUES (?)",
            (str(planned_course_input["id"]),),
        )
    storage = SQLitePlannedCourseRepository(path)
    with pytest.raises(PlannedCourseConflict):
        storage.save(
            PlannedCourse(
                id=planned_course_input["id"],
                planned_date=planned_course_input["planned_date"],
                planned_start_time=None,
                course_type=planned_course_input["course_type"],
                sections=tuple(planned_course_input["sections"]),
                user_note=None,
                trainer_note=None,
            )
        )
    assert storage.load(planned_course_input["id"]) is None


def test_save_assigns_initial_revision_instead_of_candidate_revision(
    tmp_path: Path, planned_course_input: dict[str, Any]
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    candidate = replace(
        PlannedCourse(
            id=planned_course_input["id"],
            planned_date=planned_course_input["planned_date"],
            planned_start_time=None,
            course_type=planned_course_input["course_type"],
            sections=tuple(planned_course_input["sections"]),
            user_note=None,
            trainer_note=None,
        ),
        revision=7,
    )
    storage = SQLitePlannedCourseRepository(path)
    saved, inserted = storage.save(candidate)
    assert inserted is True
    assert saved.revision == 1
    assert SQLitePlannedCourseRepository(path).load(candidate.id) == saved


def _competing_edit(path: str, id: str, note: str, start: Any, outcome: Any) -> None:
    start.wait()
    try:
        update_planned_course(
            SQLitePlannedCourseRepository(path),
            id=UUID(id),
            expected_revision=1,
            user_note=note,
        )
        outcome.put("saved")
    except PlannedCourseRevisionConflict:
        outcome.put("stale")


def test_independent_processes_allow_only_one_edit_at_a_revision(
    tmp_path: Path, planned_course_input: dict[str, Any]
) -> None:
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    original, _ = create_planned_course(
        SQLitePlannedCourseRepository(path), **planned_course_input
    )
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    outcome = context.Queue()
    workers = [
        context.Process(
            target=_competing_edit,
            args=(str(path), str(original.id), note, start, outcome),
        )
        for note in ("first", "second")
    ]
    for worker in workers:
        worker.start()
    start.set()
    for worker in workers:
        worker.join(timeout=5)
        assert worker.exitcode == 0
    assert sorted([outcome.get(timeout=1) for _ in workers]) == ["saved", "stale"]
    saved = read_planned_course(SQLitePlannedCourseRepository(path), id=original.id)
    assert saved.revision == 2
    assert saved.user_note in ("first", "second")
