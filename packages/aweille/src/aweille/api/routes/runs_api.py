from typing import Annotated

from fastapi import APIRouter, Query, Request, Response

from ..schemas.range_query import RangeQuery
from ..schemas.run_request import RunRequest
from ..schemas.run_response import RunResponse
from .creation_route import CreationRoute

router = APIRouter(route_class=CreationRoute)


@router.post(
    "/runs",
    status_code=201,
    responses={
        200: {"model": RunResponse, "description": "Identical normalized retry."}
    },
)
def post_run(data: RunRequest, request: Request, response: Response) -> RunResponse:
    """Create a planned run from JSON and return its committed representation.

    Args:
        data: Creation fields validated by FastAPI and Pydantic.
        request: Request supplying the application's bound use case.
        response: Response used to select the committed insertion/retry status.

    Returns:
        Normalized run with 201 for insertion or 200 for an identical retry.

    Raises:
        HTTPException: Unsupported media, oversized body, or malformed JSON.
        ValidationError: Request or domain fields are invalid.
        RunConflict: The ID belongs to different normalized data.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    run, inserted = request.app.state.create_run(**data.core_inputs())
    response.status_code = 201 if inserted else 200
    return RunResponse.model_validate(run.to_dict())


@router.get("/runs")
def get_runs(
    query: Annotated[RangeQuery, Query()], request: Request
) -> list[RunResponse]:
    """Read every planned run in the requested half-open local date range.

    Args:
        query: Calendar-date query parameters validated by FastAPI and Pydantic.
        request: Request supplying the application's bound use case.

    Returns:
        A 200 array of normalized runs in core ordering.

    Raises:
        ValidationError: Query fields or the date range are invalid.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    runs = request.app.state.read_runs(start=query.start, end=query.end)
    return [RunResponse.model_validate(run.to_dict()) for run in runs]
