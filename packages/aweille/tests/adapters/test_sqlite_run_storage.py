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
from aweille.adapters import SQLiteRunStorage
from aweille.core import (
    Distance,
    Pace,
    PlannedRun,
    RunType,
    Section,
    StorageFailure,
    StorageUnavailable,
)


def test_saved_run_survives_reopening_with_exact_sections_and_notes(
    tmp_path: Path,
) -> None:
    run = _run()
    path = tmp_path / "runs.sqlite"
    storage = SQLiteRunStorage(path)

    assert storage.save(run) == (run, True)
    assert SQLiteRunStorage(path).get(date(2026, 10, 14), date(2026, 10, 15)) == [run]


def test_existing_id_returns_original_without_overwriting_changed_data(
    tmp_path: Path,
) -> None:
    run = _run()
    storage = SQLiteRunStorage(tmp_path / "runs.sqlite")
    storage.save(run)

    assert storage.save(run) == (run, False)
    assert storage.save(replace(run, user_note="Changed")) == (run, False)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [run]


def test_huge_integer_targets_and_absent_optional_fields_round_trip(
    tmp_path: Path,
) -> None:
    run = replace(
        _run(),
        sections=(Section(Distance(10**5003), Pace(10**5000)),),
        planned_start_time=None,
        user_note=None,
        trainer_note=None,
    )
    path = tmp_path / "runs.sqlite"
    assert SQLiteRunStorage(path).save(run) == (run, True)
    assert SQLiteRunStorage(path).get(date(2026, 10, 14), date(2026, 10, 15)) == [run]


@pytest.mark.parametrize(
    "incompatibility",
    ["unrelated_schema", "future_version", "missing_index", "invalid_file"],
)
def test_incompatible_storage_is_rejected_without_changing_the_file(
    tmp_path: Path, incompatibility: str
) -> None:
    path = tmp_path / "runs.sqlite"
    if incompatibility == "invalid_file":
        path.write_bytes(b"not a SQLite database; PRIVATE")
    else:
        if incompatibility != "unrelated_schema":
            SQLiteRunStorage(path).save(_run())
        with closing(sqlite3.connect(path)) as connection, connection:
            if incompatibility == "unrelated_schema":
                connection.execute("CREATE TABLE sqlitex_private_data (value TEXT)")
                connection.execute(
                    "INSERT INTO sqlitex_private_data VALUES ('PRIVATE')"
                )
            elif incompatibility == "future_version":
                connection.execute("PRAGMA user_version = 99")
            else:
                connection.execute("DROP INDEX runs_planned_date")
    before = path.read_bytes()

    with pytest.raises(StorageFailure) as failure:
        SQLiteRunStorage(path)

    assert path.read_bytes() == before
    assert str(path) not in str(failure.value)
    assert "PRIVATE" not in str(failure.value)


@pytest.mark.parametrize(
    "changes",
    [
        {"sections": "PRIVATE invalid JSON"},
        {"sections": '{"distance_m":"1000","target_pace_seconds_per_km":"390"}'},
        {
            "sections": '[{"distance_m":"1000",'
            '"target_pace_seconds_per_km":"390","PRIVATE":true}]'
        },
        {"sections": '[{"distance_m":1000,"target_pace_seconds_per_km":"390"}]'},
        {"sections": '[{"distance_m":"1e3","target_pace_seconds_per_km":"390"}]'},
        {"sections": '[{"distance_m":"01000","target_pace_seconds_per_km":"390"}]'},
        {"sections": "[]"},
        {"run_type": "PRIVATE"},
        {"user_note": "  PRIVATE  "},
        {"planned_date": "2026-03-08", "planned_start_time": "02:30"},
    ],
)
def test_malformed_saved_runs_fail_reads_and_existing_id_retrieval(
    tmp_path: Path, changes: dict[str, str]
) -> None:
    path = tmp_path / "runs.sqlite"
    run = _run()
    storage = SQLiteRunStorage(path)
    storage.save(run)
    storage.save(replace(run, id=UUID(int=1)))
    with closing(sqlite3.connect(path)) as connection, connection:
        assignments = ", ".join(f"{field} = ?" for field in changes)
        connection.execute(
            f"UPDATE runs SET {assignments} WHERE id = ?",
            (*changes.values(), str(run.id)),
        )

    reopened = SQLiteRunStorage(path)
    assert reopened.get(date(2027, 1, 1), date(2027, 1, 2)) == []
    for operation in (
        lambda: reopened.get(date(2026, 1, 1), date(2027, 1, 1)),
        lambda: reopened.save(run),
    ):
        with pytest.raises(StorageFailure) as failure:
            operation()
        assert "PRIVATE" not in str(failure.value)
        assert str(path) not in str(failure.value)


@pytest.mark.parametrize("operation", ["open", "save", "get"])
def test_lock_contention_is_retryable_and_leaves_saved_data_unchanged(
    tmp_path: Path, operation: str
) -> None:
    path = tmp_path / "runs.sqlite"
    run = _run()
    other = replace(run, id=UUID(int=1))
    storage = SQLiteRunStorage(path, timeout=0.02)
    storage.save(run)
    with closing(sqlite3.connect(path)) as blocker, blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        with pytest.raises(StorageUnavailable) as failure:
            if operation == "open":
                SQLiteRunStorage(path, timeout=0.02)
            elif operation == "save":
                storage.save(other)
            else:
                storage.get(date(2026, 10, 14), date(2026, 10, 15))
        assert str(path) not in str(failure.value)

    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [run]
    assert storage.save(other) == (other, True)


def test_failed_write_rolls_back_and_storage_can_be_used_again(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite"
    storage = SQLiteRunStorage(path)
    run = _run()
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_run AFTER INSERT ON runs "
            "BEGIN SELECT RAISE(ABORT, 'PRIVATE write failure'); END"
        )

    with pytest.raises(StorageFailure) as failure:
        storage.save(run)
    assert "PRIVATE" not in str(failure.value)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == []

    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("DROP TRIGGER reject_run")
    assert SQLiteRunStorage(path).save(run) == (run, True)


def test_range_reads_are_half_open_and_see_committed_data_only(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite"
    storage = SQLiteRunStorage(path)
    runs = [
        replace(_run(), id=UUID(int=index), planned_date=day)
        for index, day in enumerate(
            [
                date(2026, 10, 11),
                date(2026, 10, 12),
                date(2026, 10, 18),
                date(2026, 10, 19),
            ]
        )
    ]
    for run in runs:
        storage.save(run)
    start, end = date(2026, 10, 12), date(2026, 10, 19)
    expected = runs[1:3]
    with closing(sqlite3.connect(path)) as writer:
        writer.execute(
            "UPDATE runs SET user_note = ? WHERE id = ?",
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
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, committed_before_failure: bool
) -> None:
    path = tmp_path / "runs.sqlite"
    storage = SQLiteRunStorage(path)
    run = _run()

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
            storage.save(run)
        assert "PRIVATE" not in str(failure.value)

    assert SQLiteRunStorage(path).get(date(2026, 10, 14), date(2026, 10, 15)) == (
        [run] if committed_before_failure else []
    )
    assert storage.save(run) == (run, not committed_before_failure)


def test_independent_processes_initialize_and_insert_one_id_without_overwriting(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runs.sqlite"
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(2)
    runs = (_run(), replace(_run(), user_note="Different proposal"))
    channels = [context.Pipe(duplex=False) for _ in runs]
    workers = [
        context.Process(target=_save_from_process, args=(path, run, barrier, sender))
        for run, (_, sender) in zip(runs, channels, strict=True)
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
        winner = next(run for run, inserted in outcomes if inserted)
        assert winner in runs
        assert all(stored == winner for stored, _ in outcomes)
        assert SQLiteRunStorage(path).get(date(2026, 10, 14), date(2026, 10, 15)) == [
            winner
        ]
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)
            worker.close()
        for receiver, sender in channels:
            receiver.close()
            sender.close()


def test_missing_parent_is_reported_as_unavailable_without_creating_directories(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing" / "runs.sqlite"
    with pytest.raises(StorageUnavailable) as failure:
        SQLiteRunStorage(path)
    assert not path.parent.exists()
    assert str(path) not in str(failure.value)

    path.parent.mkdir()
    assert SQLiteRunStorage(path).save(_run()) == (_run(), True)


def test_relative_path_keeps_the_original_file_after_working_directory_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    storage = SQLiteRunStorage("runs.sqlite")
    other_directory = tmp_path / "elsewhere"
    other_directory.mkdir()
    monkeypatch.chdir(other_directory)

    assert storage.save(_run()) == (_run(), True)
    assert SQLiteRunStorage(tmp_path / "runs.sqlite").get(
        date(2026, 10, 14), date(2026, 10, 15)
    ) == [_run()]


@pytest.mark.parametrize("operation", ["save", "get"])
def test_missing_database_is_not_recreated_by_an_operation(
    tmp_path: Path, operation: str
) -> None:
    path = tmp_path / "runs.sqlite"
    moved = tmp_path / "moved.sqlite"
    storage = SQLiteRunStorage(path)
    storage.save(_run())
    path.rename(moved)

    with pytest.raises(StorageUnavailable):
        if operation == "save":
            storage.save(_run())
        else:
            storage.get(date(2026, 10, 14), date(2026, 10, 15))
    assert not path.exists()

    moved.rename(path)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [_run()]


def _save_from_process(
    path: Path, run: PlannedRun, barrier: Barrier, sender: Connection
) -> None:
    with sender:
        barrier.wait(timeout=5)
        sender.send(SQLiteRunStorage(path).save(run))


def _run() -> PlannedRun:
    section = Section(Distance(1000), Pace(390))
    return PlannedRun(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        planned_start_time=time(6, 30),
        run_type=RunType.INTERVAL,
        sections=(section, Section(Distance(1200), Pace(345)), section),
        user_note="Keep it easy.\nThen finish strong; 'quoted'.",
        trainer_note="Finish relaxed.",
    )
