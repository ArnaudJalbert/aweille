from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from ..raise_validation_error import raise_validation_error
from ..validate_date import validate_date
from .run_type import RunType
from .section import Section

_MONTREAL = ZoneInfo("America/Toronto")


@dataclass(frozen=True, init=False)
class PlannedRun:
    """An immutable planned run with validated, normalized domain fields.

    Args:
        id: Caller-supplied UUID.
        planned_date: Montreal calendar date.
        planned_start_time: Optional naive local time with minute precision.
        run_type: A RunType member.
        sections: Non-empty ordered sections, copied to an immutable tuple.
        user_note: Optional user text; trim outer whitespace and omit blanks.
        trainer_note: Optional trainer text, normalized separately.

    Raises:
        ValidationError: A field violates the domain rules, including a
            nonexistent Montreal start time.
    """

    id: UUID
    planned_date: date
    planned_start_time: time | None
    run_type: RunType
    sections: tuple[Section, ...]
    user_note: str | None
    trainer_note: str | None

    def __init__(
        self,
        id: UUID,
        planned_date: date,
        planned_start_time: time | None,
        run_type: RunType,
        sections: Sequence[Section],
        user_note: str | None,
        trainer_note: str | None,
    ) -> None:
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
        sections = _normalize_sections(sections)
        user_note = _normalize_note(user_note, "user_note")
        trainer_note = _normalize_note(trainer_note, "trainer_note")
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "planned_date", planned_date)
        object.__setattr__(self, "planned_start_time", planned_start_time)
        object.__setattr__(self, "run_type", run_type)
        object.__setattr__(self, "sections", sections)
        object.__setattr__(self, "user_note", user_note)
        object.__setattr__(self, "trainer_note", trainer_note)


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
