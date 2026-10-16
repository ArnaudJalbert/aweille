import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

import pytest
from aweille.adapters import SQLiteRunStorage
from aweille.adapters.create_database import create_database
from aweille.adapters.upgrade_database import upgrade_database
from aweille.core import StorageFailure, create_run, read_run


def version_one(path: Path, run_input: dict[str, Any]) -> None:
    import json
    from datetime import time

    from aweille.core import PlannedRun

    run = PlannedRun(
        id=run_input["id"],
        planned_date=run_input["planned_date"],
        planned_start_time=time(7, 30),
        run_type=run_input["run_type"],
        sections=tuple(run_input["sections"]),
        user_note=run_input["user_note"].strip() or None,
        trainer_note=run_input["trainer_note"].strip() or None,
    )
    data = run.to_dict()
    with sqlite3.connect(path) as connection:
        connection.executescript("""CREATE TABLE runs (
            id TEXT NOT NULL PRIMARY KEY, planned_date TEXT NOT NULL,
            planned_start_time TEXT, run_type TEXT NOT NULL,
            sections TEXT NOT NULL, user_note TEXT, trainer_note TEXT);
            CREATE INDEX runs_planned_date ON runs(planned_date);
            PRAGMA application_id = 0x41574549;
            PRAGMA user_version = 1;""")
        connection.execute(
            "INSERT INTO runs VALUES (:id,:planned_date,:planned_start_time,"
            ":run_type,:sections,:user_note,:trainer_note)",
            {**data, "sections": json.dumps(data["sections"])},
        )


def test_explicit_upgrade_preserves_v1_data_and_is_idempotent(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    version_one(path, run_input)
    with pytest.raises(StorageFailure):
        read_run(SQLiteRunStorage(path), id=run_input["id"])
    upgrade_database(path)
    saved = read_run(SQLiteRunStorage(path), id=run_input["id"])
    assert saved.revision == 1
    assert saved.planned_start_time is not None
    assert saved.planned_start_time.isoformat(timespec="minutes") == "07:30"
    assert saved.sections == tuple(run_input["sections"])
    before = path.read_bytes()
    upgrade_database(path)
    assert path.read_bytes() == before
    retry_input: dict[str, Any] = {
        **run_input,
        "planned_start_time": saved.planned_start_time,
    }
    assert create_run(SQLiteRunStorage(path), **retry_input) == (saved, False)


def test_invalid_database_is_never_migrated(tmp_path: Path) -> None:
    path = tmp_path / "foreign.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 1")
    before = path.read_bytes()
    with pytest.raises(StorageFailure):
        upgrade_database(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "reserved_id", ["not-a-uuid", "54D97D4D-FADB-4D50-926E-AF1BB26C711A"]
)
def test_upgrade_rejects_malformed_v2_reserved_id_unchanged(
    tmp_path: Path, reserved_id: str
) -> None:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO deleted_run_ids (id) VALUES (?)", (reserved_id,)
        )
    before = path.read_bytes()

    with pytest.raises(StorageFailure):
        upgrade_database(path)

    assert path.read_bytes() == before


def test_upgrade_rejects_v2_id_both_live_and_reserved_unchanged(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    version_one(path, run_input)
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            "INSERT INTO deleted_run_ids (id) VALUES (?)", (str(run_input["id"]),)
        )
    before = path.read_bytes()

    with pytest.raises(StorageFailure):
        upgrade_database(path)

    assert path.read_bytes() == before


def test_installed_upgrade_command_preserves_original_on_failure(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    version_one(path, run_input)
    executable = shutil.which("aweille-upgrade-db")
    assert executable is not None
    result = subprocess.run(
        [executable, str(path)], cwd=tmp_path, capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
    missing = subprocess.run(
        [executable, str(tmp_path / "missing")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert missing.returncode != 0
    assert str(tmp_path) not in missing.stderr
