from decimal import Decimal
from typing import Any

import pytest
from aweille.core import Pace, ValidationError


@pytest.mark.parametrize(
    "seconds_per_km", [0, -1, 390.5, 390.0, Decimal("390"), "390", True]
)
def test_pace_rejects_values_other_than_positive_whole_seconds(
    seconds_per_km: Any,
) -> None:
    with pytest.raises(ValidationError) as failure:
        Pace(seconds_per_km)

    problem = failure.value.problems[0]
    assert problem.loc == ("seconds_per_km",)
    assert problem.code == "invalid_pace"
    assert problem.message == (
        "Target pace must be a positive whole number of seconds per kilometre."
    )
