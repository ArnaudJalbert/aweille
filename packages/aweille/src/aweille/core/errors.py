from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationProblem:
    loc: tuple[str | int, ...]
    code: str
    message: str


class ValidationError(ValueError):
    """Safe field problems, without transport prefixes or raw input values."""

    def __init__(self, problem: ValidationProblem) -> None:
        self.problems = (problem,)
        super().__init__(problem.message)


class RunConflict(Exception):
    """A committed run already uses this ID with different normalized data."""


class StorageUnavailable(Exception):
    """Temporary contention or unavailability; callers may retry the same ID."""


class StorageFailure(Exception):
    """An unexpected storage failure prevented the operation."""
