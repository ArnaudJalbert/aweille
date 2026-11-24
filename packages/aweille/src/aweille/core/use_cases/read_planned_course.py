from uuid import UUID

from ..errors.planned_course_not_found import PlannedCourseNotFound
from ..models.planned_course import PlannedCourse
from ..planned_course_storage import PlannedCourseStorage
from ..raise_validation_error import raise_validation_error


def read_planned_course(storage: PlannedCourseStorage, *, id: UUID) -> PlannedCourse:
    """Load a planned course by UUID.

    Args:
        storage: Storage port used to load the saved planned course.
        id: UUID of the planned course to read.

    Returns:
        The saved planned course with its current revision.

    Raises:
        ValidationError: ``id`` is not a UUID.
        PlannedCourseNotFound: No planned course exists for the UUID.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: Storage cannot read or decode the saved planned course.
    """
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    planned_course = storage.load(id)
    if planned_course is None:
        raise PlannedCourseNotFound
    return planned_course
