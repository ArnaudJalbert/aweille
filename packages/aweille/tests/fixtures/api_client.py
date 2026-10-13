from pathlib import Path

import pytest
from aweille.api.create_app import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path, monkeypatch):
    monkeypatch.setenv("AWEILLE_DB_PATH", str(database_path))
    with TestClient(create_app()) as client:
        yield client
