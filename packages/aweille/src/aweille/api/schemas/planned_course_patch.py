"""Partial, strictly typed planned-course edits."""

from typing import Any, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aweille.application import UpdatePlannedCourseCommand
from aweille.domain import CourseType

from .planned_course_request import _SectionRequest, _StartTime
from .request_date import RequestDate


class PlannedCoursePatch(BaseModel):
    """Only editable fields; omitted properties remain absent."""

    model_config = ConfigDict(strict=True, extra="forbid")

    planned_date: RequestDate = cast(RequestDate, None)
    planned_start_time: _StartTime | None = None
    course_type: CourseType = Field(default=cast(CourseType, None), strict=False)
    sections: list[_SectionRequest] = Field(
        default=cast(list[_SectionRequest], None), min_length=1
    )
    user_note: str | None = None
    trainer_note: str | None = None

    @field_validator("planned_date", "course_type", "sections", mode="before")
    @classmethod
    def reject_required_nulls(cls, value: Any) -> Any:
        """Reject explicit null for fields that cannot be cleared."""
        if value is None:
            raise ValueError("Required editable field cannot be null.")
        return value

    def to_input_data(
        self, id: UUID, expected_revision: int
    ) -> UpdatePlannedCourseCommand.InputData:
        """Build the update command's input from only the supplied fields.

        Args:
            id: Planned course UUID from the path.
            expected_revision: Revision from If-Match.

        Returns:
            Input that leaves every omitted field unchanged.
        """
        changes = self.model_dump(exclude_unset=True, exclude={"sections"})
        if "sections" in self.model_fields_set:
            changes["sections"] = tuple(
                UpdatePlannedCourseCommand.InputData.SectionInput(
                    metres=section.distance_m,
                    seconds_per_km=section.target_pace_seconds_per_km,
                )
                for section in self.sections
            )
        return UpdatePlannedCourseCommand.InputData(
            id=id, expected_revision=expected_revision, **changes
        )
