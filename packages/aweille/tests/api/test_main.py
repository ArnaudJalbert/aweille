from runpy import run_module

import pytest
from aweille.adapters.create_database import create_database
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
    tmp_path, monkeypatch, run_request, configured
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
        saved = client.post("/v1/runs", json=run_request)
        assert saved.status_code == 201
    with TestClient(_load_local_app()) as client:
        assert client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == [
            saved.json()
        ]


def test_relative_path_is_resolved_once_at_startup(
    database_path, monkeypatch, run_request
):
    monkeypatch.chdir(database_path.parent)
    monkeypatch.setenv("AWEILLE_DB_PATH", database_path.name)
    app = _load_local_app()
    elsewhere = database_path.parent / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("AWEILLE_DB_PATH", "missing.sqlite")
    with TestClient(app) as client:
        assert client.post("/v1/runs", json=run_request).status_code == 201
        assert len(client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json()) == 1
    assert not (elsewhere / database_path.name).exists()


@pytest.mark.parametrize("contents", [b"", b"PRIVATE not SQLite"])
def test_unprepared_file_is_not_repaired_at_startup_or_during_requests(
    tmp_path, monkeypatch, run_request, contents
):
    path = tmp_path / "unprepared.sqlite"
    path.write_bytes(contents)
    monkeypatch.setenv("AWEILLE_DB_PATH", str(path))
    with TestClient(_load_local_app()) as client:
        for response in (
            client.post("/v1/runs", json=run_request),
            client.get("/v1/runs?start=2026-10-14&end=2026-10-15"),
        ):
            assert response.status_code == 500
            assert "PRIVATE" not in response.text
            assert str(path) not in response.text
    assert path.read_bytes() == contents


def _load_local_app() -> FastAPI:
    return run_module("aweille.api.main")["app"]
