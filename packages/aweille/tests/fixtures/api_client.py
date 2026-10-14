from pathlib import Path

import pytest
from aweille.adapters import SQLiteRunStorage
from aweille.api.create_app import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path):
    with TestClient(create_app(storage=SQLiteRunStorage(database_path))) as client:
        yield client
