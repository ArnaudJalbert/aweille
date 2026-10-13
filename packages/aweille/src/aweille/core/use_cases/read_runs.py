from datetime import date, time

from ..models.planned_run import PlannedRun
from ..raise_validation_error import raise_validation_error
from ..run_storage import RunStorage
from ..validate_date import validate_date


def read_runs(storage: RunStorage, *, start: date, end: date) -> list[PlannedRun]:
    """Read planned runs in a Montreal calendar-date range.

    Validate the range before accessing storage. Use planned local dates without
    converting them to UTC or rounding the range to week boundaries.

    Args:
        storage: RunStorage port providing a committed snapshot of matching runs.
        start: First included Montreal calendar date.
        end: First excluded Montreal calendar date, strictly later than start.

    Returns:
        All matching normalized runs, ordered by planned date, then start time
        with untimed runs last within each day, then canonical UUID string.
        Return an empty list when the range contains no runs.

    Raises:
        ValidationError: A boundary is not a calendar date or end is not later
            than start. The error identifies the invalid range field.
        StorageUnavailable: Temporary storage contention or unavailability
            prevents the read. The caller may retry.
        StorageFailure: An unexpected storage failure prevents the read.
    """
    _validate_range(start, end)
    runs = storage.get(start, end)
    return sorted(runs, key=_run_sort_key)


def _validate_range(start: date, end: date) -> None:
    validate_date(start, "start")
    validate_date(end, "end")
    if end <= start:
        raise_validation_error(
            ("end",), "invalid_range", "End date must be later than start date."
        )


def _run_sort_key(run: PlannedRun) -> tuple[date, bool, time, str]:
    return (
        run.planned_date,
        run.planned_start_time is None,
        run.planned_start_time or time.min,
        str(run.id),
    )
