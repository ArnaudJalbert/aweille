from dataclasses import dataclass

from ..raise_validation_error import raise_validation_error


@dataclass(frozen=True)
class Distance:
    """An exact positive distance in whole metres.

    Args:
        metres: Positive integer metres, with no domain upper limit.

    Raises:
        ValidationError: Metres are not a positive integer. Booleans, floats,
            Decimal values, and strings are rejected without coercion.
    """

    metres: int

    def __post_init__(self) -> None:
        if type(self.metres) is not int or self.metres <= 0:
            raise_validation_error(
                ("metres",),
                "invalid_distance",
                "Distance must be a positive whole number of metres.",
            )
