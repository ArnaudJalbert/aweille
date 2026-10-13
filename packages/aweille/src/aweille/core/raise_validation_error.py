from typing import NoReturn

from .errors.validation_error import ValidationError, ValidationProblem


def raise_validation_error(
    field_path: tuple[str | int, ...], code: str, message: str
) -> NoReturn:
    raise ValidationError(ValidationProblem(field_path, code, message))
