from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo

from ..raise_validation_error import raise_validation_error
from ..validate_date import validate_date
from ..validate_id import validate_id
from ..value_objects.course_type import CourseType
from ..value_objects.section import Section


@dataclass(frozen=True)
class PlannedCourse:
    """An immutable planned course that validates normalized domain fields.

    Args:
        id: Caller-supplied UUID.
        planned_date: Montreal calendar date.
        planned_start_time: Optional naive local time with minute precision,
            normalized with normalize_start_time.
        course_type: A CourseType member.
        sections: Non-empty immutable tuple of ordered Section values.
        user_note: Optional user text, normalized with normalize_note.
        trainer_note: Optional trainer text, normalized with normalize_note.
        revision: Positive revision assigned by the repository.

    Raises:
        ValidationError: A field violates the domain rules, including a
            nonexistent Montreal start time.
    """

    id: UUID
    planned_date: date
    planned_start_time: time | None
    course_type: CourseType
    sections: tuple[Section, ...]
    user_note: str | None
    trainer_note: str | None
    revision: int = 1

    _MONTREAL = ZoneInfo("America/Toronto")

    def __post_init__(self) -> None:
        validate_id(self.id)
        validate_date(self.planned_date, "planned_date")
        self._validate_start_time(self.planned_date, self.planned_start_time)
        self._validate_sections(self.sections)
        for field, note in (
            ("user_note", self.user_note),
            ("trainer_note", self.trainer_note),
        ):
            self._validate_note(note, field)

    @staticmethod
    def _validate_sections(sections: tuple[Section, ...]) -> None:
        if not sections:
            raise_validation_error(
                ("sections",),
                "invalid_sections",
                "Supply at least one ordered section.",
            )

    @staticmethod
    def _validate_note(note: str | None, field: str) -> None:
        if note is not None and not isinstance(note, str):
            raise_validation_error(
                (field,), "invalid_note", "Note must be plain text or absent."
            )

    def _validate_start_time(self, planned_date: date, value: time | None) -> None:
        if value is None:
            return
        if (
            type(value) is not time
            or value.tzinfo is not None
            or value.second
            or value.microsecond
        ):
            raise_validation_error(
                ("planned_start_time",),
                "invalid_start_time",
                "Start time must use local minutes without seconds "
                "or a timezone offset.",
            )
        local = datetime.combine(planned_date, value.replace(fold=0), self._MONTREAL)
        # Ordinary dates need no UTC conversion, including Python's calendar endpoints.
        if local.utcoffset() != local.replace(fold=1).utcoffset():
            round_trip = local.astimezone(UTC).astimezone(self._MONTREAL)
            if round_trip.replace(tzinfo=None) != local.replace(tzinfo=None):
                raise_validation_error(
                    ("planned_start_time",),
                    "nonexistent_start_time",
                    "Start time does not exist on this date in Montreal.",
                )
