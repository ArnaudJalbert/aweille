import pytest


@pytest.fixture
def run_request():
    return {
        "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
        "planned_date": "2026-10-14",
        "run_type": "easy",
        "sections": [{"distance_m": "5000", "target_pace_seconds_per_km": "390"}],
    }
