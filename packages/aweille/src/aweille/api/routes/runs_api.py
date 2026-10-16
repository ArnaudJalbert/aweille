import re
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict

from ..schemas.range_query import RangeQuery
from ..schemas.run_error import MessageResponse, ProblemResponse
from ..schemas.run_patch import RunPatch
from ..schemas.run_request import RunRequest
from ..schemas.run_response import RunResponse
from .creation_route import CreationRoute

router = APIRouter(route_class=CreationRoute)

_ETAG = {
    "ETag": {
        "description": "Quoted strong revision; responses use no-store.",
        "schema": {"type": "string"},
    }
}
_EDIT_ERRORS = {
    status: {
        "model": ProblemResponse if status == 422 else MessageResponse,
        "description": description,
    }
    for status, description in {
        404: "Run not found.",
        412: "Stale revision; reload before another write.",
        413: "Body exceeds 1 MiB.",
        415: "JSON field object required.",
        422: "Invalid fields, JSON, or precondition.",
        428: "Missing If-Match; reload and send quoted revision.",
        500: "Uncertain failure; reload and review.",
        503: "Storage unavailable; reload and review.",
    }.items()
}


@router.post(
    "/runs",
    status_code=201,
    responses={
        200: {"model": RunResponse, "description": "Identical normalized retry."},
        201: {
            "headers": {
                "Location": {
                    "description": "Canonical single-run URL.",
                    "schema": {"type": "string"},
                }
            }
        },
        409: {
            "model": MessageResponse,
            "description": "ID belongs to different saved data.",
        },
        **{status: _EDIT_ERRORS[status] for status in (413, 415, 422, 500, 503)},
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
    if inserted:
        response.headers["Location"] = f"/v1/runs/{run.id}"
    return RunResponse.model_validate(run.to_dict())


@router.get(
    "/runs", responses={status: _EDIT_ERRORS[status] for status in (422, 500, 503)}
)
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


class _NoQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _revision(request: Request) -> int:
    values = [
        value for name, value in request.scope["headers"] if name.lower() == b"if-match"
    ]
    if not values:
        raise HTTPException(
            428, "Reload the run and supply its quoted revision in If-Match."
        )
    if (
        len(values) != 1
        or re.fullmatch(rb'"[1-9][0-9]*"', values[0].strip(b" \t")) is None
    ):
        raise HTTPException(
            422,
            [
                {
                    "loc": ["header", "if-match"],
                    "type": "revision_precondition",
                    "msg": "Supply one quoted positive canonical revision.",
                }
            ],
        )
    return int(Decimal(values[0].strip(b" \t")[1:-1].decode("ascii")))


@router.get(
    "/runs/{id}",
    responses={
        200: {"headers": _ETAG},
        **{status: _EDIT_ERRORS[status] for status in (404, 422, 500, 503)},
    },
)
def get_run(
    id: UUID, query: Annotated[_NoQuery, Query()], request: Request, response: Response
) -> RunResponse:
    """Read a single live run, including its strong revision validator."""
    run = request.app.state.read_run(id=id)
    response.headers["ETag"] = f'"{run.to_dict()["revision"]}"'
    return RunResponse.model_validate(run.to_dict())


@router.patch(
    "/runs/{id}",
    responses={200: {"headers": _ETAG}, **_EDIT_ERRORS},
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "partial": {
                            "value": {
                                "planned_date": "2026-10-18",
                                "user_note": "Keep it easy.",
                            }
                        },
                        "clear": {
                            "value": {"planned_start_time": None, "trainer_note": None}
                        },
                        "no-op": {"value": {}},
                    }
                }
            }
        },
        "parameters": [
            {
                "name": "If-Match",
                "in": "header",
                "required": True,
                "schema": {"type": "string", "pattern": '^"[1-9][0-9]*"$'},
                "description": "One quoted strong revision from GET.",
            }
        ],
    },
)
def patch_run(
    id: UUID,
    data: RunPatch,
    query: Annotated[_NoQuery, Query()],
    request: Request,
    response: Response,
) -> RunResponse:
    """Apply only supplied fields against one exact expected revision."""
    run = request.app.state.update_run(
        id=id, expected_revision=_revision(request), **data.core_inputs()
    )
    response.headers["ETag"] = f'"{run.to_dict()["revision"]}"'
    return RunResponse.model_validate(run.to_dict())
