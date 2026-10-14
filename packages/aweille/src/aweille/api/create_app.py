from functools import partial

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

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
from .routes.runs_api import router


def create_app(*, storage: RunStorage) -> FastAPI:
    """Construct the HTTP application with an explicitly supplied storage port.

    Args:
        storage: Initialized storage port for planned-run saves and range reads.

    Returns:
        Application with create and read use cases bound to the storage port.
    """
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
