from datetime import date
from decimal import Decimal
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aweille.application import (
    CreatePlannedCourseCommand,
    PlannedCourseReadModel,
    ReadPlannedCourseQuery,
    UpdatePlannedCourseCommand,
)
from aweille.domain import CourseType

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

    @classmethod
    def from_output_data(
        cls,
        planned_course: CreatePlannedCourseCommand.OutputData
        | UpdatePlannedCourseCommand.OutputData
        | ReadPlannedCourseQuery.OutputData
        | PlannedCourseReadModel,
    ) -> Self:
        """Encode a planned course from a command or query as canonical strings.

        Args:
            planned_course: Planned course values returned by the application.

        Returns:
            The response with minute times and decimal-digit targets and revision.
        """
        start_time = planned_course.planned_start_time
        return cls.model_validate(
            {
                "id": planned_course.id,
                "planned_date": planned_course.planned_date,
                "planned_start_time": start_time.isoformat(timespec="minutes")
                if start_time is not None
                else None,
                "course_type": planned_course.course_type,
                "sections": [
                    {
                        "distance_m": str(Decimal(section.metres)),
                        "target_pace_seconds_per_km": str(
                            Decimal(section.seconds_per_km)
                        ),
                    }
                    for section in planned_course.sections
                ],
                "user_note": planned_course.user_note,
                "trainer_note": planned_course.trainer_note,
                "revision": str(Decimal(planned_course.revision)),
            }
        )
