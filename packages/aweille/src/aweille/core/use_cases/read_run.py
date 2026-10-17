from uuid import UUID

from ..errors.run_not_found import RunNotFound
from ..models.planned_run import PlannedRun
from ..raise_validation_error import raise_validation_error
from ..run_storage import RunStorage


def read_run(storage: RunStorage, *, id: UUID) -> PlannedRun:
    """Load a planned run by UUID.

    Args:
        storage: Storage port used to load the saved run.
        id: UUID of the run to read.

    Returns:
        The saved run with its current revision.

    Raises:
        ValidationError: ``id`` is not a UUID.
        RunNotFound: No run exists for the UUID.
        StorageUnavailable: Storage is temporarily unavailable.
        StorageFailure: Storage cannot read or decode the saved run.
    """
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    run = storage.load(id)
    if run is None:
        raise RunNotFound
    return run
