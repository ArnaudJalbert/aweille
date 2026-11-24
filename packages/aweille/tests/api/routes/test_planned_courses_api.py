import pytest
from fastapi.testclient import TestClient


def test_openapi_describes_normalized_planned_course_responses(api_client):
    document = api_client.get("/openapi.json").json()
    resource = document["paths"]["/v1/planned-courses"]
    created = resource["post"]["responses"]["201"]["content"]["application/json"][
        "schema"
    ]
    retry = resource["post"]["responses"]["200"]["content"]["application/json"][
        "schema"
    ]
    read = resource["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert retry == created
    assert read["type"] == "array"
    assert read["items"] == created
    models = document["components"]["schemas"]
    planned_course = models[created["$ref"].split("/")[-1]]
    assert set(planned_course["required"]) == {
        "id",
        "planned_date",
        "planned_start_time",
        "course_type",
        "sections",
        "user_note",
        "trainer_note",
        "revision",
    }
    section = models[
        planned_course["properties"]["sections"]["items"]["$ref"].split("/")[-1]
    ]
    assert section["properties"]["distance_m"]["type"] == "string"
    assert section["properties"]["target_pace_seconds_per_km"]["type"] == "string"


def test_normalized_retry_and_conflict_preserve_original(
    api_client, planned_course_request
):
    original = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert original.status_code == 201
    retry = {
        **planned_course_request,
        "id": planned_course_request["id"].upper(),
        "sections": [{"distance_m": "05000", "target_pace_seconds_per_km": "0390"}],
        "user_note": " \n ",
        "trainer_note": None,
    }
    response = api_client.post("/v1/planned-courses", json=retry)
    assert response.status_code == 200
    assert response.json() == original.json()
    response = api_client.post(
        "/v1/planned-courses", json={**retry, "course_type": "long"}
    )
    assert response.status_code == 409
    assert isinstance(response.json()["detail"], str)
    assert api_client.get(
        "/v1/planned-courses?start=2026-10-14&end=2026-10-15"
    ).json() == [original.json()]


@pytest.mark.parametrize(
    ("changes", "location"),
    [
        ({"id": 123}, ["id"]),
        ({"id": "invalid-private-input"}, ["id"]),
        ({"planned_date": "20261014"}, ["planned_date"]),
        ({"planned_date": "2026-02-30"}, ["planned_date"]),
        ({"planned_date": False}, ["planned_date"]),
        ({"course_type": "invalid-private-input"}, ["course_type"]),
        ({"course_type": 1}, ["course_type"]),
        ({"planned_start_time": "07:30:00"}, ["planned_start_time"]),
        ({"planned_start_time": "07:30-04:00"}, ["planned_start_time"]),
        ({"planned_start_time": "24:00"}, ["planned_start_time"]),
        ({"planned_start_time": False}, ["planned_start_time"]),
        ({"user_note": 7}, ["user_note"]),
        ({"trainer_note": False}, ["trainer_note"]),
        ({"unknown": "invalid-private-input"}, ["unknown"]),
        ({"sections": []}, ["sections"]),
        ({"sections": {}}, ["sections"]),
        ({"sections": [None]}, ["sections", 0]),
        (
            {"sections": [{"distance_m": "1000"}]},
            ["sections", 0, "target_pace_seconds_per_km"],
        ),
        (
            {
                "sections": [
                    {
                        "distance_m": "1000",
                        "target_pace_seconds_per_km": "390",
                        "extra": 1,
                    }
                ]
            },
            ["sections", 0, "extra"],
        ),
    ],
)
def test_invalid_creation_is_rejected_without_saving(
    api_client, planned_course_request, changes, location
):
    response = api_client.post(
        "/v1/planned-courses", json={**planned_course_request, **changes}
    )
    assert response.status_code == 422
    problem = response.json()["detail"][0]
    assert problem["loc"] == ["body", *location]
    assert set(problem) == {"loc", "type", "msg"}
    assert "invalid-private-input" not in response.text
    assert (
        api_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15").json()
        == []
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("distance_m", "0"),
        ("distance_m", "-1"),
        ("distance_m", "+1"),
        ("distance_m", "1.0"),
        ("distance_m", "1e3"),
        ("distance_m", " 1"),
        ("distance_m", "1\n"),
        ("distance_m", "١"),
        ("distance_m", 1),
        ("distance_m", True),
        ("distance_m", None),
        ("target_pace_seconds_per_km", "0"),
        ("target_pace_seconds_per_km", 390),
    ],
)
def test_invalid_section_rejects_whole_planned_course(
    api_client, planned_course_request, field, value
):
    section = {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
    planned_course_request["sections"].append({**section, field: value})
    response = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "sections", 1, field]
    assert (
        api_client.get("/v1/planned-courses?start=2026-10-14&end=2026-10-15").json()
        == []
    )


@pytest.mark.parametrize("field", ["id", "planned_date", "course_type", "sections"])
def test_missing_required_field(api_client, planned_course_request, field):
    del planned_course_request[field]
    response = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


def test_invalid_uuid_error_does_not_echo_input(api_client, planned_course_request):
    response = api_client.post(
        "/v1/planned-courses", json={**planned_course_request, "id": "Q"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {
            "loc": ["body", "id"],
            "type": "uuid_parsing",
            "msg": "ID must be a UUID string.",
        }
    ]


def test_nonexistent_montreal_time_has_field_location(
    api_client, planned_course_request
):
    planned_course_request.update(planned_date="2026-03-08", planned_start_time="02:30")
    response = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "planned_start_time"]


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("end=2026-10-19", "start"),
        ("start=2026-10-12", "end"),
        ("start=20261012&end=2026-10-19", "start"),
        ("start=2026-10-12&end=2026-02-30", "end"),
        ("start=2026-10-12&end=2026-10-12", "end"),
        ("start=2026-10-19&end=2026-10-12", "end"),
        ("start=2026-10-12&end=2026-10-19&strat=private-input", "strat"),
    ],
)
def test_invalid_range_query(api_client, query, field):
    response = api_client.get(f"/v1/planned-courses?{query}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", field]
    assert "private-input" not in response.text


def test_repeated_query_dates_use_last_value(api_client, planned_course_request):
    created = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert created.status_code == 201
    response = api_client.get(
        "/v1/planned-courses?start=2026-10-15&start=2026-10-14&end=2026-10-15"
    )
    assert response.status_code == 200
    assert response.json() == [created.json()]


def test_range_boundaries_and_date_time_uuid_order(api_client, planned_course_request):
    scenarios = [
        (7, "2026-10-19", None),
        (6, "2026-10-18", None),
        (5, "2026-10-12", None),
        (4, "2026-10-12", "09:00"),
        (3, "2026-10-12", "07:30"),
        (2, "2026-10-12", "07:30"),
        (1, "2026-10-11", "07:30"),
    ]
    for number, planned_date, planned_start_time in scenarios:
        response = api_client.post(
            "/v1/planned-courses",
            json={
                **planned_course_request,
                "id": f"00000000-0000-0000-0000-{number:012d}",
                "planned_date": planned_date,
                "planned_start_time": planned_start_time,
            },
        )
        assert response.status_code == 201
    response = api_client.get("/v1/planned-courses?start=2026-10-12&end=2026-10-19")
    assert response.status_code == 200
    assert [planned_course["id"] for planned_course in response.json()] == [
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000004",
        "00000000-0000-0000-0000-000000000005",
        "00000000-0000-0000-0000-000000000006",
    ]
    assert (
        api_client.get("/v1/planned-courses?start=2026-11-01&end=2026-11-02").json()
        == []
    )


def test_exact_large_targets_and_notes_survive_http(api_client, planned_course_request):
    # Exceeds both JavaScript's safe integer range and Python's digit threshold.
    digits = "9" * 5000
    planned_course_request.update(
        planned_date="2026-11-01",
        planned_start_time="01:30",
        user_note="  first line\n  second line  ",
        sections=[{"distance_m": digits, "target_pace_seconds_per_km": digits}],
    )
    response = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert response.status_code == 201
    saved = response.json()
    assert saved["sections"] == planned_course_request["sections"]
    assert saved["user_note"] == "first line\n  second line"
    assert saved["planned_start_time"] == "01:30"
    assert api_client.get(
        "/v1/planned-courses?start=2026-11-01&end=2026-11-02"
    ).json() == [saved]


def test_planned_courses_replace_the_runs_resource(
    api_client: TestClient, planned_course_request: dict
) -> None:
    """Planned courses use course_type at the new path, with no /v1/runs alias."""
    created = api_client.post("/v1/planned-courses", json=planned_course_request)
    assert created.status_code == 201
    location = f"/v1/planned-courses/{planned_course_request['id']}"
    assert created.headers["Location"] == location
    assert created.headers["Cache-Control"] == "no-store"
    assert created.json()["course_type"] == "easy"
    assert "run_type" not in created.json()
    assert api_client.post("/v1/runs", json=planned_course_request).status_code == 404
    assert api_client.get(f"/v1/runs/{planned_course_request['id']}").status_code == 404
