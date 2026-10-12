from datetime import date
from typing import Protocol

from .model import PlannedRun


class Storage(Protocol):
    """Storage adapters implement these two synchronous operations.

    Translate temporary contention or unavailability to StorageUnavailable,
    and unexpected failures to StorageFailure, with safe explanatory messages.
    Driver exceptions must not cross this port.
    """

    def insert_if_absent(self, run: PlannedRun) -> tuple[PlannedRun, bool]:
        """Atomically insert or return the existing run, without overwriting it.

        True means a new run is committed. Failure leaves no partial run.
        """
        ...

    def read_range(self, start: date, end: date) -> list[PlannedRun]:
        """Return all runs in [start, end) from one committed snapshot, in any order.

        There is no pagination or silent result cap.
        """
        ...
