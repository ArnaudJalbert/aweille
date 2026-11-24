from pathlib import Path

import pytest
from aweille.adapters.create_database import create_database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "planned-courses.sqlite"
    create_database(path)
    return path
