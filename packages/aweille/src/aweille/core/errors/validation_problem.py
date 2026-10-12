from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationProblem:
    loc: tuple[str | int, ...]
    code: str
    message: str
