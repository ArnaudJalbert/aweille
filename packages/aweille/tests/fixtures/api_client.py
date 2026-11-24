from pathlib import Path

import pytest
from aweille.api.create_app import create_app
from aweille.interface_adapters import (
    SQLitePlannedCourseReader,
    SQLitePlannedCourseRepository,
)
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path):
    with TestClient(
        create_app(
            repository=SQLitePlannedCourseRepository(database_path),
            reader=SQLitePlannedCourseReader(database_path),
        )
    ) as client:
        yield client
