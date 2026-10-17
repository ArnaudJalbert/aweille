from collections.abc import Sequence
from dataclasses import replace
from datetime import date, time
from typing import cast
from uuid import UUID

from ..errors.run_revision_conflict import RunRevisionConflict
from ..models.planned_run import PlannedRun
from ..models.run_type import RunType
from ..models.section import Section
from ..raise_validation_error import raise_validation_error
from ..run_storage import RunStorage
from .create_run import _normalize_note, _normalize_sections, _normalize_start_time
from .read_run import read_run

UNSET = object()


def update_run(
    storage: RunStorage,
    *,
    id: UUID,
    expected_revision: int,
    planned_date: date | object = UNSET,
    planned_start_time: time | None | object = UNSET,
    run_type: RunType | object = UNSET,
    sections: Sequence[Section] | object = UNSET,
    user_note: str | None | object = UNSET,
    trainer_note: str | None | object = UNSET,
) -> PlannedRun:
    """Replace supplied fields if the saved revision still matches.

    Args:
        storage: Atomic run storage.
        id: Saved run UUID.
        expected_revision: Positive integer revision read by the caller.
        planned_date: New date, or omitted to retain the saved date.
        planned_start_time: New time, None to clear, or omitted to retain.
        run_type: New type or omitted to retain.
        sections: Complete replacement sequence or omitted to retain.
        user_note: New note, None to clear, or omitted to retain.
        trainer_note: New note, None to clear, or omitted to retain.

    Returns:
        Committed full run and current revision, unchanged on a no-op.

    Raises:
        ValidationError: Invalid revision or complete resulting run.
        RunNotFound: The run is absent.
        RunRevisionConflict: A newer revision exists.
    """
    if type(expected_revision) is not int or expected_revision < 1:
        raise_validation_error(
            ("expected_revision",),
            "invalid_revision",
            "Revision must be a positive integer.",
        )
    current = read_run(storage, id=id)
    if current.revision != expected_revision:
        raise RunRevisionConflict
    changes = {}
    for field, value in (
        ("planned_date", planned_date),
        ("planned_start_time", planned_start_time),
        ("run_type", run_type),
        ("sections", sections),
        ("user_note", user_note),
        ("trainer_note", trainer_note),
    ):
        if value is UNSET:
            continue
        if field == "sections":
            value = _normalize_sections(cast(Sequence[Section], value))
        elif field == "planned_start_time":
            value = _normalize_start_time(cast(time | None, value))
        elif field.endswith("_note"):
            value = _normalize_note(cast(str | None, value))
        changes[field] = value
    candidate = replace(current, **changes)
    return storage.replace(candidate, expected_revision=expected_revision)
