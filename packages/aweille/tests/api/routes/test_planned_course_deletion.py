import asyncio
from dataclasses import replace
from typing import Any
from unittest.mock import Mock, create_autospec

import httpx2 as httpx
import pytest
from aweille.api.create_app import create_app
from aweille.application import (
    PlannedCourseReader,
    PlannedCourseRepository,
    StorageFailure,
    StorageUnavailable,
)
from aweille.interface_adapters import (
    SQLitePlannedCourseReader,
    SQLitePlannedCourseRepository,
)
from fastapi.testclient import TestClient


def test_delete_commits_empty_response_and_prevents_resurrection(
    api_client: Any, planned_course_request: dict[str, Any]
) -> None:
    assert (
        api_client.post("/v1/planned-courses", json=planned_course_request).status_code
        == 201
    )
    url = f"/v1/planned-courses/{planned_course_request['id']}"
    response = api_client.delete(url, headers={"If-Match": '"1"'})
    assert response.status_code == 204
    assert response.content == b""
    assert "etag" not in response.headers
    assert response.headers["cache-control"] == "no-store"
    assert api_client.get(url).status_code == 404
    assert (
        api_client.get("/v1/planned-courses?start=2026-10-12&end=2026-10-19").json()
        == []
    )
    repeated = api_client.delete(url, headers={"If-Match": '"1"'})
    assert repeated.status_code == 404
    assert repeated.json() == {"detail": "Planned course not found."}
    assert (
        api_client.patch(url, json={}, headers={"If-Match": '"1"'}).status_code == 404
    )
    retry = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert retry.status_code == 409
    assert retry.json() == {"detail": "The ID cannot be used for this planned course."}


@pytest.mark.parametrize(
    "headers",
    [
        None,
        {"If-Match": ""},
        {"If-Match": "1"},
        [("If-Match", '"1"'), ("if-match", '"1"')],
    ],
)
def test_delete_precondition_failures_never_reach_storage(
    headers, planned_course_request
) -> None:
    storage = Mock(spec=PlannedCourseRepository)
    reader = create_autospec(PlannedCourseReader, instance=True)
    with TestClient(create_app(repository=storage, reader=reader)) as client:
        response = client.delete(
            f"/v1/planned-courses/{planned_course_request['id']}", headers=headers
        )
    assert response.status_code == (428 if headers is None else 422)
    if headers is not None:
        assert response.json()["detail"][0] == {
            "loc": ["header", "if-match"],
            "type": "revision_precondition",
            "msg": "Supply one quoted positive canonical revision.",
        }
    assert response.headers["cache-control"] == "no-store"
    assert storage.mock_calls == []
    assert reader.mock_calls == []


@pytest.mark.parametrize(
    "path,body,location",
    [
        ("not-a-uuid", b"", ["path", "id"]),
        ("00000000-0000-0000-0000-000000000033?revision=1", b"", ["query", "revision"]),
        ("00000000-0000-0000-0000-000000000033", b" ", ["body"]),
    ],
)
def test_delete_transport_and_schema_precede_missing_header(
    path, body, location
) -> None:
    storage = Mock(spec=PlannedCourseRepository)
    reader = create_autospec(PlannedCourseReader, instance=True)
    with TestClient(create_app(repository=storage, reader=reader)) as client:
        response = client.request("DELETE", f"/v1/planned-courses/{path}", content=body)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == location
    assert storage.mock_calls == []
    assert reader.mock_calls == []


def test_delete_stops_reading_nonempty_stream(
    api_client, planned_course_request
) -> None:
    async def send():
        async def body():
            yield b"x"
            raise AssertionError("DELETE must stop after first received byte")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=api_client.app),
            base_url="http://testserver",
        ) as client:
            return await client.request(
                "DELETE",
                f"/v1/planned-courses/{planned_course_request['id']}",
                content=body(),
                headers={"If-Match": '"1"', "Content-Length": "0"},
            )

    response = asyncio.run(send())
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body"]


@pytest.mark.parametrize("competing", ["edit", "delete"])
def test_delete_rechecks_competing_writes_at_atomic_boundary(
    database_path, planned_course_request, competing
) -> None:
    class CompetingStorage(SQLitePlannedCourseRepository):
        def delete(self, id, *, expected_revision):
            if competing == "edit":
                current = self.load(id)
                assert current is not None
                self.replace(replace(current, trainer_note="new"), expected_revision=1)
            else:
                super().delete(id, expected_revision=1)
            super().delete(id, expected_revision=expected_revision)

    with TestClient(
        create_app(
            repository=CompetingStorage(database_path),
            reader=SQLitePlannedCourseReader(database_path),
        )
    ) as client:
        client.post("/v1/planned-courses", json=planned_course_request)
        url = f"/v1/planned-courses/{planned_course_request['id']}"
        response = client.delete(url, headers={"If-Match": ' "1"\t'})
        assert response.status_code == (412 if competing == "edit" else 404)
        current = client.get(url)
        assert current.status_code == (200 if competing == "edit" else 404)
        if competing == "edit":
            assert current.json()["trainer_note"] == "new"


@pytest.mark.parametrize("error", [StorageFailure, StorageUnavailable])
@pytest.mark.parametrize("committed", [False, True])
def test_delete_storage_errors_are_safe_and_do_not_claim_rollback(
    database_path, planned_course_request, error, committed
) -> None:
    class FailingStorage(SQLitePlannedCourseRepository):
        def delete(self, id, *, expected_revision):
            if committed:
                super().delete(id, expected_revision=expected_revision)
            raise error("PRIVATE SQL path")

    with TestClient(
        create_app(
            repository=FailingStorage(database_path),
            reader=SQLitePlannedCourseReader(database_path),
        ),
        raise_server_exceptions=False,
    ) as client:
        client.post("/v1/planned-courses", json=planned_course_request)
        url = f"/v1/planned-courses/{planned_course_request['id']}"
        response = client.delete(url, headers={"If-Match": '"1"'})
        assert response.status_code == (503 if error is StorageUnavailable else 500)
        assert "PRIVATE" not in response.text
        assert response.headers["cache-control"] == "no-store"
        assert "retry with the same ID" not in response.text
        if error is StorageUnavailable:
            assert "Reload and review" in response.json()["detail"]
        assert client.get(url).status_code == (404 if committed else 200)


def test_openapi_delete_contract(api_client) -> None:
    resource = api_client.get("/openapi.json").json()["paths"][
        "/v1/planned-courses/{id}"
    ]["delete"]
    assert "requestBody" not in resource
    assert any(
        p["name"] == "id" and p["schema"]["format"] == "uuid"
        for p in resource["parameters"]
    )
    assert any(
        p["name"] == "If-Match"
        and p["required"]
        and p["schema"]["pattern"] == '^"[1-9][0-9]*"$'
        for p in resource["parameters"]
    )
    assert set(resource["responses"]) == {
        "204",
        "404",
        "412",
        "422",
        "428",
        "500",
        "503",
    }
    assert "content" not in resource["responses"]["204"]
    for code in (404, 412, 422, 428, 500, 503):
        assert "content" in resource["responses"][str(code)]
