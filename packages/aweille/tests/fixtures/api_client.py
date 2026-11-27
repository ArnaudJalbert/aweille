from functools import partial
from pathlib import Path

import pytest
from aweille.api.create_app import create_app
from aweille.infrastructure import create_factory_session
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path):
    with TestClient(
        create_app(factory=partial(create_factory_session, database_path))
    ) as client:
        yield client
