from datetime import date
from typing import Protocol
from uuid import UUID

from .models.planned_run import PlannedRun


class RunStorage(Protocol):
    """Storage adapters implement synchronous planned-run reads and writes.

    Translate temporary contention or unavailability to StorageUnavailable,
    and unexpected failures to StorageFailure, with safe explanatory messages.
    Driver exceptions must not cross this port.
    """

    def save(self, run: PlannedRun) -> tuple[PlannedRun, bool]:
        """Atomically insert or return the existing run, without overwriting it.

        Args:
            run: Validated, normalized planned run with a caller-supplied UUID.

        Returns:
            The committed run and insertion outcome. True means a new run was
            committed; False means the existing ID's run is returned unchanged
            for core to compare. Failure leaves no partial run.

        Raises:
            StorageUnavailable: Temporary contention or unavailability prevents
                the operation. The caller may retry with the same ID.
            StorageFailure: An unexpected storage failure prevents the operation.
        """
        ...

    def load(self, id: UUID) -> PlannedRun | None:
        """Read a single committed run, or None if absent."""
        ...

    def replace(self, run: PlannedRun, *, expected_revision: int) -> PlannedRun:
        """Atomically check revision and replace changed content."""
        ...

    def delete(self, id: UUID, *, expected_revision: int) -> None:
        """Atomically remove workout content and permanently reserve its UUID.

        Args:
            id: UUID of the live run to remove.
            expected_revision: Revision that must match the committed run.

        Raises:
            RunNotFound: The UUID is absent or already deleted.
            RunRevisionConflict: The live revision differs from the expected one.
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage failed; a possible commit remains uncertain.
        """
        ...

    def get(self, start: date, end: date) -> list[PlannedRun]:
        """Return all runs in [start, end) from one committed snapshot, in any order.

        Args:
            start: First included Montreal calendar date.
            end: First excluded Montreal calendar date, later than start.

        Returns:
            All matching normalized runs from one committed snapshot, or an
            empty list. Storage order is unspecified; core applies ordering.
            There is no pagination or silent result cap.

        Raises:
            StorageUnavailable: Temporary contention or unavailability prevents
                the read. The caller may retry.
            StorageFailure: An unexpected storage failure prevents the read.
        """
        ...
