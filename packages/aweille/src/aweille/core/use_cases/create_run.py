from collections.abc import Sequence
from datetime import date, time
from uuid import UUID

from ..errors.run_conflict import RunConflict
from ..models.planned_run import PlannedRun
from ..models.run_type import RunType
from ..models.section import Section
from ..run_storage import RunStorage


def create_run(
    storage: RunStorage,
    *,
    id: UUID,
    planned_date: date,
    run_type: RunType,
    sections: Sequence[Section],
    planned_start_time: time | None = None,
    user_note: str | None = None,
    trainer_note: str | None = None,
) -> tuple[PlannedRun, bool]:
    """Validate and create a planned run, or return an identical retry.

    Validate and normalize all fields before accessing storage. Preserve section
    order and repeated entries. Trim notes and treat blank notes as absent.

    Args:
        storage: RunStorage port providing an atomic insert-or-read operation.
        id: Caller-supplied UUID, reused when retrying the same creation.
        planned_date: Montreal calendar date. Past and future dates are allowed.
        run_type: A supported RunType enum member.
        sections: Non-empty ordered Section values. Their Distance and Pace
            fields are validated during construction, in whole metres and whole
            seconds per kilometre respectively.
        planned_start_time: Optional naive Montreal clock time with minute
            precision. Reject spring-forward gaps; allow fall-back ambiguity
            without selecting an occurrence. None means no start time.
        user_note: Optional plain-text note from the user about the whole run.
        trainer_note: Optional plain-text note from the trainer about the run.

    Returns:
        A tuple of the normalized stored run and its insertion outcome. The
        outcome is True only after a new run is committed. An identical retry
        returns the existing run and False.

    Raises:
        ValidationError: An input field or section violates the domain rules.
            The error reports a safe field path, code, and message.
        RunConflict: The ID belongs to a run with different normalized data.
        StorageUnavailable: Temporary storage contention or unavailability
            prevents the operation. The caller may retry with the same ID.
        StorageFailure: An unexpected storage failure prevents the operation.
    """
    run = PlannedRun(
        id=id,
        planned_date=planned_date,
        run_type=run_type,
        sections=sections,
        planned_start_time=planned_start_time,
        user_note=user_note,
        trainer_note=trainer_note,
    )
    stored_run, inserted = storage.save(run)
    if not inserted:
        _ensure_retry_matches(run, stored_run)
    return stored_run, inserted


def _ensure_retry_matches(proposed: PlannedRun, stored: PlannedRun) -> None:
    if stored != proposed:
        raise RunConflict("The ID already belongs to a different planned run.")
