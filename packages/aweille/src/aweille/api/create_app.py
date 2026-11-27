from typing import Any, cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from aweille.application import (
    CreatePlannedCourseCommand,
    DeletePlannedCourseCommand,
    InvalidPlannedCourse,
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseReader,
    PlannedCourseRepository,
    PlannedCourseRevisionConflict,
    ReadPlannedCourseQuery,
    ReadPlannedCoursesQuery,
    StorageFailure,
    StorageUnavailable,
    UpdatePlannedCourseCommand,
)

from .api_errors import (
    conflict_response,
    failure_response,
    missing_response,
    stale_response,
    validation_response,
)
from .routes.planned_courses_api import router
from .routes.weekly_page import WEB_DIRECTORY
from .routes.weekly_page import router as weekly_router


def create_app(
    *, repository: PlannedCourseRepository, reader: PlannedCourseReader
) -> FastAPI:
    """Construct the HTTP application with an explicitly supplied repository and reader.

    Args:
        repository: Initialized repository for planned-course commands.
        reader: Initialized reader for planned-course queries.

    Returns:
        HTTP and browser application with planned-course commands and queries
        built on the repository and reader.
    """
    app = FastAPI()
    _register_error_handlers(app)
    _bind_use_cases(app, repository, reader)
    _configure_cache_policy(app)
    _configure_routes(app)
    _configure_openapi(app)
    return app


def _register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PlannedCourseConflict, conflict_response)
    app.add_exception_handler(PlannedCourseNotFound, missing_response)
    app.add_exception_handler(PlannedCourseRevisionConflict, stale_response)
    app.add_exception_handler(InvalidPlannedCourse, validation_response)
    app.add_exception_handler(RequestValidationError, validation_response)
    for error in (StorageUnavailable, StorageFailure, Exception):
        app.add_exception_handler(error, failure_response)


def _bind_use_cases(
    app: FastAPI, repository: PlannedCourseRepository, reader: PlannedCourseReader
) -> None:
    app.state.create_planned_course = CreatePlannedCourseCommand(repository)
    app.state.update_planned_course = UpdatePlannedCourseCommand(repository)
    app.state.delete_planned_course = DeletePlannedCourseCommand(repository)
    app.state.read_planned_course = ReadPlannedCourseQuery(reader)
    app.state.read_planned_courses = ReadPlannedCoursesQuery(reader)


def _configure_cache_policy(app: FastAPI) -> None:
    @app.middleware("http")
    async def prevent_planned_course_caching(request, call_next):
        result = await call_next(request)
        if request.url.path.startswith("/v1/planned-courses"):
            result.headers["Cache-Control"] = "no-store"
        return result


def _configure_routes(app: FastAPI) -> None:
    app.include_router(router, prefix="/v1")
    app.include_router(weekly_router)
    app.mount("/static", StaticFiles(directory=WEB_DIRECTORY / "static"), name="static")


def _configure_openapi(app: FastAPI) -> None:
    original_openapi = app.openapi

    def openapi_with_clear_example():
        # FastAPI drops explicit nulls when serializing route-level examples.
        document = original_openapi()
        document["paths"]["/v1/planned-courses/{id}"]["patch"]["requestBody"][
            "content"
        ]["application/json"]["examples"]["clear"]["value"] = {
            "planned_start_time": None,
            "trainer_note": None,
        }
        return document

    cast(Any, app).openapi = openapi_with_clear_example
