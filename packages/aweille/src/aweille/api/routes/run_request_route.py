import json
from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any, NoReturn

from fastapi import HTTPException, Request, Response
from fastapi.routing import APIRoute


class RunRequestRoute(APIRoute):
    """Guard run writes with JSON transport limits and bodyless deletion.

    These checks run before FastAPI validates request fields. FastAPI's defaults
    do not cap JSON bodies and use different statuses for some decoding errors.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        """Validate received bytes before FastAPI parses run request fields.

        Returns:
            Handler preserving native body and query parameter validation.
        """
        handler = super().get_route_handler()

        async def handle(request: Request) -> Response:
            if request.method in ("POST", "PATCH"):
                request = _JsonRequest(request.scope, receive=request.receive)
            elif request.method == "DELETE":
                async for chunk in request.stream():
                    if chunk:
                        raise HTTPException(
                            422,
                            [
                                {
                                    "loc": ["body"],
                                    "type": "body_forbidden",
                                    "msg": "Deletion requires an empty body.",
                                }
                            ],
                        )
            return await handler(request)

        return handle


class _JsonRequest(Request):
    async def stream(self) -> AsyncGenerator[bytes]:
        media_type = (
            self.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        )
        if self.method == "PATCH" and media_type in (
            "application/json-patch+json",
            "application/merge-patch+json",
        ):
            raise HTTPException(
                415, "Editing requires a JSON field object, not a patch document."
            )
        if media_type != "application/json" and not (
            media_type.startswith("application/") and media_type.endswith("+json")
        ):
            raise HTTPException(415, "Creation requires a JSON content type.")
        received = 0
        async for chunk in super().stream():
            received += len(chunk)
            if received > 1_048_576:
                raise HTTPException(
                    413, "Creation body exceeds 1 MiB (1,048,576 bytes)."
                )
            yield chunk

    async def json(self) -> Any:
        try:
            return json.loads(await self.body(), parse_constant=_reject_constant)
        except (ValueError, UnicodeError, RecursionError):
            raise HTTPException(
                422,
                [
                    {
                        "loc": ["body"],
                        "type": "json_invalid",
                        "msg": "Supply a valid JSON document.",
                    }
                ],
            ) from None


def _reject_constant(value: str) -> NoReturn:
    raise ValueError("Non-finite constants are not JSON.")
