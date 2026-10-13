import sqlite3
import subprocess
import sys
from datetime import date
from functools import partial
from pathlib import Path
from types import TracebackType
from typing import Any, Literal

import pytest
from aweille.adapters import SQLiteRunStorage
from aweille.adapters.create_database import create_database
from aweille.core import create_run


def test_creation_script_creates_storage_and_refuses_to_reinitialize_it(
    tmp_path: Path, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"
    command = [sys.executable, "-m", "aweille.adapters.create_database", str(path)]
    created = subprocess.run(command, capture_output=True, text=True, timeout=5)
    assert created.returncode == 0, created.stderr
    storage = SQLiteRunStorage(path)
    run, _ = create_run(storage, **run_input)
    before = path.read_bytes()

    repeated = subprocess.run(command, capture_output=True, text=True, timeout=5)

    assert repeated.returncode != 0
    assert "already exists" in repeated.stderr
    assert path.read_bytes() == before
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [run]


def test_failed_creation_removes_its_new_file_and_can_be_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, run_input: dict[str, Any]
) -> None:
    path = tmp_path / "runs.sqlite"

    class CreationFailureConnection(sqlite3.Connection):
        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            traceback: TracebackType | None,
        ) -> Literal[False]:
            raise sqlite3.OperationalError("Creation failed before commit")

    with monkeypatch.context() as patch:
        patch.setattr(
            sqlite3,
            "connect",
            partial(sqlite3.connect, factory=CreationFailureConnection),
        )
        with pytest.raises(sqlite3.OperationalError):
            create_database(path)

    assert not path.exists()
    create_database(path)
    storage = SQLiteRunStorage(path)
    run, _ = create_run(storage, **run_input)
    assert storage.get(date(2026, 10, 14), date(2026, 10, 15)) == [run]
