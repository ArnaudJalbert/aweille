import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from aweille.core import StorageUnavailable, ValidationError

logger = logging.getLogger(__name__)


async def failure_response(request: Request, error: Exception) -> JSONResponse:
    """Log internal failure diagnostics and return a safe HTTP explanation.

    Args:
        request: Failed HTTP request.
        error: Storage or unexpected operation failure to log locally.

    Returns:
        Safe 503 response for unavailability or 500 for other failures.
    """
    logger.error("Run operation failed.", exc_info=error)
    if isinstance(error, StorageUnavailable):
        return JSONResponse(
            {"detail": "Storage is temporarily unavailable; retry with the same ID."},
            status_code=503,
        )
    return JSONResponse(
        {"detail": "An unexpected failure prevents the operation."}, status_code=500
    )


async def validation_response(request: Request, error: Exception) -> JSONResponse:
    """Translate request and domain validation problems to HTTP locations.

    Args:
        request: Request supplying the body or query location prefix for core errors.
        error: FastAPI or core validation error without response input values.

    Returns:
        A 422 response with field problems and no raw input or internal context.
    """
    if isinstance(error, RequestValidationError):
        problems = [
            {
                "loc": list(problem["loc"]),
                "type": problem["type"],
                "msg": "ID must be a UUID string."
                if problem["type"] == "uuid_parsing"
                else problem["msg"],
            }
            for problem in error.errors()
        ]
    else:
        assert isinstance(error, ValidationError)
        prefix = "body" if request.method == "POST" else "query"
        problems = [
            {
                "loc": [prefix, *problem.loc],
                "type": problem.code,
                "msg": problem.message,
            }
            for problem in error.problems
        ]
    return JSONResponse(
        {"detail": problems},
        status_code=422,
    )


async def conflict_response(request: Request, error: Exception) -> JSONResponse:
    """Return a safe response when a caller reuses an ID for different data.

    Args:
        request: Conflicting creation request.
        error: RunConflict raised by the initialized create use case.

    Returns:
        A 409 response explaining that the ID belongs to different run data.
    """
    return JSONResponse(
        {"detail": "The ID already belongs to a different planned run."},
        status_code=409,
    )
