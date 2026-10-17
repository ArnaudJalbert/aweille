import multiprocessing
import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from aweille.adapters import SQLiteRunStorage
from aweille.adapters.create_database import create_database
from aweille.core import (
    PlannedRun,
    RunConflict,
    RunRevisionConflict,
    StorageFailure,
    create_run,
    read_run,
    update_run,
)


def test_atomic_edit_persists_and_rejects_stale_writer(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    writer = SQLiteRunStorage(path)
    saved, _ = create_run(writer, **run_input)
    revised = update_run(writer, id=saved.id, expected_revision=1, trainer_note="new")
    assert revised.revision == 2
    reader = SQLiteRunStorage(path)
    assert read_run(reader, id=saved.id) == revised
    with pytest.raises(RunRevisionConflict):
        update_run(reader, id=saved.id, expected_revision=1, user_note="lost")
    assert read_run(writer, id=saved.id) == revised


def test_new_database_schema_is_version_two(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        assert connection.execute("PRAGMA table_info(runs)").fetchall()[-1][1:4] == (
            "revision",
            "TEXT",
            1,
        )


def test_incompatible_schema_fails_safely(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    sqlite3.connect(path).close()
    with pytest.raises(StorageFailure):
        create_run(SQLiteRunStorage(path), **run_input)


def test_save_rejects_reserved_identity_without_resurrection(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO deleted_run_ids (id) VALUES (?)", (str(run_input["id"]),)
        )
    storage = SQLiteRunStorage(path)
    with pytest.raises(RunConflict):
        storage.save(
            PlannedRun(
                id=run_input["id"],
                planned_date=run_input["planned_date"],
                planned_start_time=None,
                run_type=run_input["run_type"],
                sections=tuple(run_input["sections"]),
                user_note=None,
                trainer_note=None,
            )
        )
    assert storage.load(run_input["id"]) is None


def test_save_assigns_initial_revision_instead_of_candidate_revision(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    candidate = replace(
        PlannedRun(
            id=run_input["id"],
            planned_date=run_input["planned_date"],
            planned_start_time=None,
            run_type=run_input["run_type"],
            sections=tuple(run_input["sections"]),
            user_note=None,
            trainer_note=None,
        ),
        revision=7,
    )
    storage = SQLiteRunStorage(path)
    saved, inserted = storage.save(candidate)
    assert inserted is True
    assert saved.revision == 1
    assert SQLiteRunStorage(path).load(candidate.id) == saved


def _competing_edit(path: str, id: str, note: str, start: Any, outcome: Any) -> None:
    start.wait()
    try:
        update_run(
            SQLiteRunStorage(path), id=UUID(id), expected_revision=1, user_note=note
        )
        outcome.put("saved")
    except RunRevisionConflict:
        outcome.put("stale")


def test_independent_processes_allow_only_one_edit_at_a_revision(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    original, _ = create_run(SQLiteRunStorage(path), **run_input)
    context = multiprocessing.get_context("fork")
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
    saved = read_run(SQLiteRunStorage(path), id=original.id)
    assert saved.revision == 2
    assert saved.user_note in ("first", "second")
