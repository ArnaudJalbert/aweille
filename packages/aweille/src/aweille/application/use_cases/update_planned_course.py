from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date, time
from enum import Enum
from uuid import UUID

from aweille.domain import CourseType, Distance, Pace, PlannedCourse, Section
from aweille.domain.normalize_note import normalize_note
from aweille.domain.normalize_start_time import normalize_start_time
from aweille.domain.validate_expected_revision import validate_expected_revision
from aweille.domain.validate_id import validate_id

from ..exceptions.planned_course_not_found import PlannedCourseNotFound
from ..exceptions.planned_course_revision_conflict import PlannedCourseRevisionConflict
from ..readers.section_read_model import SectionReadModel
from ..repositories.planned_course_repository import PlannedCourseRepository
from ..translate_validation_error import translate_validation_error


class Unchanged(Enum):
    """Marks an editable field the caller leaves as saved."""

    UNCHANGED = "unchanged"


class UpdatePlannedCourseCommand:
    """Replace the supplied fields of a planned course at its expected revision."""

    @dataclass(frozen=True, slots=True)
    class InputData:
        """The planned course to edit and the fields to replace.

        Each editable field defaults to Unchanged.UNCHANGED, which keeps the saved
        value. None clears the start time or a note.

        Args:
            id: Saved planned course UUID.
            expected_revision: Positive integer revision read by the caller.
            planned_date: New Montreal calendar date.
            planned_start_time: New start time, or None to clear it.
            course_type: New course type value, such as "easy".
            sections: Complete replacement of the ordered sections.
            user_note: New user note, or None to clear it.
            trainer_note: New trainer note, or None to clear it.
        """

        @dataclass(frozen=True, slots=True)
        class SectionInput:
            """One ordered section in whole metres and seconds per kilometre."""

            metres: int
            seconds_per_km: int

        id: UUID
        expected_revision: int
        planned_date: date | Unchanged = Unchanged.UNCHANGED
        planned_start_time: time | None | Unchanged = Unchanged.UNCHANGED
        course_type: str | Unchanged = Unchanged.UNCHANGED
        sections: tuple[SectionInput, ...] | Unchanged = Unchanged.UNCHANGED
        user_note: str | None | Unchanged = Unchanged.UNCHANGED
        trainer_note: str | None | Unchanged = Unchanged.UNCHANGED

    @dataclass(frozen=True, slots=True)
    class OutputData:
        """The committed planned course and its current revision."""

        id: UUID
        planned_date: date
        planned_start_time: time | None
        course_type: str
        sections: tuple[SectionReadModel, ...]
        user_note: str | None
        trainer_note: str | None
        revision: int

    def __init__(self, repository: PlannedCourseRepository) -> None:
        self._repository = repository

    @translate_validation_error()
    def execute(self, input_data: InputData) -> OutputData:
        """Replace supplied fields if the saved revision still matches.

        Changed normalized content increments the revision; a no-op keeps it.

        Args:
            input_data: The planned course, its expected revision and the changes.

        Returns:
            The committed planned course, unchanged on a no-op.

        Raises:
            InvalidPlannedCourse: The ID, the revision or the resulting planned
                course is invalid.
            PlannedCourseNotFound: The planned course is absent.
            PlannedCourseRevisionConflict: A newer revision exists.
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage failed; a possible commit remains uncertain.
        """
        validate_id(input_data.id)
        validate_expected_revision(input_data.expected_revision)
        current = self._load_current(input_data.id, input_data.expected_revision)
        candidate = self._candidate(current, input_data)
        saved = self._repository.replace(
            candidate, expected_revision=input_data.expected_revision
        )
        return self._output(saved)

    def _load_current(self, id: UUID, expected_revision: int) -> PlannedCourse:
        current = self._repository.load(id)
        if current is None:
            raise PlannedCourseNotFound
        if current.revision != expected_revision:
            raise PlannedCourseRevisionConflict
        return current

    @classmethod
    def _candidate(cls, current: PlannedCourse, input_data: InputData) -> PlannedCourse:
        return replace(
            current,
            planned_date=_supplied_or(
                input_data.planned_date, current.planned_date, _same
            ),
            planned_start_time=_supplied_or(
                input_data.planned_start_time,
                current.planned_start_time,
                normalize_start_time,
            ),
            course_type=_supplied_or(
                input_data.course_type, current.course_type, CourseType.parse
            ),
            sections=_supplied_or(input_data.sections, current.sections, cls._sections),
            user_note=_supplied_or(
                input_data.user_note, current.user_note, normalize_note
            ),
            trainer_note=_supplied_or(
                input_data.trainer_note, current.trainer_note, normalize_note
            ),
        )

    @staticmethod
    def _sections(sections: tuple[InputData.SectionInput, ...]) -> tuple[Section, ...]:
        return tuple(
            Section(Distance(section.metres), Pace(section.seconds_per_km))
            for section in sections
        )

    @classmethod
    def _output(cls, planned_course: PlannedCourse) -> OutputData:
        return cls.OutputData(
            id=planned_course.id,
            planned_date=planned_course.planned_date,
            planned_start_time=planned_course.planned_start_time,
            course_type=planned_course.course_type.value,
            sections=tuple(
                SectionReadModel(
                    metres=section.distance.metres,
                    seconds_per_km=section.target_pace.seconds_per_km,
                )
                for section in planned_course.sections
            ),
            user_note=planned_course.user_note,
            trainer_note=planned_course.trainer_note,
            revision=planned_course.revision,
        )


def _supplied_or[Supplied, Saved](
    value: Supplied | Unchanged, saved: Saved, convert: Callable[[Supplied], Saved]
) -> Saved:
    """Return the converted supplied value, or the saved one when unchanged."""
    return saved if isinstance(value, Unchanged) else convert(value)


def _same[Value](value: Value) -> Value:
    return value
