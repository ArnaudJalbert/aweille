import pytest


def test_normalized_retry_and_conflict_preserve_original(api_client, run_request):
    original = api_client.post("/v1/runs", json=run_request)
    assert original.status_code == 201
    retry = {
        **run_request,
        "id": run_request["id"].upper(),
        "sections": [{"distance_m": "05000", "target_pace_seconds_per_km": "0390"}],
        "user_note": " \n ",
        "trainer_note": None,
    }
    response = api_client.post("/v1/runs", json=retry)
    assert response.status_code == 200
    assert response.json() == original.json()
    response = api_client.post("/v1/runs", json={**retry, "run_type": "long"})
    assert response.status_code == 409
    assert isinstance(response.json()["detail"], str)
    assert api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == [
        original.json()
    ]


@pytest.mark.parametrize(
    ("changes", "location"),
    [
        ({"id": 123}, ["id"]),
        ({"id": "invalid-private-input"}, ["id"]),
        ({"planned_date": "20261014"}, ["planned_date"]),
        ({"planned_date": "2026-02-30"}, ["planned_date"]),
        ({"planned_date": False}, ["planned_date"]),
        ({"run_type": "invalid-private-input"}, ["run_type"]),
        ({"run_type": 1}, ["run_type"]),
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
    api_client, run_request, changes, location
):
    response = api_client.post("/v1/runs", json={**run_request, **changes})
    assert response.status_code == 422
    problem = response.json()["detail"][0]
    assert problem["loc"] == ["body", *location]
    assert set(problem) == {"loc", "type", "msg"}
    assert "invalid-private-input" not in response.text
    assert api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == []


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
def test_invalid_section_rejects_whole_run(api_client, run_request, field, value):
    section = {"distance_m": "1000", "target_pace_seconds_per_km": "390"}
    run_request["sections"].append({**section, field: value})
    response = api_client.post("/v1/runs", json=run_request)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "sections", 1, field]
    assert api_client.get("/v1/runs?start=2026-10-14&end=2026-10-15").json() == []


@pytest.mark.parametrize("field", ["id", "planned_date", "run_type", "sections"])
def test_missing_required_field(api_client, run_request, field):
    del run_request[field]
    response = api_client.post("/v1/runs", json=run_request)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", field]


def test_invalid_uuid_error_does_not_echo_input(api_client, run_request):
    response = api_client.post("/v1/runs", json={**run_request, "id": "Q"})
    assert response.status_code == 422
    assert response.json()["detail"] == [
        {
            "loc": ["body", "id"],
            "type": "uuid_parsing",
            "msg": "ID must be a UUID string.",
        }
    ]


def test_nonexistent_montreal_time_has_field_location(api_client, run_request):
    run_request.update(planned_date="2026-03-08", planned_start_time="02:30")
    response = api_client.post("/v1/runs", json=run_request)
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
        ("start=2026-10-12&start=2026-10-13&end=2026-10-19", "start"),
    ],
)
def test_invalid_range_query(api_client, query, field):
    response = api_client.get(f"/v1/runs?{query}")
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", field]
    assert "private-input" not in response.text


def test_range_boundaries_and_date_time_uuid_order(api_client, run_request):
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
            "/v1/runs",
            json={
                **run_request,
                "id": f"00000000-0000-0000-0000-{number:012d}",
                "planned_date": planned_date,
                "planned_start_time": planned_start_time,
            },
        )
        assert response.status_code == 201
    response = api_client.get("/v1/runs?start=2026-10-12&end=2026-10-19")
    assert response.status_code == 200
    assert [run["id"] for run in response.json()] == [
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000003",
        "00000000-0000-0000-0000-000000000004",
        "00000000-0000-0000-0000-000000000005",
        "00000000-0000-0000-0000-000000000006",
    ]
    assert api_client.get("/v1/runs?start=2026-11-01&end=2026-11-02").json() == []


def test_exact_large_targets_and_notes_survive_http(api_client, run_request):
    # Exceeds both JavaScript's safe integer range and Python's digit threshold.
    digits = "9" * 5000
    run_request.update(
        planned_date="2026-11-01",
        planned_start_time="01:30",
        user_note="  first line\n  second line  ",
        sections=[{"distance_m": digits, "target_pace_seconds_per_km": digits}],
    )
    response = api_client.post("/v1/runs", json=run_request)
    assert response.status_code == 201
    saved = response.json()
    assert saved["sections"] == run_request["sections"]
    assert saved["user_note"] == "first line\n  second line"
    assert saved["planned_start_time"] == "01:30"
    assert api_client.get("/v1/runs?start=2026-11-01&end=2026-11-02").json() == [saved]
