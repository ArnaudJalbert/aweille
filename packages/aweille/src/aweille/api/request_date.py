from datetime import date
from typing import Annotated

from pydantic import Field, ValidateAs

RequestDate = Annotated[
    date,
    ValidateAs(
        Annotated[str, Field(strict=True, pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")],
        date.fromisoformat,
    ),
]
