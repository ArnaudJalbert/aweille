from datetime import time
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidateAs

from aweille.application import CreatePlannedCourseCommand
from aweille.domain import CourseType

from .request_date import RequestDate

# Decimal preserves exact targets beyond Python's integer-string digit threshold.
_Target = Annotated[
    int,
    ValidateAs(
        Annotated[str, Field(strict=True, pattern=r"^0*[1-9][0-9]*$")],
        lambda value: int(Decimal(value)),
    ),
]
_StartTime = Annotated[
    time,
    ValidateAs(
        Annotated[str, Field(strict=True, pattern=r"^[0-9]{2}:[0-9]{2}$")],
        time.fromisoformat,
    ),
]


class _SectionRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    distance_m: _Target
    target_pace_seconds_per_km: _Target


class PlannedCourseRequest(BaseModel):
    """Strict creation shape, with encoded scalars parsed into domain input types."""

    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(strict=False)
    planned_date: RequestDate
    course_type: CourseType = Field(strict=False)
    sections: list[_SectionRequest] = Field(min_length=1)
    planned_start_time: _StartTime | None = None
    user_note: str | None = None
    trainer_note: str | None = None

    def input_data(self) -> CreatePlannedCourseCommand.InputData:
        """Build the create command's input from the validated request.

        Returns:
            Plain planned course values with ordered sections in whole metres and
            seconds per kilometre.
        """
        return CreatePlannedCourseCommand.InputData(
            id=self.id,
            planned_date=self.planned_date,
            course_type=self.course_type,
            sections=tuple(
                CreatePlannedCourseCommand.InputData.SectionInput(
                    metres=section.distance_m,
                    seconds_per_km=section.target_pace_seconds_per_km,
                )
                for section in self.sections
            ),
            planned_start_time=self.planned_start_time,
            user_note=self.user_note,
            trainer_note=self.trainer_note,
        )
