"""Local Uvicorn entry point with configured persistent SQLite storage."""

import os
from functools import partial
from pathlib import Path

from aweille.infrastructure import create_factory_session

from .create_app import create_app


def _database_path() -> Path:
    configured = os.environ.get(
        "AWEILLE_DB_PATH", "~/.local/share/aweille/aweille.sqlite3"
    )
    if not configured.strip() or configured.strip() == ":memory:":
        raise ValueError("AWEILLE_DB_PATH must name a persistent database file.")
    try:
        path = Path(configured).expanduser().resolve()
        if not path.is_file():
            raise ValueError(
                "AWEILLE_DB_PATH must name an existing database file. Prepare its "
                "parent directory and run aweille-init-db <path> before startup."
            )
    except (OSError, RuntimeError) as error:
        raise ValueError(
            "AWEILLE_DB_PATH could not be resolved to a database file."
        ) from error
    return path


app = create_app(factory=partial(create_factory_session, _database_path()))
