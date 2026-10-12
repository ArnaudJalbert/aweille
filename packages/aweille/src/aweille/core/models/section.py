from dataclasses import dataclass


@dataclass(frozen=True)
class Section:
    distance_m: int
    target_pace_seconds_per_km: int
