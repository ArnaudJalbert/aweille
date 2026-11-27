import sqlite3
from contextlib import closing

import pytest


def test_missing_database_returns_retryable_errors_without_recreating(
    api_client, database_path, planned_course_request
):
    moved = database_path.with_name("moved.sqlite")
    database_path.rename(moved)
    for response in (
        api_client.post("/v1/planned-courses", json=planned_course_request),
        api_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15"),
    ):
        assert response.status_code == 503
        assert isinstance(response.json()["detail"], str)
        assert str(database_path) not in response.text
    assert not database_path.exists()
    moved.rename(database_path)
    assert (
        api_client.post("/v1/planned-courses", json=planned_course_request).status_code
        == 201
    )


def test_lock_contention_can_be_resolved_by_retry(
    api_client, database_path, planned_course_request
):
    with closing(sqlite3.connect(database_path)) as blocker:
        blocker.execute("BEGIN EXCLUSIVE")
        response = api_client.post("/v1/planned-courses", json=planned_course_request)
        assert response.status_code == 503
        blocker.rollback()
    assert (
        api_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15").json()
        == []
    )
    assert (
        api_client.post("/v1/planned-courses", json=planned_course_request).status_code
        == 201
    )


def test_failed_write_has_safe_error_and_no_partial_save(
    api_client, database_path, planned_course_request
):
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_run AFTER INSERT ON planned_courses "
            "BEGIN SELECT RAISE(ABORT, 'PRIVATE SQL failure'); END"
        )
    response = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert response.status_code == 500
    assert set(response.json()) == {"detail"}
    assert "PRIVATE" not in response.text
    assert "INSERT" not in response.text
    assert str(database_path) not in response.text
    assert (
        api_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15").json()
        == []
    )


@pytest.mark.parametrize("operation", ["create", "read_range"])
def test_unexpected_failure_is_logged_but_hidden_from_the_response(
    stub_client, stub_use_cases, planned_course_request, caplog, operation
):
    """An unexpected use case error returns a generic 500 and logs the detail."""
    failing = getattr(stub_use_cases, operation)
    failing.execute.side_effect = RuntimeError("PRIVATE unexpected failure")
    response = (
        stub_client.post("/v1/planned-courses", json=planned_course_request)
        if operation == "create"
        else stub_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15")
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected failure prevents the operation."
    }
    assert "PRIVATE" not in response.text
    assert "PRIVATE unexpected failure" in caplog.text
