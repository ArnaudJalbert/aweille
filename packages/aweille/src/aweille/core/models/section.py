from dataclasses import dataclass

from ..raise_validation_error import raise_validation_error
from .distance import Distance
from .pace import Pace


@dataclass(frozen=True)
class Section:
    """One ordered section with validated distance and target pace.

    Args:
        distance: Distance in whole metres.
        target_pace: Target pace in whole seconds per kilometre.

    Raises:
        ValidationError: A field is not its required value object.
    """

    distance: Distance
    target_pace: Pace

    def __post_init__(self) -> None:
        if not isinstance(self.distance, Distance):
            raise_validation_error(
                ("distance",), "invalid_distance", "Supply a Distance value."
            )
        if not isinstance(self.target_pace, Pace):
            raise_validation_error(
                ("target_pace",), "invalid_pace", "Supply a Pace value."
            )
