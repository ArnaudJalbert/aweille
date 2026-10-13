from pathlib import Path

import pytest

from scripts.create_database import create_database


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    path = tmp_path / "runs.sqlite"
    create_database(path)
    return path
