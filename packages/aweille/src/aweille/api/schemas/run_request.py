from datetime import time
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidateAs

from aweille.core import Distance, Pace, RunType, Section

from .request_date import RequestDate

# Decimal preserves exact targets beyond Python's integer-string digit threshold.
_Target = Annotated[
    int,
    ValidateAs(
        Annotated[str, Field(strict=True, pattern=r"^0*[1-9][0-9]*$")],
        lambda value: int(Decimal(value)),
    ),
]
_StartTime = Annotated[
    time,
    ValidateAs(
        Annotated[str, Field(strict=True, pattern=r"^[0-9]{2}:[0-9]{2}$")],
        time.fromisoformat,
    ),
]


class _SectionRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    distance_m: _Target
    target_pace_seconds_per_km: _Target


class RunRequest(BaseModel):
    """Strict creation shape, with encoded scalars parsed into core input types."""

    model_config = ConfigDict(strict=True, extra="forbid")

    id: UUID = Field(strict=False)
    planned_date: RequestDate
    run_type: RunType = Field(strict=False)
    sections: list[_SectionRequest] = Field(min_length=1)
    planned_start_time: _StartTime | None = None
    user_note: str | None = None
    trainer_note: str | None = None

    def core_inputs(self) -> dict[str, Any]:
        """Build validated inputs for the create_run use case.

        Returns:
            Typed run fields and ordered Distance/Pace/Section values.
        """
        return {
            **self.model_dump(exclude={"sections"}),
            "sections": [
                Section(
                    Distance(section.distance_m),
                    Pace(section.target_pace_seconds_per_km),
                )
                for section in self.sections
            ],
        }
