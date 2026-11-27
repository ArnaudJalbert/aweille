from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from aweille.domain.validate_id import validate_id

from ..exceptions.planned_course_not_found import PlannedCourseNotFound
from ..readers.planned_course_read_model import PlannedCourseReadModel
from ..readers.planned_course_reader import PlannedCourseReader
from ..readers.section_read_model import SectionReadModel
from ..translate_validation_error import translate_validation_error


class ReadPlannedCourseQuery:
    """Read one saved planned course by UUID."""

    @dataclass(frozen=True, slots=True)
    class InputData:
        """The planned course to read.

        Args:
            id: UUID of the planned course to read.
        """

        id: UUID

    @dataclass(frozen=True, slots=True)
    class OutputData:
        """The saved planned course and its current revision."""

        id: UUID
        planned_date: date
        planned_start_time: time | None
        course_type: str
        sections: tuple[SectionReadModel, ...]
        user_note: str | None
        trainer_note: str | None
        revision: int

    def __init__(self, reader: PlannedCourseReader) -> None:
        self._reader = reader

    @translate_validation_error()
    def execute(self, input_data: InputData) -> OutputData:
        """Read a planned course by UUID.

        Args:
            input_data: The planned course to read.

        Returns:
            The saved planned course with its current revision.

        Raises:
            InvalidPlannedCourse: The ID is not a UUID.
            PlannedCourseNotFound: No planned course exists for the UUID.
            StorageUnavailable: Storage is temporarily unavailable.
            StorageFailure: Storage cannot read or decode the planned course.
        """
        validate_id(input_data.id)
        planned_course = self._reader.read(input_data.id)
        if planned_course is None:
            raise PlannedCourseNotFound
        return self._to_output_data(planned_course)

    @classmethod
    def _to_output_data(cls, planned_course: PlannedCourseReadModel) -> OutputData:
        return cls.OutputData(
            id=planned_course.id,
            planned_date=planned_course.planned_date,
            planned_start_time=planned_course.planned_start_time,
            course_type=planned_course.course_type,
            sections=planned_course.sections,
            user_note=planned_course.user_note,
            trainer_note=planned_course.trainer_note,
            revision=planned_course.revision,
        )
