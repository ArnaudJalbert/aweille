from collections.abc import AsyncGenerator, Callable
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
)
from typing import Any, cast

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from aweille.application import (
    InvalidPlannedCourse,
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseRevisionConflict,
    StorageFailure,
    StorageUnavailable,
)
from aweille.infrastructure import AweilleFactory

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

FactorySessionOpener = Callable[[], AbstractContextManager[AweilleFactory]]


def create_app(*, factory: FactorySessionOpener) -> FastAPI:
    """Construct the HTTP application over a factory session opened at startup.

    Args:
        factory: Opens the factory session. The app's lifespan calls it once per
            startup and keeps the yielded factory until shutdown.

    Returns:
        HTTP and browser application whose routes call the factory's use cases.
        Startup raises whatever the session raises, such as StorageFailure for
        an incompatible database.
    """
    app = FastAPI(lifespan=_hold_factory_session(factory))
    _register_error_handlers(app)
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


def _hold_factory_session(
    factory: FactorySessionOpener,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        with factory() as opened_factory:
            app.state.factory = opened_factory
            yield

    return lifespan


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
