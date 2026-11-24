"""Partial, strictly typed planned-course edits."""

from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aweille.core import CourseType, Distance, Pace, Section

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

    def core_inputs(self) -> dict[str, Any]:
        """Return only supplied, validated editable fields."""
        data = self.model_dump(exclude_unset=True)
        if "sections" in data:
            data["sections"] = [
                Section(Distance(s.distance_m), Pace(s.target_pace_seconds_per_km))
                for s in self.sections
            ]
        return data
