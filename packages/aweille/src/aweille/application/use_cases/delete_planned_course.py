from uuid import UUID

from aweille.domain.raise_validation_error import raise_validation_error
from aweille.domain.validate_expected_revision import validate_expected_revision

from ..repositories.planned_course_repository import PlannedCourseRepository
from .translate_validation_error import translate_validation_error


@translate_validation_error()
def delete_planned_course(
    repository: PlannedCourseRepository, *, id: UUID, expected_revision: int
) -> None:
    """Permanently remove a planned course if its saved revision still matches.

    Args:
        repository: Atomic repository that permanently reserves deleted UUIDs.
        id: UUID of the planned course to delete.
        expected_revision: Positive integer revision read by the caller.

    Raises:
        InvalidPlannedCourse: ID or expected revision is invalid.
        PlannedCourseNotFound: The planned course is absent, including an
            already-deleted planned course.
        PlannedCourseRevisionConflict: The saved revision differs from the expected one.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: Storage failed; the commit outcome may be uncertain.
    """
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    validate_expected_revision(expected_revision)
    repository.delete(id, expected_revision=expected_revision)
