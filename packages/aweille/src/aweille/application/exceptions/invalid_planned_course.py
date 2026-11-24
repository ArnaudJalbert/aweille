from aweille.domain import ValidationProblem

from .application_error import ApplicationError


class InvalidPlannedCourse(ApplicationError):
    """Input violates planned-course rules; problems keep the domain field paths."""

    def __init__(self, problems: tuple[ValidationProblem, ...]) -> None:
        self.problems = problems
        super().__init__(problems[0].message)
