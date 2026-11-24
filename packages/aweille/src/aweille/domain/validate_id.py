from uuid import UUID

from .raise_validation_error import raise_validation_error


def validate_id(value: UUID) -> None:
    if not isinstance(value, UUID):
        raise_validation_error(("id",), "invalid_id", "ID must be a UUID.")
