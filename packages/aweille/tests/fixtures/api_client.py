from collections.abc import Generator
from functools import partial
from pathlib import Path

import pytest
from aweille.api.create_app import create_app
from aweille.infrastructure import create_factory_session
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(database_path: Path) -> Generator[TestClient]:
    """Serve the HTTP app over a real factory session on a temporary database."""
    with TestClient(
        create_app(factory=partial(create_factory_session, database_path))
    ) as client:
        yield client
