from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from ..errors.run_conflict import RunConflict
from ..models.planned_run import PlannedRun
from ..models.run_type import RunType
from ..models.section import Section
from ..models.section_input import SectionInput
from ..raise_validation_error import raise_validation_error
from ..storage import Storage
from ..validate_date import validate_date

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
    run = _normalize_run(
        id=id,
        planned_date=planned_date,
        run_type=run_type,
        sections=sections,
        planned_start_time=planned_start_time,
        user_note=user_note,
        trainer_note=trainer_note,
    )
    stored_run, inserted = storage.insert_if_absent(run)
    if not inserted:
        _ensure_retry_matches(run, stored_run)
    return stored_run, inserted


def _normalize_run(
    *,
    id: UUID,
    planned_date: date,
    run_type: RunType,
    sections: Sequence[SectionInput],
    planned_start_time: time | None,
    user_note: str | None,
    trainer_note: str | None,
) -> PlannedRun:
    if not isinstance(id, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
    validate_date(planned_date, "planned_date")
    planned_start_time = _normalize_start_time(planned_date, planned_start_time)
    if run_type not in ("easy", "hard", "interval", "long"):
        raise_validation_error(
            ("run_type",),
            "invalid_run_type",
            "Run type must be easy, hard, interval, or long.",
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


def _normalize_sections(sections: Sequence[SectionInput]) -> tuple[Section, ...]:
    if (
        not isinstance(sections, Sequence)
        or isinstance(sections, (str, bytes, bytearray))
        or not sections
    ):
        raise_validation_error(
            ("sections",), "invalid_sections", "Supply at least one ordered section."
        )
    return tuple(
        _normalize_section(section, index) for index, section in enumerate(sections)
    )


def _normalize_section(section: SectionInput, index: int) -> Section:
    if not isinstance(section, SectionInput):
        raise_validation_error(
            ("sections", index), "invalid_section", "Supply a section input."
        )
    distance_m = _distance_in_metres(section.distance_km, index)
    _validate_pace(section.target_pace_seconds_per_km, index)
    return Section(distance_m, section.target_pace_seconds_per_km)


def _distance_in_metres(distance_km: Decimal, index: int) -> int:
    loc = ("sections", index, "distance_km")
    if (
        not isinstance(distance_km, Decimal)
        or not distance_km.is_finite()
        or distance_km <= 0
    ):
        raise_validation_error(
            loc,
            "invalid_distance",
            "Distance must be finite, positive, and use whole-metre increments.",
        )
    numerator, denominator = distance_km.as_integer_ratio()
    distance_m, remainder = divmod(numerator * 1000, denominator)
    if remainder:
        raise_validation_error(
            loc,
            "invalid_distance",
            "Distance must use whole-metre increments without rounding.",
        )
    return distance_m


def _validate_pace(pace: int, index: int) -> None:
    if type(pace) is not int or pace <= 0:
        raise_validation_error(
            ("sections", index, "target_pace_seconds_per_km"),
            "invalid_pace",
            "Target pace must be a positive whole number of seconds per kilometre.",
        )


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
