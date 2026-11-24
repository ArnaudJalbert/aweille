from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from .planned_course_read_model import PlannedCourseReadModel


class PlannedCourseReader(ABC):
    """Readers return saved planned courses as read models for queries.

    Translate temporary contention or unavailability to StorageUnavailable,
    and unexpected failures to StorageFailure, with safe explanatory messages.
    Driver exceptions must not cross this port.
    """

    @abstractmethod
    def read(self, id: UUID) -> PlannedCourseReadModel | None:
        """Read a single committed planned course, or None if absent.

        Raises:
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage cannot read or decode the planned course.
        """
        ...

    @abstractmethod
    def read_range(self, start: date, end: date) -> list[PlannedCourseReadModel]:
        """Return planned courses in [start, end) from one snapshot, in any order.

        Args:
            start: First included Montreal calendar date.
            end: First excluded Montreal calendar date, later than start.

        Returns:
            All matching planned courses from one committed snapshot, or an empty
            list. Storage order is unspecified; the query applies ordering. There
            is no pagination or silent result cap.

        Raises:
            StorageUnavailable: Temporary contention or unavailability prevents
                the read. The caller may retry.
            StorageFailure: An unexpected storage failure prevents the read.
        """
        ...
