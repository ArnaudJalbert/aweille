from dataclasses import dataclass
from uuid import UUID

from aweille.domain.validate_expected_revision import validate_expected_revision
from aweille.domain.validate_id import validate_id

from ..repositories.planned_course_repository import PlannedCourseRepository
from ..translate_validation_error import translate_validation_error


class DeletePlannedCourseCommand:
    """Permanently delete a planned course at its expected revision."""

    @dataclass(frozen=True, slots=True)
    class InputData:
        """The planned course to delete.

        Args:
            id: UUID of the planned course to delete.
            expected_revision: Positive integer revision read by the caller.
        """

        id: UUID
        expected_revision: int

    @dataclass(frozen=True, slots=True)
    class OutputData:
        """Deletion committed; no planned course data is returned."""

    def __init__(self, repository: PlannedCourseRepository) -> None:
        self._repository = repository

    @translate_validation_error()
    def execute(self, input_data: InputData) -> OutputData:
        """Remove a planned course if its saved revision still matches.

        The repository permanently reserves the deleted UUID.

        Args:
            input_data: The planned course and its expected revision.

        Returns:
            Empty output once the deletion is committed.

        Raises:
            InvalidPlannedCourse: The ID or expected revision is invalid.
            PlannedCourseNotFound: The planned course is absent, including an
                already-deleted planned course.
            PlannedCourseRevisionConflict: The saved revision differs from the
                expected one.
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage failed; the commit outcome may be uncertain.
        """
        validate_id(input_data.id)
        validate_expected_revision(input_data.expected_revision)
        self._repository.delete(
            input_data.id, expected_revision=input_data.expected_revision
        )
        return self.OutputData()
