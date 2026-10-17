import sqlite3
from typing import Any

import pytest


def test_single_read_and_partial_patch_with_strong_revision(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    created = api_client.post("/v1/runs", json=run_request)
    assert created.status_code == 201
    assert created.json()["revision"] == "1"
    assert created.headers["location"] == f"/v1/runs/{run_request['id']}"
    url = f"/v1/runs/{run_request['id']}"
    read = api_client.get(url)
    assert read.status_code == 200
    assert read.headers["etag"] == '"1"'
    assert read.json() == created.json()
    edited = api_client.patch(
        url, json={"user_note": " new note "}, headers={"If-Match": '"1"'}
    )
    assert edited.status_code == 200
    assert edited.headers["etag"] == '"2"'
    assert edited.json()["revision"] == "2"
    assert edited.json()["user_note"] == "new note"
    assert edited.json()["trainer_note"] == created.json()["trainer_note"]
    assert (
        api_client.post(
            "/v1/runs", json={**run_request, "user_note": "new note"}
        ).json()
        == edited.json()
    )
    assert api_client.get(url).json() == edited.json()


@pytest.mark.parametrize(
    "header", [None, "1", 'W/"1"', '"01"', '"1", "2"', "*", b'"\xd9\xa1"']
)
def test_patch_requires_one_canonical_quoted_precondition(
    api_client: Any, run_request: dict[str, Any], header: str | None
) -> None:
    url = f"/v1/runs/{run_request['id']}"
    response = api_client.patch(
        url, json={}, headers={"If-Match": header} if header is not None else {}
    )
    assert response.status_code == (428 if header is None else 422)
    assert response.headers["cache-control"] == "no-store"


def test_stale_edit_does_not_overwrite_saved_run(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    url = f"/v1/runs/{run_request['id']}"
    api_client.post("/v1/runs", json=run_request)
    api_client.patch(url, json={"user_note": "new"}, headers={"If-Match": '"1"'})
    stale = api_client.patch(
        url, json={"user_note": "lost"}, headers={"If-Match": '"1"'}
    )
    assert stale.status_code == 412
    assert stale.json() == {
        "detail": "The planned run has changed; reload it before another edit "
        "or deletion."
    }
    assert api_client.get(url).json()["user_note"] == "new"


def test_patch_validation_and_precondition_order(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    url = f"/v1/runs/{run_request['id']}"
    api_client.post("/v1/runs", json=run_request)
    invalid = api_client.patch(url, json={"sections": None})
    assert invalid.status_code == 422
    assert invalid.json()["detail"][0]["loc"] == ["body", "sections"]
    for body in (
        {"id": run_request["id"]},
        {"revision": "1"},
        {"planned_date": None},
        {"sections": []},
    ):
        response = api_client.patch(url, json=body, headers={"If-Match": '"1"'})
        assert response.status_code == 422
    assert (
        api_client.patch(
            url, json={"user_note": "x"}, headers={"If-Match": '"1"'}
        ).status_code
        == 200
    )
    stale_domain = api_client.patch(
        url,
        json={"planned_date": "2026-03-08", "planned_start_time": "02:30"},
        headers={"If-Match": '"1"'},
    )
    assert stale_domain.status_code == 412


def test_repeated_precondition_and_patch_transport(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    url = f"/v1/runs/{run_request['id']}"
    api_client.post("/v1/runs", json=run_request)
    repeated = api_client.patch(
        url, json={}, headers=[("If-Match", '"1"'), ("if-match", '"1"')]
    )
    assert repeated.status_code == 422
    assert repeated.json()["detail"][0]["loc"] == ["header", "if-match"]
    assert (
        api_client.patch(
            url,
            content="{}",
            headers={"Content-Type": "application/merge-patch+json", "If-Match": '"1"'},
        ).status_code
        == 415
    )
    assert (
        api_client.patch(
            url,
            content="[1]",
            headers={"Content-Type": "application/json", "If-Match": '"1"'},
        ).status_code
        == 422
    )
    assert (
        api_client.patch(
            url,
            content=b"{" + b" " * 1_048_576,
            headers={"Content-Type": "application/json", "If-Match": '"1"'},
        ).status_code
        == 413
    )


def test_openapi_edit_contract(api_client: Any) -> None:
    document = api_client.get("/openapi.json").json()
    resource = document["paths"]["/v1/runs/{id}"]
    assert set(resource) == {"get", "patch", "delete"}
    patch = resource["patch"]
    model = document["components"]["schemas"]["RunPatch"]
    assert "required" not in model
    assert model["additionalProperties"] is False
    for field in ("planned_date", "run_type", "sections"):
        assert {"type": "null"} not in model["properties"][field].get("anyOf", [])
    for field in ("planned_start_time", "user_note", "trainer_note"):
        assert {"type": "null"} in model["properties"][field].get("anyOf", [])
    assert patch["responses"]["200"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("RunResponse")
    assert any(
        parameter["name"] == "If-Match" and parameter["required"]
        for parameter in patch["parameters"]
    )
    assert "ETag" in patch["responses"]["200"]["headers"]
    assert "ETag" in resource["get"]["responses"]["200"]["headers"]
    assert {"500", "503"} <= set(resource["get"]["responses"])
    for status in (500, 503):
        assert "content" in resource["get"]["responses"][str(status)]
    assert (
        "Location"
        in document["paths"]["/v1/runs"]["post"]["responses"]["201"]["headers"]
    )
    assert {"409", "413", "415", "422", "500", "503"} <= set(
        document["paths"]["/v1/runs"]["post"]["responses"]
    )
    assert {"404", "412", "413", "415", "422", "428", "500", "503"} <= set(
        patch["responses"]
    )
    for status in (404, 412, 413, 415, 422, 428, 500, 503):
        assert "content" in patch["responses"][str(status)]
    examples = patch["requestBody"]["content"]["application/json"]["examples"]
    assert examples["clear"]["value"] == {
        "planned_start_time": None,
        "trainer_note": None,
    }


def test_openapi_recovery_examples_match_http_responses(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    document = api_client.get("/openapi.json").json()
    resource = document["paths"]["/v1/runs/{id}"]
    patch_responses = resource["patch"]["responses"]
    stale_example = patch_responses["412"]["content"]["application/json"]["examples"][
        "stale-write"
    ]["value"]
    missing_example = patch_responses["428"]["content"]["application/json"]["examples"][
        "missing-if-match"
    ]["value"]
    reload_example = resource["get"]["responses"]["200"]["content"]["application/json"][
        "examples"
    ]["reload-recovery"]["value"]
    assert stale_example == {
        "detail": "The planned run has changed; reload it before another edit "
        "or deletion."
    }
    assert missing_example == {
        "detail": "Reload the run and supply its quoted revision in If-Match."
    }
    assert reload_example == {
        "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "run_type": "easy",
        "sections": [{"distance_m": "5000", "target_pace_seconds_per_km": "390"}],
        "user_note": "Keep it easy.",
        "trainer_note": "Finish relaxed.",
        "revision": "2",
    }

    url = f"/v1/runs/{run_request['id']}"
    assert (
        api_client.post(
            "/v1/runs",
            json={
                **run_request,
                "planned_start_time": "07:30",
                "trainer_note": "Finish relaxed.",
            },
        ).status_code
        == 201
    )
    missing = api_client.patch(url, json={"user_note": "Keep it easy."})
    assert missing.status_code == 428
    assert missing.json() == missing_example
    edited = api_client.patch(
        url, json={"user_note": "Keep it easy."}, headers={"If-Match": '"1"'}
    )
    assert edited.status_code == 200
    stale = api_client.patch(url, json={}, headers={"If-Match": '"1"'})
    assert stale.status_code == 412
    assert stale.json() == stale_example
    reload = api_client.get(url)
    assert reload.status_code == 200
    assert reload.headers["etag"] == '"2"'
    assert reload.json() == reload_example


def test_huge_revision_remains_exact_through_sqlite_and_http(
    api_client: Any, database_path, run_request: dict[str, Any]
) -> None:
    api_client.post("/v1/runs", json=run_request)
    huge = "1" + "0" * 5000
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE runs SET revision = ? WHERE id = ?", (huge, run_request["id"])
        )
    url = f"/v1/runs/{run_request['id']}"
    assert api_client.get(url).json()["revision"] == huge
    response = api_client.patch(
        url, json={"user_note": "updated"}, headers={"If-Match": f'"{huge}"'}
    )
    assert response.status_code == 200
    assert response.json()["revision"] == "1" + "0" * 4999 + "1"
    assert response.headers["etag"] == f'"{response.json()["revision"]}"'
    assert (
        api_client.delete(
            url, headers={"If-Match": response.headers["etag"]}
        ).status_code
        == 204
    )


def test_missing_run_and_unknown_query_have_safe_locations(
    api_client: Any, run_request: dict[str, Any]
) -> None:
    url = f"/v1/runs/{run_request['id']}"
    assert api_client.get(url).status_code == 404
    assert (
        api_client.patch(url, json={}, headers={"If-Match": '"1"'}).status_code == 404
    )
    invalid = api_client.get(url + "?secret=PRIVATE")
    assert invalid.status_code == 422
    assert invalid.json()["detail"][0]["loc"] == ["query", "secret"]
    assert "PRIVATE" not in invalid.text


def test_storage_failure_response_remains_no_store(
    database_path, run_request: dict[str, Any]
) -> None:
    from aweille.adapters import SQLiteRunStorage
    from aweille.api.create_app import create_app
    from aweille.core import StorageFailure
    from fastapi.testclient import TestClient

    class BrokenStorage(SQLiteRunStorage):
        def load(self, id):
            raise StorageFailure("PRIVATE SQL path")

    with TestClient(
        create_app(storage=BrokenStorage(database_path)), raise_server_exceptions=False
    ) as client:
        response = client.get(f"/v1/runs/{run_request['id']}")
    assert response.status_code == 500
    assert response.headers["cache-control"] == "no-store"
    assert "PRIVATE" not in response.text
