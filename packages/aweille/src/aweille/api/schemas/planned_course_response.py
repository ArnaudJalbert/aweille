from datetime import date
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aweille.core import CourseType

from .section_response import SectionResponse


class PlannedCourseResponse(BaseModel):
    """Complete normalized planned course returned by every HTTP operation."""

    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(strict=False)
    planned_date: date = Field(strict=False)
    planned_start_time: Annotated[str, Field(pattern=r"^[0-9]{2}:[0-9]{2}$")] | None
    course_type: CourseType = Field(strict=False)
    sections: list[SectionResponse] = Field(min_length=1)
    user_note: str | None
    trainer_note: str | None
    revision: Annotated[str, Field(pattern=r"^[1-9][0-9]*$")]
