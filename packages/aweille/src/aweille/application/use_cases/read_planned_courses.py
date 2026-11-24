from datetime import date, time

from aweille.domain import PlannedCourse
from aweille.domain.raise_validation_error import raise_validation_error
from aweille.domain.validate_date import validate_date

from ..repositories.planned_course_repository import PlannedCourseRepository
from .translate_validation_error import translate_validation_error


@translate_validation_error()
def read_planned_courses(
    repository: PlannedCourseRepository, *, start: date, end: date
) -> list[PlannedCourse]:
    """Read planned courses in a Montreal calendar-date range.

    Validate the range before accessing storage. Use planned local dates without
    converting them to UTC or rounding the range to week boundaries.

    Args:
        repository: Repository providing a committed snapshot of
            matching planned courses.
        start: First included Montreal calendar date.
        end: First excluded Montreal calendar date, strictly later than start.

    Returns:
        All matching normalized planned courses, ordered by planned date, then
        start time with untimed planned courses last within each day, then
        canonical UUID string.
        Return an empty list when the range contains no planned courses.

    Raises:
        InvalidPlannedCourse: A boundary is not a calendar date or end is not later
            than start. The error identifies the invalid range field.
        StorageUnavailable: Temporary storage contention or unavailability
            prevents the read. The caller may retry.
        StorageFailure: An unexpected storage failure prevents the read.
    """
    _validate_range(start, end)
    planned_courses = repository.get(start, end)
    return sorted(planned_courses, key=_planned_course_sort_key)


def _validate_range(start: date, end: date) -> None:
    validate_date(start, "start")
    validate_date(end, "end")
    if end <= start:
        raise_validation_error(
            ("end",), "invalid_range", "End date must be later than start date."
        )


def _planned_course_sort_key(
    planned_course: PlannedCourse,
) -> tuple[date, bool, time, str]:
    return (
        planned_course.planned_date,
        planned_course.planned_start_time is None,
        planned_course.planned_start_time or time.min,
        str(planned_course.id),
    )
