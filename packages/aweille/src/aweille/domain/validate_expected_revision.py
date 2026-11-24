from .raise_validation_error import raise_validation_error


def validate_expected_revision(expected_revision: int) -> None:
    if type(expected_revision) is not int or expected_revision < 1:
        raise_validation_error(
            ("expected_revision",),
            "invalid_revision",
            "Revision must be a positive integer.",
        )
