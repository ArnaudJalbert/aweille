from typing import Any

import pytest
from aweille.domain import Distance, Pace, Section, ValidationError


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [("distance", 1000, "invalid_distance"), ("target_pace", 390, "invalid_pace")],
)
def test_section_requires_validated_values(field: str, value: Any, code: str) -> None:
    values: dict[str, Any] = {"distance": Distance(1000), "target_pace": Pace(390)}
    values[field] = value

    with pytest.raises(ValidationError) as failure:
        Section(**values)

    assert failure.value.problems[0].loc == (field,)
    assert failure.value.problems[0].code == code
