from dataclasses import dataclass

from .distance import Distance
from .pace import Pace


@dataclass(frozen=True)
class Section:
    """One ordered section with validated distance and target pace.

    Args:
        distance: Distance in whole metres.
        target_pace: Target pace in whole seconds per kilometre.
    """

    distance: Distance
    target_pace: Pace
