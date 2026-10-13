import re
from datetime import time
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from pydantic_core import PydanticCustomError

from aweille.core import Distance, Pace, RunType, Section

from .request_date import RequestDate


def _parse_decimal_digits(value: Any) -> int:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]+", value) is None:
        raise PydanticCustomError(
            "invalid_integer", "Supply a positive whole number as decimal-digit text."
        )
    # Preserve exact targets beyond Python's integer-string digit threshold.
    return int(Decimal(value))


def _require_time_format(value: Any) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{2}:[0-9]{2}", value) is None:
        raise PydanticCustomError(
            "invalid_start_time", "Supply a local start time in HH:MM format or null."
        )
    return value


_Target = Annotated[int, Field(gt=0), BeforeValidator(_parse_decimal_digits)]
_StartTime = Annotated[time, Field(strict=False), BeforeValidator(_require_time_format)]


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
            "id": self.id,
            "planned_date": self.planned_date,
            "run_type": self.run_type,
            "sections": [
                Section(
                    Distance(section.distance_m),
                    Pace(section.target_pace_seconds_per_km),
                )
                for section in self.sections
            ],
            "planned_start_time": self.planned_start_time,
            "user_note": self.user_note,
            "trainer_note": self.trainer_note,
        }
