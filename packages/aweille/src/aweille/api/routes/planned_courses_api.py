import re
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict

from ..schemas.planned_course_error import MessageResponse, ProblemResponse
from ..schemas.planned_course_patch import PlannedCoursePatch
from ..schemas.planned_course_request import PlannedCourseRequest
from ..schemas.planned_course_response import PlannedCourseResponse
from ..schemas.range_query import RangeQuery
from .planned_course_request_route import PlannedCourseRequestRoute

router = APIRouter(route_class=PlannedCourseRequestRoute)

_IF_MATCH = {
    "name": "If-Match",
    "in": "header",
    "required": True,
    "schema": {"type": "string", "pattern": '^"[1-9][0-9]*"$'},
    "description": "Exactly one quoted strong revision from GET; no lists or wildcard.",
}
_ETAG = {
    "ETag": {
        "description": "Quoted strong revision; responses use no-store.",
        "schema": {"type": "string"},
    }
}
_RECOVERY_RESPONSE_EXAMPLES = {
    412: {
        "stale-write": {
            "summary": "Reload after a stale write",
            "value": {
                "detail": "The planned run has changed; reload it before another "
                "edit or deletion."
            },
        }
    },
    428: {
        "missing-if-match": {
            "summary": "Supply the missing precondition",
            "value": {
                "detail": "Reload the run and supply its quoted revision in If-Match."
            },
        }
    },
}
_EDIT_ERRORS = {
    status: {
        "model": ProblemResponse if status == 422 else MessageResponse,
        "description": description,
        **(
            {
                "content": {
                    "application/json": {
                        "examples": _RECOVERY_RESPONSE_EXAMPLES[status]
                    }
                }
            }
            if status in _RECOVERY_RESPONSE_EXAMPLES
            else {}
        ),
    }
    for status, description in {
        404: "Planned run not found.",
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
    "/planned-courses",
    status_code=201,
    responses={
        200: {
            "model": PlannedCourseResponse,
            "description": "Identical normalized retry.",
        },
        201: {
            "headers": {
                "Location": {
                    "description": "Canonical planned-course URL.",
                    "schema": {"type": "string"},
                }
            }
        },
        409: {
            "model": MessageResponse,
            "description": "ID conflicts with current content or is reserved.",
        },
        **{status: _EDIT_ERRORS[status] for status in (413, 415, 422, 500, 503)},
    },
)
def post_planned_course(
    data: PlannedCourseRequest, request: Request, response: Response
) -> PlannedCourseResponse:
    """Create a planned course from JSON and return its committed representation.

    Args:
        data: Creation fields validated by FastAPI and Pydantic.
        request: Request supplying the application's bound use case.
        response: Response used to select the committed insertion/retry status.

    Returns:
        Normalized planned course with 201 for insertion or 200 for an identical retry.

    Raises:
        HTTPException: Unsupported media, oversized body, or malformed JSON.
        InvalidPlannedCourse: Request or domain fields are invalid.
        PlannedCourseConflict: The ID belongs to different normalized data.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    planned_course, inserted = request.app.state.create_planned_course(
        **data.core_inputs()
    )
    response.status_code = 201 if inserted else 200
    if inserted:
        response.headers["Location"] = f"/v1/planned-courses/{planned_course.id}"
    return PlannedCourseResponse.model_validate(planned_course.to_dict())


@router.get(
    "/planned-courses",
    responses={status: _EDIT_ERRORS[status] for status in (422, 500, 503)},
)
def get_planned_courses(
    query: Annotated[RangeQuery, Query()], request: Request
) -> list[PlannedCourseResponse]:
    """Read every planned course in the requested half-open local date range.

    Args:
        query: Calendar-date query parameters validated by FastAPI and Pydantic.
        request: Request supplying the application's bound use case.

    Returns:
        A 200 array of normalized planned courses in use case ordering.

    Raises:
        InvalidPlannedCourse: Query fields or the date range are invalid.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: The storage operation failed.
    """
    planned_courses = request.app.state.read_planned_courses(
        start=query.start, end=query.end
    )
    return [
        PlannedCourseResponse.model_validate(planned_course.to_dict())
        for planned_course in planned_courses
    ]


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
    "/planned-courses/{id}",
    responses={
        200: {
            "headers": _ETAG,
            "content": {
                "application/json": {
                    "examples": {
                        "reload-recovery": {
                            "summary": "Reload the planned course and use its new ETag",
                            "value": {
                                "id": "54d97d4d-fadb-4d50-926e-af1bb26c711a",
                                "planned_date": "2026-10-14",
                                "planned_start_time": "07:30",
                                "course_type": "easy",
                                "sections": [
                                    {
                                        "distance_m": "5000",
                                        "target_pace_seconds_per_km": "390",
                                    }
                                ],
                                "user_note": "Keep it easy.",
                                "trainer_note": "Finish relaxed.",
                                "revision": "2",
                            },
                        }
                    }
                }
            },
        },
        **{status: _EDIT_ERRORS[status] for status in (404, 422, 500, 503)},
    },
)
def get_planned_course(
    id: UUID, query: Annotated[_NoQuery, Query()], request: Request, response: Response
) -> PlannedCourseResponse:
    """Read one live planned course and return its current revision as a strong ETag.

    Args:
        id: Planned course UUID parsed from the path by FastAPI.
        query: Empty query model; extra parameters are rejected.
        request: Request supplying the bound read use case.
        response: Response receiving the quoted revision ETag.

    Returns:
        Complete normalized planned course with its exact string revision.

    Raises:
        RequestValidationError: Path UUID or query parameters are invalid.
        PlannedCourseNotFound: No planned course exists for the UUID (HTTP 404).
        StorageUnavailable: Storage cannot currently read (HTTP 503).
        StorageFailure: Storage cannot read or decode the planned course (HTTP 500).
    """
    planned_course = request.app.state.read_planned_course(id=id)
    response.headers["ETag"] = f'"{planned_course.to_dict()["revision"]}"'
    return PlannedCourseResponse.model_validate(planned_course.to_dict())


@router.patch(
    "/planned-courses/{id}",
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
        "parameters": [_IF_MATCH],
    },
)
def patch_planned_course(
    id: UUID,
    data: PlannedCoursePatch,
    query: Annotated[_NoQuery, Query()],
    request: Request,
    response: Response,
) -> PlannedCourseResponse:
    """Edit supplied fields only when If-Match names the saved revision.

    Args:
        id: Planned course UUID parsed from the path by FastAPI.
        data: Validated partial edit; omitted fields retain saved values.
        query: Empty query model; extra parameters are rejected.
        request: Request supplying If-Match and the bound update use case.
        response: Response receiving the resulting quoted revision ETag.

    Returns:
        Complete normalized planned course with the new revision, or the same revision
        when normalized values did not change.

    Raises:
        RequestValidationError: Path, query, or patch body is invalid (HTTP 422).
        HTTPException: If-Match is missing (HTTP 428) or malformed (HTTP 422).
        InvalidPlannedCourse: The complete edited planned course is invalid (HTTP 422).
        PlannedCourseNotFound: The planned course is absent (HTTP 404).
        PlannedCourseRevisionConflict: The revision is stale (HTTP 412).
        StorageUnavailable: Storage cannot currently read or write (HTTP 503).
        StorageFailure: Storage cannot read or write the planned course (HTTP 500).
    """
    planned_course = request.app.state.update_planned_course(
        id=id, expected_revision=_revision(request), **data.core_inputs()
    )
    response.headers["ETag"] = f'"{planned_course.to_dict()["revision"]}"'
    return PlannedCourseResponse.model_validate(planned_course.to_dict())


@router.delete(
    "/planned-courses/{id}",
    status_code=204,
    responses={
        204: {
            "description": "Committed deletion; no body or ETag. "
            "Cache-Control: no-store."
        },
        **{status: _EDIT_ERRORS[status] for status in (404, 412, 422, 428, 500, 503)},
    },
    openapi_extra={"parameters": [_IF_MATCH]},
)
def delete_planned_course(
    id: UUID, query: Annotated[_NoQuery, Query()], request: Request
) -> Response:
    """Permanently delete a planned course with one quoted If-Match and no body.

    Args:
        id: Planned course UUID parsed from the path by FastAPI.
        query: Empty query model; extra parameters are rejected.
        request: Request supplying If-Match and the bound deletion use case.

    Returns:
        Empty 204 after committed deletion, without an ETag.

    Raises:
        RequestValidationError: Path or query is invalid (HTTP 422).
        HTTPException: Body or precondition is invalid (HTTP 422), or missing
            If-Match (HTTP 428).
        PlannedCourseNotFound: The planned course is absent or already deleted
            (HTTP 404).
        PlannedCourseRevisionConflict: The live revision is stale (HTTP 412).
        StorageUnavailable: Storage is unavailable; reload and review (HTTP 503).
        StorageFailure: The outcome may be uncertain; reload and review (HTTP 500).
    """
    request.app.state.delete_planned_course(id=id, expected_revision=_revision(request))
    return Response(status_code=204)
