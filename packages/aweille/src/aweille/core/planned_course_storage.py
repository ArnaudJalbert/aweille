from datetime import date
from typing import Protocol
from uuid import UUID

from .models.planned_course import PlannedCourse


class PlannedCourseStorage(Protocol):
    """Storage adapters implement synchronous planned-course reads and writes.

    Translate temporary contention or unavailability to StorageUnavailable,
    and unexpected failures to StorageFailure, with safe explanatory messages.
    Driver exceptions must not cross this port.
    """

    def save(self, planned_course: PlannedCourse) -> tuple[PlannedCourse, bool]:
        """Atomically insert or return the existing planned course without overwriting.

        Args:
            planned_course: Validated, normalized planned course with a caller-supplied
                UUID.

        Returns:
            The committed planned course and insertion outcome. True means a new
            planned course was committed; False means the existing ID's planned
            course is returned unchanged for core to compare. Failure leaves no
            partial planned course.

        Raises:
            StorageUnavailable: Temporary contention or unavailability prevents
                the operation. The caller may retry with the same ID.
            StorageFailure: An unexpected storage failure prevents the operation.
        """
        ...

    def load(self, id: UUID) -> PlannedCourse | None:
        """Read a single committed planned course, or None if absent."""
        ...

    def replace(
        self, planned_course: PlannedCourse, *, expected_revision: int
    ) -> PlannedCourse:
        """Atomically check revision and replace changed content."""
        ...

    def delete(self, id: UUID, *, expected_revision: int) -> None:
        """Atomically remove workout content and permanently reserve its UUID.

        Args:
            id: UUID of the live planned course to remove.
            expected_revision: Revision that must match the committed planned course.

        Raises:
            PlannedCourseNotFound: The UUID is absent or already deleted.
            PlannedCourseRevisionConflict: The live revision differs from the expected
                one.
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage failed; a possible commit remains uncertain.
        """
        ...

    def get(self, start: date, end: date) -> list[PlannedCourse]:
        """Return planned courses in [start, end) from one snapshot, in any order.

        Args:
            start: First included Montreal calendar date.
            end: First excluded Montreal calendar date, later than start.

        Returns:
            All matching normalized planned courses from one committed snapshot, or an
            empty list. Storage order is unspecified; core applies ordering.
            There is no pagination or silent result cap.

        Raises:
            StorageUnavailable: Temporary contention or unavailability prevents
                the read. The caller may retry.
            StorageFailure: An unexpected storage failure prevents the read.
        """
        ...
