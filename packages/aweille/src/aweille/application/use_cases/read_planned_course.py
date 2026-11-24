from uuid import UUID

from aweille.domain import PlannedCourse
from aweille.domain.raise_validation_error import raise_validation_error

from ..exceptions.planned_course_not_found import PlannedCourseNotFound
from ..repositories.planned_course_repository import PlannedCourseRepository
from .translate_validation_error import translate_validation_error


@translate_validation_error()
def read_planned_course(
    repository: PlannedCourseRepository, *, id: UUID
) -> PlannedCourse:
    """Load a planned course by UUID.

    Args:
        repository: Repository used to load the saved planned course.
        id: UUID of the planned course to read.

    Returns:
        The saved planned course with its current revision.

    Raises:
        InvalidPlannedCourse: ``id`` is not a UUID.
        PlannedCourseNotFound: No planned course exists for the UUID.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: Storage cannot read or decode the saved planned course.
    """
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    planned_course = repository.load(id)
    if planned_course is None:
        raise PlannedCourseNotFound
    return planned_course
