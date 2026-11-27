from dataclasses import dataclass, replace
from datetime import date, time
from uuid import UUID

from aweille.domain import CourseType, Distance, Pace, PlannedCourse, Section
from aweille.domain.normalize_note import normalize_note
from aweille.domain.normalize_start_time import normalize_start_time

from ..exceptions.planned_course_conflict import PlannedCourseConflict
from ..readers.section_read_model import SectionReadModel
from ..repositories.planned_course_repository import PlannedCourseRepository
from ..translate_validation_error import translate_validation_error


class CreatePlannedCourseCommand:
    """Create a planned course, or return the saved one for an identical retry."""

    @dataclass(frozen=True, slots=True)
    class InputData:
        """Plain creation values.

        Args:
            id: Caller-supplied UUID, reused when retrying the same creation.
            planned_date: Montreal calendar date. Past and future dates are allowed.
            course_type: Course type value, such as "easy".
            sections: Non-empty ordered sections.
            planned_start_time: Naive Montreal clock time with minute precision,
                or None for no start time.
            user_note: Plain-text note from the user, or None.
            trainer_note: Plain-text note from the trainer, or None.
        """

        @dataclass(frozen=True, slots=True)
        class SectionInput:
            """One ordered section in whole metres and seconds per kilometre."""

            metres: int
            seconds_per_km: int

        id: UUID
        planned_date: date
        course_type: str
        sections: tuple[SectionInput, ...]
        planned_start_time: time | None
        user_note: str | None
        trainer_note: str | None

    @dataclass(frozen=True, slots=True)
    class OutputData:
        """The saved planned course, and whether this call created it."""

        id: UUID
        planned_date: date
        planned_start_time: time | None
        course_type: str
        sections: tuple[SectionReadModel, ...]
        user_note: str | None
        trainer_note: str | None
        revision: int
        created: bool

    def __init__(self, repository: PlannedCourseRepository) -> None:
        self._repository = repository

    @translate_validation_error()
    def execute(self, input_data: InputData) -> OutputData:
        """Validate and create a planned course, or return an identical retry.

        Validate and normalize all fields before saving. Preserve section order and
        repeated entries. Trim notes and treat blank notes as absent. Reject a
        spring-forward gap start time; allow fall-back ambiguity without selecting
        an occurrence.

        Args:
            input_data: The planned course to create.

        Returns:
            The saved planned course. created is True only after a new planned
            course is committed; an identical retry returns the saved one with
            created False.

        Raises:
            InvalidPlannedCourse: A field violates the domain rules. The error
                reports a safe field path, code, and message.
            PlannedCourseConflict: The ID belongs to a planned course with
                different normalized data, or to a deleted one.
            StorageUnavailable: Storage is temporarily unavailable. The caller may
                retry with the same ID.
            StorageFailure: An unexpected storage failure prevents the operation.
        """
        planned_course = PlannedCourse(
            id=input_data.id,
            planned_date=input_data.planned_date,
            planned_start_time=normalize_start_time(input_data.planned_start_time),
            course_type=CourseType.parse(input_data.course_type),
            sections=self._to_sections(input_data.sections),
            user_note=normalize_note(input_data.user_note),
            trainer_note=normalize_note(input_data.trainer_note),
        )
        saved, created = self._repository.save(planned_course)
        if not created:
            self._ensure_retry_matches(planned_course, saved)
        return self._to_output_data(saved, created)

    @staticmethod
    def _to_sections(
        sections: tuple[InputData.SectionInput, ...],
    ) -> tuple[Section, ...]:
        return tuple(
            Section(Distance(section.metres), Pace(section.seconds_per_km))
            for section in sections
        )

    @staticmethod
    def _ensure_retry_matches(proposed: PlannedCourse, saved: PlannedCourse) -> None:
        if replace(proposed, revision=saved.revision) != saved:
            raise PlannedCourseConflict(
                "The ID already belongs to a different planned course."
            )

    @classmethod
    def _to_output_data(
        cls, planned_course: PlannedCourse, created: bool
    ) -> OutputData:
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
            created=created,
        )
