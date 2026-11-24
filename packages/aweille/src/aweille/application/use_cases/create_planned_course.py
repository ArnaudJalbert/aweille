from collections.abc import Sequence
from datetime import date, time
from uuid import UUID

from aweille.domain import CourseType, PlannedCourse, Section
from aweille.domain.raise_validation_error import raise_validation_error

from ..exceptions.planned_course_conflict import PlannedCourseConflict
from ..repositories.planned_course_repository import PlannedCourseRepository
from .translate_validation_error import translate_validation_error


@translate_validation_error()
def create_planned_course(
    repository: PlannedCourseRepository,
    *,
    id: UUID,
    planned_date: date,
    course_type: CourseType,
    sections: Sequence[Section],
    planned_start_time: time | None = None,
    user_note: str | None = None,
    trainer_note: str | None = None,
) -> tuple[PlannedCourse, bool]:
    """Validate and create a planned course, or return an identical retry.

    Validate and normalize all fields before accessing storage. Preserve section
    order and repeated entries. Trim notes and treat blank notes as absent.

    Args:
        repository: Repository providing an atomic insert-or-read operation.
        id: Caller-supplied UUID, reused when retrying the same creation.
        planned_date: Montreal calendar date. Past and future dates are allowed.
        course_type: A supported CourseType enum member.
        sections: Non-empty ordered Section values. Their Distance and Pace
            fields are validated during construction, in whole metres and whole
            seconds per kilometre respectively.
        planned_start_time: Optional naive Montreal clock time with minute
            precision. Reject spring-forward gaps; allow fall-back ambiguity
            without selecting an occurrence. None means no start time.
        user_note: Optional plain-text note from the user about the planned course.
        trainer_note: Optional plain-text note from the trainer about the course.

    Returns:
        A tuple of the normalized stored planned course and its insertion outcome. The
        outcome is True only after a new planned course is committed. An identical retry
        returns the existing planned course and False.

    Raises:
        InvalidPlannedCourse: An input field or section violates the domain rules.
            The error reports a safe field path, code, and message.
        PlannedCourseConflict: The ID belongs to a planned course with different
            normalized data.
        StorageUnavailable: Temporary storage contention or unavailability
            prevents the operation. The caller may retry with the same ID.
        StorageFailure: An unexpected storage failure prevents the operation.
    """
    planned_course = PlannedCourse(
        id=id,
        planned_date=planned_date,
        course_type=course_type,
        sections=_normalize_sections(sections),
        planned_start_time=_normalize_start_time(planned_start_time),
        user_note=_normalize_note(user_note),
        trainer_note=_normalize_note(trainer_note),
    )
    stored_planned_course, inserted = repository.save(planned_course)
    if not inserted:
        _ensure_retry_matches(planned_course, stored_planned_course)
    return stored_planned_course, inserted


def _normalize_sections(sections: Sequence[Section]) -> tuple[Section, ...]:
    if not isinstance(sections, Sequence) or isinstance(
        sections, (str, bytes, bytearray)
    ):
        raise_validation_error(
            ("sections",), "invalid_sections", "Supply at least one ordered section."
        )
    return tuple(sections)


def _normalize_start_time(value: time | None) -> time | None:
    return value.replace(fold=0) if type(value) is time else value


def _normalize_note(note: str | None) -> str | None:
    return note.strip() or None if isinstance(note, str) else note


def _ensure_retry_matches(proposed: PlannedCourse, stored: PlannedCourse) -> None:
    if stored.to_dict() | {"revision": "1"} != proposed.to_dict():
        raise PlannedCourseConflict(
            "The ID already belongs to a different planned course."
        )
