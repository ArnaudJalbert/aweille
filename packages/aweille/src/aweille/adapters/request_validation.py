from typing import NoReturn

from fastapi import HTTPException


def reject(loc: tuple[str | int, ...], code: str, message: str) -> NoReturn:
    """Reject a request with one safe field problem.

    Args:
        loc: Transport-prefixed field path, including section indexes.
        code: Machine-readable error code.
        message: Explanation without raw input values.

    Raises:
        HTTPException: A 422 response containing the field problem.
    """
    raise HTTPException(422, [{"loc": list(loc), "type": code, "msg": message}])
