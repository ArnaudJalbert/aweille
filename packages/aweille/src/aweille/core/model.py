from dataclasses import dataclass
from datetime import date, time
from decimal import Decimal
from typing import Literal
from uuid import UUID

type RunType = Literal["easy", "hard", "interval", "long"]


@dataclass(frozen=True)
class SectionInput:
    distance_km: Decimal
    target_pace_seconds_per_km: int


@dataclass(frozen=True)
class Section:
    distance_m: int
    target_pace_seconds_per_km: int


@dataclass(frozen=True)
class PlannedRun:
    id: UUID
    planned_date: date
    planned_start_time: time | None
    run_type: RunType
    sections: tuple[Section, ...]
    user_note: str | None
    trainer_note: str | None
