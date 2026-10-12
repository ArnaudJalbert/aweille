from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import NoReturn
from uuid import UUID
from zoneinfo import ZoneInfo

from .errors import RunConflict, ValidationError, ValidationProblem
from .model import PlannedRun, RunType, Section, SectionInput
from .storage import Storage

_MONTREAL = ZoneInfo("America/Toronto")


def create_run(
    storage: Storage,
    *,
    id: UUID,
    planned_date: date,
    run_type: RunType,
    sections: Sequence[SectionInput],
    planned_start_time: time | None = None,
    user_note: str | None = None,
    trainer_note: str | None = None,
) -> tuple[PlannedRun, bool]:
    """Create a planned run and return its committed insertion outcome."""
    if not isinstance(id, UUID):
        _invalid(("id",), "invalid_id", "ID must be a UUID.")
    _validate_date(planned_date, "planned_date")
    planned_start_time = _normalize_start_time(planned_date, planned_start_time)
    if run_type not in ("easy", "hard", "interval", "long"):
        _invalid(
            ("run_type",),
            "invalid_run_type",
            "Run type must be easy, hard, interval, or long.",
        )
    if (
        not isinstance(sections, Sequence)
        or isinstance(sections, (str, bytes, bytearray))
        or not sections
    ):
        _invalid(
            ("sections",), "invalid_sections", "Supply at least one ordered section."
        )
    normalized_sections = []
    for index, section in enumerate(sections):
        if not isinstance(section, SectionInput):
            _invalid(("sections", index), "invalid_section", "Supply a section input.")
        distance = section.distance_km
        distance_loc = ("sections", index, "distance_km")
        if (
            not isinstance(distance, Decimal)
            or not distance.is_finite()
            or distance <= 0
        ):
            _invalid(
                distance_loc,
                "invalid_distance",
                "Distance must be finite, positive, and use whole-metre increments.",
            )
        numerator, denominator = section.distance_km.as_integer_ratio()
        distance_m, remainder = divmod(numerator * 1000, denominator)
        if remainder:
            _invalid(
                distance_loc,
                "invalid_distance",
                "Distance must use whole-metre increments without rounding.",
            )
        pace = section.target_pace_seconds_per_km
        if type(pace) is not int or pace <= 0:
            _invalid(
                ("sections", index, "target_pace_seconds_per_km"),
                "invalid_pace",
                "Target pace must be a positive whole number of seconds per kilometre.",
            )
        normalized_sections.append(Section(distance_m, pace))
    run = PlannedRun(
        id,
        planned_date,
        planned_start_time,
        run_type,
        tuple(normalized_sections),
        _normalize_note(user_note, "user_note"),
        _normalize_note(trainer_note, "trainer_note"),
    )
    stored_run, inserted = storage.insert_if_absent(run)
    if not inserted and stored_run != run:
        raise RunConflict("The ID already belongs to a different planned run.")
    return stored_run, inserted


def read_runs(storage: Storage, *, start: date, end: date) -> list[PlannedRun]:
    """Read planned runs whose local date is in [start, end)."""
    _validate_date(start, "start")
    _validate_date(end, "end")
    if end <= start:
        _invalid(("end",), "invalid_range", "End date must be later than start date.")
    return sorted(
        storage.read_range(start, end),
        key=lambda run: (
            run.planned_date,
            run.planned_start_time is None,
            run.planned_start_time or time.min,
            str(run.id),
        ),
    )


def _normalize_note(note: str | None, field: str) -> str | None:
    if note is not None and not isinstance(note, str):
        _invalid((field,), "invalid_note", "Note must be plain text or absent.")
    return note.strip() or None if note is not None else None


def _validate_date(value: date, field: str) -> None:
    if type(value) is not date:
        _invalid((field,), "invalid_date", "Supply a calendar date without a time.")


def _normalize_start_time(planned_date: date, value: time | None) -> time | None:
    if value is None:
        return None
    if (
        type(value) is not time
        or value.tzinfo is not None
        or value.second
        or value.microsecond
    ):
        _invalid(
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
            _invalid(
                ("planned_start_time",),
                "nonexistent_start_time",
                "Start time does not exist on this date in Montreal.",
            )
    return value


def _invalid(loc: tuple[str | int, ...], code: str, message: str) -> NoReturn:
    raise ValidationError(ValidationProblem(loc, code, message))
