"""Encode planned courses as canonical SQLite rows and decode them back."""

import json
import re
from collections.abc import Mapping
from dataclasses import fields
from datetime import date, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from aweille.domain import CourseType, Distance, Pace, PlannedCourse, Section
from aweille.domain.normalize_note import normalize_note


def encode_planned_course_row(planned_course: PlannedCourse) -> dict[str, str | None]:
    """Encode a planned course as canonical column values.

    Args:
        planned_course: Validated, normalized planned course.

    Returns:
        A fresh mapping of column names to canonical UUID, date, and time strings,
        JSON sections with decimal-digit metre and pace strings, optional notes,
        and a decimal-digit revision.
    """
    return {
        "id": str(planned_course.id),
        "planned_date": planned_course.planned_date.isoformat(),
        "planned_start_time": planned_course.planned_start_time.isoformat(
            timespec="minutes"
        )
        if planned_course.planned_start_time is not None
        else None,
        "course_type": planned_course.course_type.value,
        "sections": json.dumps(
            [
                {
                    "distance_m": str(Decimal(section.distance.metres)),
                    "target_pace_seconds_per_km": str(
                        Decimal(section.target_pace.seconds_per_km)
                    ),
                }
                for section in planned_course.sections
            ]
        ),
        "user_note": planned_course.user_note,
        "trainer_note": planned_course.trainer_note,
        "revision": str(Decimal(planned_course.revision)),
    }


def decode_planned_course_row(row: Mapping[str, Any]) -> PlannedCourse:
    """Decode canonical column values into a planned course.

    Args:
        row: Every column in the representation produced by
            encode_planned_course_row.

    Returns:
        The validated planned course, preserving exact ordered targets.

    Raises:
        ValueError: The encoded shape or a scalar representation is invalid, a
            note is not normalized, or decoded values violate domain invariants.
    """
    data = dict(row)
    try:
        _ensure_columns(data)
        planned_course = _planned_course(data)
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        raise ValueError("Encoded planned-course data is invalid.") from None
    if encode_planned_course_row(planned_course) != data:
        raise ValueError("Encoded planned-course data is invalid.")
    return planned_course


def _ensure_columns(data: dict[str, Any]) -> None:
    if data.keys() != {field.name for field in fields(PlannedCourse)}:
        raise ValueError
    for note in (data["user_note"], data["trainer_note"]):
        if normalize_note(note) != note:
            raise ValueError


def _planned_course(data: dict[str, Any]) -> PlannedCourse:
    return PlannedCourse(
        id=UUID(data["id"]),
        planned_date=date.fromisoformat(data["planned_date"]),
        planned_start_time=time.fromisoformat(data["planned_start_time"])
        if data["planned_start_time"] is not None
        else None,
        course_type=CourseType(data["course_type"]),
        sections=_sections(json.loads(data["sections"])),
        user_note=data["user_note"],
        trainer_note=data["trainer_note"],
        revision=decode_positive_integer(data["revision"]),
    )


def _sections(values: object) -> tuple[Section, ...]:
    if not isinstance(values, list):
        raise ValueError
    return tuple(_section(value) for value in values)


def _section(value: object) -> Section:
    if not isinstance(value, dict) or value.keys() != {
        "distance_m",
        "target_pace_seconds_per_km",
    }:
        raise ValueError
    return Section(
        Distance(decode_integer(value["distance_m"])),
        Pace(decode_integer(value["target_pace_seconds_per_km"])),
    )


def decode_positive_integer(value: object) -> int:
    """Decode a canonical positive decimal-digit string, such as a revision.

    Raises:
        ValueError: The value is not a canonical positive decimal-digit string.
    """
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]*", value) is None:
        raise ValueError
    return int(Decimal(value))


def decode_integer(value: object) -> int:
    """Decode a canonical whole-number decimal-digit string, such as a target.

    Raises:
        ValueError: The value is not a canonical decimal-digit string.
    """
    if not isinstance(value, str) or re.fullmatch(r"0|[1-9][0-9]*", value) is None:
        raise ValueError
    # Decimal conversion is exact and avoids Python's int/str digit threshold.
    return int(Decimal(value))
