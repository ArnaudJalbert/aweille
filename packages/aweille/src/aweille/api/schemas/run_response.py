from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aweille.core import RunType

from .section_response import SectionResponse


class RunResponse(BaseModel):
    """Complete normalized run representation returned by both HTTP operations."""

    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(strict=False)
    planned_date: date = Field(strict=False)
    planned_start_time: Annotated[str, Field(pattern=r"^[0-9]{2}:[0-9]{2}$")] | None
    run_type: RunType = Field(strict=False)
    sections: list[SectionResponse] = Field(min_length=1)
    user_note: str | None
    trainer_note: str | None
