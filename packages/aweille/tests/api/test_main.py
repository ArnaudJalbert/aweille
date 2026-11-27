import sqlite3
from pathlib import Path
from runpy import run_module

import pytest
from aweille.interface_adapters.sqlite.create_database import create_database
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.mark.parametrize("configured", ["", "  ", ":memory:"])
def test_invalid_database_configuration_fails_startup(monkeypatch, configured):
    monkeypatch.setenv("AWEILLE_DB_PATH", configured)
    with pytest.raises(ValueError, match="AWEILLE_DB_PATH"):
        _load_local_app()


@pytest.mark.parametrize("directory_exists", [False, True])
def test_missing_or_directory_database_fails_without_creating(
    tmp_path, monkeypatch, directory_exists
):
    path = tmp_path / "unprepared"
    if directory_exists:
        path.mkdir()
    monkeypatch.setenv("AWEILLE_DB_PATH", str(path))
    with pytest.raises(ValueError, match="aweille-init-db"):
        _load_local_app()
    assert path.is_dir() if directory_exists else not path.exists()


@pytest.mark.parametrize("configured", [None, "~/.local/share/aweille/aweille.sqlite3"])
def test_default_and_tilde_database_paths_persist(
    tmp_path, monkeypatch, planned_course_request, configured
):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = tmp_path / ".local/share/aweille/aweille.sqlite3"
    path.parent.mkdir(parents=True)
    create_database(path)
    if configured is None:
        monkeypatch.delenv("AWEILLE_DB_PATH", raising=False)
    else:
        monkeypatch.setenv("AWEILLE_DB_PATH", configured)
    with TestClient(_load_local_app()) as client:
        saved = client.post("/v1/planned-courses", json=planned_course_request)
        assert saved.status_code == 201
    with TestClient(_load_local_app()) as client:
        assert client.get(
            "/v1/planned-courses?start=2026-10-14&end=2026-10-15"
        ).json() == [saved.json()]


def test_relative_path_is_resolved_once_at_startup(
    database_path, monkeypatch, planned_course_request
):
    monkeypatch.chdir(database_path.parent)
    monkeypatch.setenv("AWEILLE_DB_PATH", database_path.name)
    app = _load_local_app()
    elsewhere = database_path.parent / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("AWEILLE_DB_PATH", "missing.sqlite")
    with TestClient(app) as client:
        assert (
            client.post("/v1/planned-courses", json=planned_course_request).status_code
            == 201
        )
        assert (
            len(
                client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15").json()
            )
            == 1
        )
    assert not (elsewhere / database_path.name).exists()


@pytest.mark.parametrize("contents", [b"", b"PRIVATE not SQLite"])
def test_unprepared_file_is_not_repaired_at_startup_or_during_requests(
    tmp_path, monkeypatch, planned_course_request, contents
):
    path = tmp_path / "unprepared.sqlite"
    path.write_bytes(contents)
    monkeypatch.setenv("AWEILLE_DB_PATH", str(path))
    with pytest.raises(ValueError, match="aweille-init-db"):
        _load_local_app()
    assert path.read_bytes() == contents


@pytest.mark.parametrize("version", [1, 2])
def test_pre_rename_database_is_rejected_at_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: int
) -> None:
    """Startup names the fix for a version 1 or 2 file and leaves it unchanged."""
    path = tmp_path / "runs.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA application_id = 0x41574549")
        connection.execute(f"PRAGMA user_version = {version}")
    before = path.read_bytes()
    monkeypatch.setenv("AWEILLE_DB_PATH", str(path))
    with pytest.raises(ValueError, match=f"version {version}.*aweille-init-db"):
        _load_local_app()
    assert path.read_bytes() == before


def _load_local_app() -> FastAPI:
    return run_module("aweille.api.main")["app"]
