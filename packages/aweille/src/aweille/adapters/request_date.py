import re
from datetime import date
from typing import Annotated, Any

from pydantic import BeforeValidator, Field
from pydantic_core import PydanticCustomError


def _require_date_format(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
    ):
        raise PydanticCustomError("invalid_date", "Supply a date in YYYY-MM-DD format.")
    return value


RequestDate = Annotated[
    date, Field(strict=False), BeforeValidator(_require_date_format)
]
