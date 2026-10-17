from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import UTC, date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from ..errors.validation_error import ValidationError
from ..raise_validation_error import raise_validation_error
from ..validate_date import validate_date
from .distance import Distance
from .pace import Pace
from .run_type import RunType
from .section import Section


@dataclass(frozen=True)
class PlannedRun:
    """An immutable planned run that validates already-normalized domain fields.

    Args:
        id: Caller-supplied UUID.
        planned_date: Montreal calendar date.
        planned_start_time: Optional naive local time with minute precision.
        run_type: A RunType member.
        sections: Non-empty immutable tuple of ordered Section values.
        user_note: Optional nonblank user text with outer whitespace trimmed.
        trainer_note: Optional trainer text with the same normalization rules.

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
    revision: int = 1

    _MONTREAL = ZoneInfo("America/Toronto")

    def __post_init__(self) -> None:
        if type(self.revision) is not int or self.revision < 1:
            raise_validation_error(
                ("revision",),
                "invalid_revision",
                "Revision must be a positive integer.",
            )
        self._validate_id(self.id)
        validate_date(self.planned_date, "planned_date")
        self._validate_start_time(self.planned_date, self.planned_start_time)
        if self.planned_start_time is not None and self.planned_start_time.fold:
            raise_validation_error(
                ("planned_start_time",),
                "invalid_start_time",
                "Start time must not select a daylight-saving occurrence.",
            )
        self._validate_run_type(self.run_type)
        self._validate_sections(self.sections)
        for field, note in (
            ("user_note", self.user_note),
            ("trainer_note", self.trainer_note),
        ):
            self._validate_note(note, field)

    def to_dict(self) -> dict[str, Any]:
        """Encode a normalized run as portable canonical values.

        Returns:
            A fresh dictionary with UUID/date/time strings, ordered sections,
            decimal-digit metre and pace strings, and separate optional notes.
        """
        return {
            "id": str(self.id),
            "planned_date": self.planned_date.isoformat(),
            "planned_start_time": self.planned_start_time.isoformat(timespec="minutes")
            if self.planned_start_time is not None
            else None,
            "run_type": self.run_type.value,
            "sections": [
                {
                    "distance_m": str(Decimal(section.distance.metres)),
                    "target_pace_seconds_per_km": str(
                        Decimal(section.target_pace.seconds_per_km)
                    ),
                }
                for section in self.sections
            ],
            "user_note": self.user_note,
            "trainer_note": self.trainer_note,
            "revision": str(Decimal(self.revision)),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PlannedRun:
        """Decode the canonical dictionary representation of a run.

        Args:
            data: All fields in the representation produced by to_dict.

        Returns:
            An immutable validated run, preserving exact ordered targets.

        Raises:
            ValueError: The encoded shape or scalar representation is invalid.
            ValidationError: Decoded values violate domain invariants.
        """
        try:
            if data.keys() != {field.name for field in fields(cls)}:
                raise ValueError
            if not isinstance(data["sections"], list):
                raise ValueError
            run = cls(
                id=UUID(data["id"]),
                planned_date=date.fromisoformat(data["planned_date"]),
                planned_start_time=time.fromisoformat(data["planned_start_time"])
                if data["planned_start_time"] is not None
                else None,
                run_type=RunType(data["run_type"]),
                sections=tuple(
                    cls._decode_section(value) for value in data["sections"]
                ),
                user_note=data["user_note"],
                trainer_note=data["trainer_note"],
                revision=cls._decode_revision(data["revision"]),
            )
            if run.to_dict() != dict(data):
                raise ValueError
            return run
        except ValidationError:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
            raise ValueError("Encoded planned-run data is invalid.") from None

    @classmethod
    def _decode_section(cls, value: object) -> Section:
        if not isinstance(value, dict) or value.keys() != {
            "distance_m",
            "target_pace_seconds_per_km",
        }:
            raise ValueError
        return Section(
            Distance(cls._decode_integer(value["distance_m"])),
            Pace(cls._decode_integer(value["target_pace_seconds_per_km"])),
        )

    @staticmethod
    def _decode_revision(value: object) -> int:
        if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
            raise ValueError
        return int(Decimal(value))

    @staticmethod
    def _decode_integer(value: object) -> int:
        if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
            raise ValueError
        # Decimal conversion is exact and avoids Python's int/str digit threshold.
        return int(Decimal(value))

    @staticmethod
    def _validate_id(value: UUID) -> None:
        if not isinstance(value, UUID):
            raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")

    @staticmethod
    def _validate_run_type(value: RunType) -> None:
        if not isinstance(value, RunType):
            raise_validation_error(
                ("run_type",),
                "invalid_run_type",
                f"Run type must be a RunType member: {', '.join(RunType)}.",
            )

    @staticmethod
    def _validate_sections(sections: tuple[Section, ...]) -> None:
        if not isinstance(sections, tuple) or not sections:
            raise_validation_error(
                ("sections",),
                "invalid_sections",
                "Supply an immutable tuple with at least one ordered section.",
            )
        for index, section in enumerate(sections):
            if not isinstance(section, Section):
                raise_validation_error(
                    ("sections", index), "invalid_section", "Supply a Section value."
                )

    @staticmethod
    def _validate_note(note: str | None, field: str) -> None:
        if note is not None and not isinstance(note, str):
            raise_validation_error(
                (field,), "invalid_note", "Note must be plain text or absent."
            )
        if note is not None and (not note or note.strip() != note):
            raise_validation_error(
                (field,),
                "invalid_note",
                "Notes must be trimmed and nonblank, or absent.",
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
