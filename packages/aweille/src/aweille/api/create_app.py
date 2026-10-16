from functools import partial
from typing import Any, cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from aweille.core import (
    RunConflict,
    RunNotFound,
    RunRevisionConflict,
    RunStorage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_run,
    read_run,
    read_runs,
    update_run,
)

from .api_errors import (
    conflict_response,
    failure_response,
    missing_response,
    stale_response,
    validation_response,
)
from .routes.runs_api import router
from .routes.weekly_page import WEB_DIRECTORY
from .routes.weekly_page import router as weekly_router


def create_app(*, storage: RunStorage) -> FastAPI:
    """Construct the HTTP application with an explicitly supplied storage port.

    Args:
        storage: Initialized storage port for planned-run saves and range reads.

    Returns:
        Application with create and read use cases bound to the storage port.
    """
    app = FastAPI()
    app.add_exception_handler(RunConflict, conflict_response)
    app.add_exception_handler(RunNotFound, missing_response)
    app.add_exception_handler(RunRevisionConflict, stale_response)
    app.add_exception_handler(ValidationError, validation_response)
    app.add_exception_handler(RequestValidationError, validation_response)
    for error in (StorageUnavailable, StorageFailure, Exception):
        app.add_exception_handler(error, failure_response)
    app.state.create_run = partial(create_run, storage)
    app.state.read_runs = partial(read_runs, storage)
    app.state.read_run = partial(read_run, storage)
    app.state.update_run = partial(update_run, storage)

    @app.middleware("http")
    async def prevent_run_caching(request, call_next):
        result = await call_next(request)
        if request.url.path.startswith("/v1/runs"):
            result.headers["Cache-Control"] = "no-store"
        return result

    app.include_router(router, prefix="/v1")
    app.include_router(weekly_router)
    app.mount("/static", StaticFiles(directory=WEB_DIRECTORY / "static"), name="static")
    original_openapi = app.openapi

    def openapi_with_clear_example():
        # FastAPI drops explicit nulls when serializing route-level examples.
        document = original_openapi()
        document["paths"]["/v1/runs/{id}"]["patch"]["requestBody"]["content"][
            "application/json"
        ]["examples"]["clear"]["value"] = {
            "planned_start_time": None,
            "trainer_note": None,
        }
        return document

    cast(Any, app).openapi = openapi_with_clear_example
    return app
