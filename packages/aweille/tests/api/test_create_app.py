from pathlib import Path

from aweille.api.create_app import create_app
from aweille.interface_adapters import SQLitePlannedCourseRepository
from fastapi.testclient import TestClient


def test_create_normalize_and_read_after_restart(database_path: Path):
    payload = {
        "id": "54D97D4D-FADB-4D50-926E-AF1BB26C711A",
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "course_type": "interval",
        "sections": [
            {"distance_m": "01000", "target_pace_seconds_per_km": "0390"},
            {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
            {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
        ],
        "user_note": "  Keep the first section easy.  ",
        "trainer_note": "  Finish relaxed.  ",
    }
    expected = {
        "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
        "planned_date": "2026-10-14",
        "planned_start_time": "07:30",
        "course_type": "interval",
        "sections": [
            {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
            {"distance_m": "1000", "target_pace_seconds_per_km": "345"},
            {"distance_m": "1000", "target_pace_seconds_per_km": "390"},
        ],
        "user_note": "Keep the first section easy.",
        "trainer_note": "Finish relaxed.",
        "revision": "1",
    }
    with TestClient(
        create_app(repository=SQLitePlannedCourseRepository(database_path))
    ) as client:
        response = client.post("/v1/planned-courses", json=payload)
        assert response.status_code == 201
        assert response.json() == expected
        response = client.get("/v1/planned-courses?start=2026-10-12&end=2026-10-19")
        assert response.status_code == 200
        assert response.json() == [expected]
    with TestClient(
        create_app(repository=SQLitePlannedCourseRepository(database_path))
    ) as client:
        assert client.get(
            "/v1/planned-courses?start=2026-10-12&end=2026-10-19"
        ).json() == [expected]
        retry = client.post("/v1/planned-courses", json=payload)
        assert retry.status_code == 200
        assert retry.json() == expected
