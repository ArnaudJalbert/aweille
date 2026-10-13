from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from ..errors.run_conflict import RunConflict
from ..models.planned_run import PlannedRun
from ..models.run_type import RunType
from ..models.section import Section
from ..raise_validation_error import raise_validation_error
from ..run_storage import RunStorage
from ..validate_date import validate_date

_MONTREAL = ZoneInfo("America/Toronto")


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
    run = _normalize_run(
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


def _normalize_run(
    *,
    id: UUID,
    planned_date: date,
    run_type: RunType,
    sections: Sequence[Section],
    planned_start_time: time | None,
    user_note: str | None,
    trainer_note: str | None,
) -> PlannedRun:
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    validate_date(planned_date, "planned_date")
    planned_start_time = _normalize_start_time(planned_date, planned_start_time)
    if not isinstance(run_type, RunType):
        raise_validation_error(
            ("run_type",),
            "invalid_run_type",
            f"Run type must be a RunType member: {', '.join(RunType)}.",
        )
    return PlannedRun(
        id=id,
        planned_date=planned_date,
        planned_start_time=planned_start_time,
        run_type=run_type,
        sections=_normalize_sections(sections),
        user_note=_normalize_note(user_note, "user_note"),
        trainer_note=_normalize_note(trainer_note, "trainer_note"),
    )


def _normalize_sections(sections: Sequence[Section]) -> tuple[Section, ...]:
    if (
        not isinstance(sections, Sequence)
        or isinstance(sections, (str, bytes, bytearray))
        or not sections
    ):
        raise_validation_error(
            ("sections",), "invalid_sections", "Supply at least one ordered section."
        )
    normalized = tuple(sections)
    for index, section in enumerate(normalized):
        if not isinstance(section, Section):
            raise_validation_error(
                ("sections", index), "invalid_section", "Supply a Section value."
            )
    return normalized


def _ensure_retry_matches(proposed: PlannedRun, stored: PlannedRun) -> None:
    if stored != proposed:
        raise RunConflict("The ID already belongs to a different planned run.")


def _normalize_note(note: str | None, field: str) -> str | None:
    if note is not None and not isinstance(note, str):
        raise_validation_error(
            (field,), "invalid_note", "Note must be plain text or absent."
        )
    return note.strip() or None if note is not None else None


def _normalize_start_time(planned_date: date, value: time | None) -> time | None:
    if value is None:
        return None
    if (
        type(value) is not time
        or value.tzinfo is not None
        or value.second
        or value.microsecond
    ):
        raise_validation_error(
            ("planned_start_time",),
            "invalid_start_time",
            "Start time must use local minutes without seconds or a timezone offset.",
        )
    value = value.replace(fold=0)
    local = datetime.combine(planned_date, value, _MONTREAL)
    # Ordinary dates need no UTC conversion, including Python's calendar endpoints.
    if local.utcoffset() != local.replace(fold=1).utcoffset():
        round_trip = local.astimezone(UTC).astimezone(_MONTREAL)
        if round_trip.replace(tzinfo=None) != local.replace(tzinfo=None):
            raise_validation_error(
                ("planned_start_time",),
                "nonexistent_start_time",
                "Start time does not exist on this date in Montreal.",
            )
    return value
