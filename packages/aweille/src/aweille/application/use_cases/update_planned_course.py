from collections.abc import Sequence
from dataclasses import replace
from datetime import date, time
from typing import cast
from uuid import UUID

from aweille.domain import CourseType, PlannedCourse, Section
from aweille.domain.validate_expected_revision import validate_expected_revision

from ..exceptions.planned_course_revision_conflict import PlannedCourseRevisionConflict
from ..repositories.planned_course_repository import PlannedCourseRepository
from .create_planned_course import (
    _normalize_note,
    _normalize_sections,
    _normalize_start_time,
)
from .read_planned_course import read_planned_course
from .translate_validation_error import translate_validation_error

UNSET = object()


@translate_validation_error()
def update_planned_course(
    repository: PlannedCourseRepository,
    *,
    id: UUID,
    expected_revision: int,
    planned_date: date | object = UNSET,
    planned_start_time: time | None | object = UNSET,
    course_type: CourseType | object = UNSET,
    sections: Sequence[Section] | object = UNSET,
    user_note: str | None | object = UNSET,
    trainer_note: str | None | object = UNSET,
) -> PlannedCourse:
    """Replace supplied fields if the saved revision still matches.

    Args:
        repository: Atomic planned course repository.
        id: Saved planned course UUID.
        expected_revision: Positive integer revision read by the caller.
        planned_date: New date, or omitted to retain the saved date.
        planned_start_time: New time, None to clear, or omitted to retain.
        course_type: New type or omitted to retain.
        sections: Complete replacement sequence or omitted to retain.
        user_note: New note, None to clear, or omitted to retain.
        trainer_note: New note, None to clear, or omitted to retain.

    Returns:
        Committed full planned course and current revision, unchanged on a no-op.

    Raises:
        InvalidPlannedCourse: Invalid revision or complete resulting planned course.
        PlannedCourseNotFound: The planned course is absent.
        PlannedCourseRevisionConflict: A newer revision exists.
    """
    validate_expected_revision(expected_revision)
    current = read_planned_course(repository, id=id)
    if current.revision != expected_revision:
        raise PlannedCourseRevisionConflict
    changes = {}
    for field, value in (
        ("planned_date", planned_date),
        ("planned_start_time", planned_start_time),
        ("course_type", course_type),
        ("sections", sections),
        ("user_note", user_note),
        ("trainer_note", trainer_note),
    ):
        if value is UNSET:
            continue
        if field == "sections":
            value = _normalize_sections(cast(Sequence[Section], value))
        elif field == "planned_start_time":
            value = _normalize_start_time(cast(time | None, value))
        elif field.endswith("_note"):
            value = _normalize_note(cast(str | None, value))
        changes[field] = value
    candidate = replace(current, **changes)
    return repository.replace(candidate, expected_revision=expected_revision)
