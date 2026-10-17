"""Public safe error envelopes used in OpenAPI responses."""

from pydantic import BaseModel


class Problem(BaseModel):
    """One field-level failure without echoed input."""

    loc: list[str | int]
    type: str
    msg: str


class ProblemResponse(BaseModel):
    """Safe validation error envelope."""

    detail: list[Problem]


class MessageResponse(BaseModel):
    """Safe non-field error envelope."""

    detail: str
