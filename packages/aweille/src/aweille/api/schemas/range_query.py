from pydantic import BaseModel, ConfigDict

from .request_date import RequestDate


class RangeQuery(BaseModel):
    """Required calendar-date boundaries with unknown parameters forbidden."""

    model_config = ConfigDict(strict=True, extra="forbid")

    start: RequestDate
    end: RequestDate
