from dataclasses import dataclass

from ..raise_validation_error import raise_validation_error


@dataclass(frozen=True)
class Pace:
    """An exact positive target pace in whole seconds per kilometre.

    Args:
        seconds_per_km: Positive integer seconds per kilometre, with no domain
            upper limit.

    Raises:
        ValidationError: Seconds per kilometre are not a positive integer.
            Booleans, floats, Decimal values, and strings are rejected.
    """

    seconds_per_km: int

    def __post_init__(self) -> None:
        if type(self.seconds_per_km) is not int or self.seconds_per_km <= 0:
            raise_validation_error(
                ("seconds_per_km",),
                "invalid_pace",
                "Target pace must be a positive whole number of seconds per kilometre.",
            )
