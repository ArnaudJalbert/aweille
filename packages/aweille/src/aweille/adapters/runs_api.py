from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .range_query import RangeQuery
from .read_creation_body import read_creation_body
from .request_validation import reject
from .run_request import RunRequest

router = APIRouter()


@router.post("/api/runs")
async def post_run(request: Request) -> JSONResponse:
    """Create a planned run from JSON and return its committed representation.

    Args:
        request: JSON creation request using the application's bound use case.

    Returns:
        Normalized run with 201 for insertion or 200 for an identical retry.

    Raises:
        HTTPException: Unsupported media, oversized body, or malformed JSON.
        ValidationError: Request or domain fields are invalid.
        RunConflict: The ID belongs to different normalized data.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    data = await read_creation_body(request)
    run, inserted = await run_in_threadpool(
        request.app.state.create_run,
        **RunRequest.model_validate(data).core_inputs(),
    )
    return JSONResponse(run.to_dict(), status_code=201 if inserted else 200)


@router.get("/api/runs")
async def get_runs(request: Request) -> JSONResponse:
    """Read every planned run in the requested half-open local date range.

    Args:
        request: Request with start/end calendar-date query parameters.

    Returns:
        A 200 array of normalized runs in core ordering.

    Raises:
        HTTPException: A query parameter is repeated.
        ValidationError: Query fields or the date range are invalid.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    for field in request.query_params:
        if len(request.query_params.getlist(field)) != 1:
            reject(
                ("query", field), "duplicate_parameter", "Supply this parameter once."
            )
    query = RangeQuery.model_validate(dict(request.query_params))
    runs = await run_in_threadpool(
        request.app.state.read_runs,
        start=query.start,
        end=query.end,
    )
    return JSONResponse([run.to_dict() for run in runs])
