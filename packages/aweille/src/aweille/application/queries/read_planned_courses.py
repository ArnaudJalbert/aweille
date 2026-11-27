from dataclasses import dataclass
from datetime import date, time

from aweille.domain.raise_validation_error import raise_validation_error
from aweille.domain.validate_date import validate_date

from ..readers.planned_course_read_model import PlannedCourseReadModel
from ..readers.planned_course_reader import PlannedCourseReader
from ..translate_validation_error import translate_validation_error


class ReadPlannedCoursesQuery:
    """Read planned courses in a Montreal calendar-date range."""

    @dataclass(frozen=True, slots=True)
    class InputData:
        """The half-open date range to read.

        Args:
            start: First included Montreal calendar date.
            end: First excluded Montreal calendar date, later than start.
        """

        start: date
        end: date

    @dataclass(frozen=True, slots=True)
    class OutputData:
        """The planned courses in the range, in schedule order."""

        planned_courses: tuple[PlannedCourseReadModel, ...]

    def __init__(self, reader: PlannedCourseReader) -> None:
        self._reader = reader

    @translate_validation_error()
    def execute(self, input_data: InputData) -> OutputData:
        """Read planned courses in a Montreal calendar-date range.

        Validate the range before reading. Use planned local dates without
        converting them to UTC or rounding the range to week boundaries.

        Args:
            input_data: The half-open date range.

        Returns:
            All matching planned courses, ordered by planned date, then start time
            with untimed planned courses last within each day, then canonical UUID
            string. The tuple is empty when the range contains none.

        Raises:
            InvalidPlannedCourse: A boundary is not a calendar date or end is not
                later than start. The error identifies the invalid range field.
            StorageUnavailable: Storage is temporarily unavailable. The caller may
                retry.
            StorageFailure: An unexpected storage failure prevents the read.
        """
        self._validate_range(input_data.start, input_data.end)
        planned_courses = self._reader.read_range(input_data.start, input_data.end)
        return self.OutputData(
            planned_courses=tuple(sorted(planned_courses, key=self._to_schedule_key))
        )

    @staticmethod
    def _validate_range(start: date, end: date) -> None:
        validate_date(start, "start")
        validate_date(end, "end")
        if end <= start:
            raise_validation_error(
                ("end",), "invalid_range", "End date must be later than start date."
            )

    @staticmethod
    def _to_schedule_key(
        planned_course: PlannedCourseReadModel,
    ) -> tuple[date, bool, time, str]:
        return (
            planned_course.planned_date,
            planned_course.planned_start_time is None,
            planned_course.planned_start_time or time.min,
            str(planned_course.id),
        )
