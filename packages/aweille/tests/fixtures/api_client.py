from pathlib import Path

import pytest
from aweille.adapters import SQLitePlannedCourseStorage
from aweille.api.create_app import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path):
    with TestClient(
        create_app(storage=SQLitePlannedCourseStorage(database_path))
    ) as client:
        yield client
