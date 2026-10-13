import sqlite3
from contextlib import closing
from unittest.mock import Mock

import pytest
from aweille.api.create_app import create_app
from aweille.core import RunStorage
from fastapi.testclient import TestClient


def test_missing_database_returns_retryable_errors_without_recreating(
    api_client, database_path, run_request
):
    moved = database_path.with_name("moved.sqlite")
    database_path.rename(moved)
    for response in (
        api_client.post("/v1/runs", json=run_request),
        api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15"),
    ):
        assert response.status_code == 503
        assert isinstance(response.json()["detail"], str)
        assert str(database_path) not in response.text
    assert not database_path.exists()
    moved.rename(database_path)
    assert api_client.post("/v1/runs", json=run_request).status_code == 201


def test_lock_contention_can_be_resolved_by_retry(
    api_client, database_path, run_request
):
    with closing(sqlite3.connect(database_path)) as blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        response = api_client.post("/v1/runs", json=run_request)
        assert response.status_code == 503
        blocker.rollback()
    assert api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == []
    assert api_client.post("/v1/runs", json=run_request).status_code == 201


def test_failed_write_has_safe_error_and_no_partial_save(
    api_client, database_path, run_request
):
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_run AFTER INSERT ON runs "
            "BEGIN SELECT RAISE(ABORT, 'PRIVATE SQL failure'); END"
        )
    response = api_client.post("/v1/runs", json=run_request)
    assert response.status_code == 500
    assert set(response.json()) == {"detail"}
    assert "PRIVATE" not in response.text
    assert "INSERT" not in response.text
    assert str(database_path) not in response.text
    assert api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == []


@pytest.mark.parametrize("operation", ["save", "get"])
def test_unexpected_port_failure_is_safe_and_logged(
    database_path, monkeypatch, run_request, caplog, operation
):
    monkeypatch.setenv("AWEILLE_DB_PATH", str(database_path))
    storage = Mock(spec=RunStorage)
    getattr(storage, operation).side_effect = RuntimeError("PRIVATE unexpected failure")
    with TestClient(
        create_app(storage=storage), raise_server_exceptions=False
    ) as client:
        response = (
            client.post("/v1/runs", json=run_request)
            if operation == "save"
            else client.get("/v1/runs?start=2026-10-14&end=2026-10-15")
        )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected failure prevents the operation."
    }
    assert "PRIVATE" not in response.text
    assert "PRIVATE unexpected failure" in caplog.text
