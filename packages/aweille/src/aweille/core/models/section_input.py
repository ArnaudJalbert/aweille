from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class SectionInput:
    distance_km: Decimal
    target_pace_seconds_per_km: int
