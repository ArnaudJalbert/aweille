import os
from functools import partial
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from aweille.adapters import SQLiteRunStorage
from aweille.core import (
    RunConflict,
    RunStorage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_run,
    read_runs,
)

from .api_errors import conflict_response, failure_response, validation_response
from .runs_api import router


def create_app(*, storage: RunStorage | None = None) -> FastAPI:
    """Construct the HTTP application with injected or configured storage.

    Args:
        storage: Optional initialized storage port, used without SQLite
            configuration. When omitted, construct SQLite storage from the
            configured path to a prepared database.

    Returns:
        Application with create and read use cases bound to the storage port.

    Raises:
        ValueError: No storage port was supplied and database configuration is
            invalid or its resolved path is not an existing file. Prepare
            SQLite storage with aweille-init-db first.
    """
    if storage is None:
        storage = SQLiteRunStorage(_database_path())
    app = FastAPI()
    app.add_exception_handler(RunConflict, conflict_response)
    app.add_exception_handler(ValidationError, validation_response)
    app.add_exception_handler(RequestValidationError, validation_response)
    for error in (StorageUnavailable, StorageFailure, Exception):
        app.add_exception_handler(error, failure_response)
    app.state.create_run = partial(create_run, storage)
    app.state.read_runs = partial(read_runs, storage)
    app.include_router(router, prefix="/v1")
    return app


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
