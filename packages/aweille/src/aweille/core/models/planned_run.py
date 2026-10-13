from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from .run_type import RunType
from .section import Section


@dataclass(frozen=True)
class PlannedRun:
    id: UUID
    planned_date: date
    planned_start_time: time | None
    run_type: RunType
    sections: tuple[Section, ...]
    user_note: str | None
    trainer_note: str | None
