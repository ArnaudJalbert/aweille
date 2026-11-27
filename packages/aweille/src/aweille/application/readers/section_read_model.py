from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SectionReadModel:
    """One ordered section as plain values.

    Args:
        metres: Distance in whole metres.
        seconds_per_km: Target pace in whole seconds per kilometre.
    """

    metres: int
    seconds_per_km: int
