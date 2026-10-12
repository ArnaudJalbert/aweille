from datetime import date, time

from ..models.planned_run import PlannedRun
from ..raise_validation_error import raise_validation_error
from ..storage import Storage
from ..validate_date import validate_date


def read_runs(storage: Storage, *, start: date, end: date) -> list[PlannedRun]:
    """Read planned runs whose local date is in [start, end)."""
    _validate_range(start, end)
    runs = storage.read_range(start, end)
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
