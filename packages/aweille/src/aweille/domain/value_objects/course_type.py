from enum import StrEnum


class CourseType(StrEnum):
    """The supported planned-course types and their transport values."""

    EASY = "easy"
    HARD = "hard"
    INTERVAL = "interval"
    LONG = "long"
