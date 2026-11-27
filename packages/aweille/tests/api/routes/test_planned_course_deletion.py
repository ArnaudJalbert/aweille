import asyncio
from typing import Any

import httpx2 as httpx
import pytest
from aweille.application import (
    PlannedCourseNotFound,
    PlannedCourseRevisionConflict,
    StorageFailure,
    StorageUnavailable,
)


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
    stub_client, stub_use_cases, headers, planned_course_request
) -> None:
    response = stub_client.delete(
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
    stub_use_cases.delete.execute.assert_not_called()


@pytest.mark.parametrize(
    "path,body,location",
    [
        ("not-a-uuid", b"", ["path", "id"]),
        ("00000000-0000-0000-0000-000000000033?revision=1", b"", ["query", "revision"]),
        ("00000000-0000-0000-0000-000000000033", b" ", ["body"]),
    ],
)
def test_delete_transport_and_schema_precede_missing_header(
    stub_client, stub_use_cases, path, body, location
) -> None:
    response = stub_client.request(
        "DELETE", f"/v1/planned-courses/{path}", content=body
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == location
    stub_use_cases.delete.execute.assert_not_called()


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


@pytest.mark.parametrize(
    "error,status",
    [(PlannedCourseRevisionConflict, 412), (PlannedCourseNotFound, 404)],
)
def test_delete_reports_a_competing_write(
    stub_client, stub_use_cases, planned_course_request, error, status
) -> None:
    """A delete that loses to a competing edit or delete gets 412 or 404."""
    stub_use_cases.delete.execute.side_effect = error()
    response = stub_client.delete(
        f"/v1/planned-courses/{planned_course_request['id']}",
        headers={"If-Match": ' "1"\t'},
    )
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("error", [StorageFailure, StorageUnavailable])
def test_delete_storage_errors_are_safe_and_do_not_claim_rollback(
    stub_client, stub_use_cases, planned_course_request, error
) -> None:
    """A storage error after delete hides its detail and asks for a reload."""
    stub_use_cases.delete.execute.side_effect = error("PRIVATE SQL path")
    response = stub_client.delete(
        f"/v1/planned-courses/{planned_course_request['id']}",
        headers={"If-Match": '"1"'},
    )
    assert response.status_code == (503 if error is StorageUnavailable else 500)
    assert "PRIVATE" not in response.text
    assert response.headers["cache-control"] == "no-store"
    assert "retry with the same ID" not in response.text
    if error is StorageUnavailable:
        assert "Reload and review" in response.json()["detail"]


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
