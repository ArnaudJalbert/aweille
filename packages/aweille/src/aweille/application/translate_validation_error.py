"""Translate domain validation errors raised inside a use case."""

from collections.abc import Generator
from contextlib import contextmanager

from aweille.domain import ValidationError

from .exceptions.invalid_planned_course import InvalidPlannedCourse


@contextmanager
def translate_validation_error() -> Generator[None]:
    """Raise a domain ValidationError as InvalidPlannedCourse with the same problems.

    Raises:
        InvalidPlannedCourse: The wrapped code raised a domain ValidationError.
    """
    try:
        yield
    except ValidationError as error:
        raise InvalidPlannedCourse(error.problems) from error
