from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

_TargetDigits = Annotated[str, Field(pattern=r"^[1-9][0-9]*$")]


class SectionResponse(BaseModel):
    """Exact canonical distance and pace strings for an ordered section."""

    model_config = ConfigDict(strict=True, extra="forbid")

    distance_m: _TargetDigits
    target_pace_seconds_per_km: _TargetDigits
