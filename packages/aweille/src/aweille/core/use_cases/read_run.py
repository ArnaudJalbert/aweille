from uuid import UUID

from ..errors.run_not_found import RunNotFound
from ..models.planned_run import PlannedRun
from ..raise_validation_error import raise_validation_error
from ..run_storage import RunStorage


def read_run(storage: RunStorage, *, id: UUID) -> PlannedRun:
    """Read a run by UUID, raising RunNotFound when absent."""
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    run = storage.load(id)
    if run is None:
        raise RunNotFound
    return run
