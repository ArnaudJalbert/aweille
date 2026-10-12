from .validation_problem import ValidationProblem


class ValidationError(ValueError):
    """Safe field problems, without transport prefixes or raw input values."""

    def __init__(self, problem: ValidationProblem) -> None:
        self.problems = (problem,)
        super().__init__(problem.message)
