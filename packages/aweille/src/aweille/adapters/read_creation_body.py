import json
from typing import Any, NoReturn

from fastapi import HTTPException, Request

from .request_validation import reject

MAX_CREATION_BYTES = 1_048_576


async def read_creation_body(request: Request) -> Any:
    """Read bounded JSON from the received request stream.

    Args:
        request: Incoming creation request, with or without Content-Length.

    Returns:
        Decoded JSON ready for creation-field validation.

    Raises:
        HTTPException: Non-JSON media type (415), oversized received body (413),
            or malformed JSON (422).
    """
    _require_json_media_type(request)
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_CREATION_BYTES:
            raise HTTPException(413, "Creation body exceeds 1 MiB (1,048,576 bytes).")
        body.extend(chunk)
    try:
        return json.loads(body, parse_constant=_reject_constant)
    except (ValueError, UnicodeError, RecursionError):
        reject(("body",), "json_invalid", "Supply a valid JSON document.")


def _require_json_media_type(request: Request) -> None:
    media_type = (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    )
    if media_type != "application/json" and not (
        media_type.startswith("application/") and media_type.endswith("+json")
    ):
        raise HTTPException(415, "Creation requires a JSON content type.")


def _reject_constant(value: str) -> NoReturn:
    raise ValueError("Non-finite constants are not JSON.")
