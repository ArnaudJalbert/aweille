from typing import NoReturn

from .errors.validation_error import ValidationError, ValidationProblem


def raise_validation_error(
    loc: tuple[str | int, ...], code: str, message: str
) -> NoReturn:
    raise ValidationError(ValidationProblem(loc, code, message))
