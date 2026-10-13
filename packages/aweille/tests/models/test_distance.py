from decimal import Decimal
from typing import Any

import pytest
from aweille.core import Distance, ValidationError


@pytest.mark.parametrize(
    "metres",
    [0, -1, 1.5, 1.0, Decimal("1"), "1000", True],
)
def test_distance_rejects_values_other_than_positive_whole_metres(metres: Any) -> None:
    with pytest.raises(ValidationError) as failure:
        Distance(metres)

    problem = failure.value.problems[0]
    assert problem.loc == ("metres",)
    assert problem.code == "invalid_distance"
    assert problem.message == "Distance must be a positive whole number of metres."
