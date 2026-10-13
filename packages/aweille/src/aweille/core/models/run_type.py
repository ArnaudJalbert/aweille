from enum import StrEnum


class RunType(StrEnum):
    """The supported planned-run types and their transport values."""

    EASY = "easy"
    HARD = "hard"
    INTERVAL = "interval"
    LONG = "long"
