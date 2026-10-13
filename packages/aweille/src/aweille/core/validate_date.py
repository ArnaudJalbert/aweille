from datetime import date

from .raise_validation_error import raise_validation_error


def validate_date(value: date, field: str) -> None:
    if type(value) is not date:
        raise_validation_error(
            (field,), "invalid_date", "Supply a calendar date without a time."
        )
