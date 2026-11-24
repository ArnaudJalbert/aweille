from enum import StrEnum
from typing import Self

from ..raise_validation_error import raise_validation_error


class CourseType(StrEnum):
    """The supported planned-course types and their transport values."""

    EASY = "easy"
    HARD = "hard"
    INTERVAL = "interval"
    LONG = "long"

    @classmethod
    def parse(cls, value: str) -> Self:
        """Return the course type for a transport value.

        Args:
            value: One of the course type values, such as "easy".

        Returns:
            The matching course type.

        Raises:
            ValidationError: The value is not a supported course type.
        """
        if value not in cls._value2member_map_:
            raise_validation_error(
                ("course_type",),
                "invalid_course_type",
                f"Course type must be one of: {', '.join(cls)}.",
            )
        return cls(value)
