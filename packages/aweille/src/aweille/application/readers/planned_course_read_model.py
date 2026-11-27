from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from .section_read_model import SectionReadModel


@dataclass(frozen=True, slots=True)
class PlannedCourseReadModel:
    """A saved planned course as plain values, read without building an entity.

    Args:
        id: Planned course UUID.
        planned_date: Montreal calendar date.
        planned_start_time: Optional naive Montreal clock time.
        course_type: Course type value, such as "easy".
        sections: Ordered sections.
        user_note: Optional user note.
        trainer_note: Optional trainer note.
        revision: Current positive revision.
    """

    id: UUID
    planned_date: date
    planned_start_time: time | None
    course_type: str
    sections: tuple[SectionReadModel, ...]
    user_note: str | None
    trainer_note: str | None
    revision: int
