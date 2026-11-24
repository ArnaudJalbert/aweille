from dataclasses import replace
from datetime import date, time
from typing import Any

import pytest
from aweille.core import (
    PlannedCourseRevisionConflict,
    PlannedCourseStorage,
    ValidationError,
    create_planned_course,
    read_planned_course,
    update_planned_course,
)


def test_partial_edit_increments_revision_and_retry_matches_current_content(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    original, _ = create_planned_course(storage, **planned_course_input)
    changed = update_planned_course(
        storage, id=original.id, expected_revision=1, user_note="  edited  "
    )
    assert changed.revision == 2
    assert changed.user_note == "edited"
    assert changed.sections == original.sections
    assert read_planned_course(storage, id=original.id) == changed
    with pytest.raises(PlannedCourseRevisionConflict):
        update_planned_course(
            storage, id=original.id, expected_revision=1, user_note="edited"
        )
    assert (
        update_planned_course(
            storage, id=original.id, expected_revision=2, user_note=" edited "
        )
        == changed
    )
    retry_input: dict[str, Any] = {**planned_course_input, "user_note": "edited"}
    assert create_planned_course(storage, **retry_input) == (changed, False)


def test_complete_result_validation_precedes_replacement(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    original, _ = create_planned_course(
        storage, **planned_course_input, planned_start_time=time(2, 30)
    )
    with pytest.raises(ValidationError) as failure:
        update_planned_course(
            storage, id=original.id, expected_revision=1, planned_date=date(2026, 3, 8)
        )
    assert failure.value.problems[0].loc == ("planned_start_time",)
    assert read_planned_course(storage, id=original.id) == original
    changed = update_planned_course(
        storage,
        id=original.id,
        expected_revision=1,
        planned_date=date(2026, 3, 8),
        planned_start_time=None,
    )
    assert changed.revision == 2
    assert changed.planned_start_time is None


@pytest.mark.parametrize("invalid", [False, 0, "1", 1.0])
def test_expected_revision_requires_positive_integer(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any], invalid: Any
) -> None:
    original, _ = create_planned_course(storage, **planned_course_input)
    with pytest.raises(ValidationError) as failure:
        update_planned_course(storage, id=original.id, expected_revision=invalid)
    assert failure.value.problems[0].loc == ("expected_revision",)


def test_exact_huge_revision_round_trip(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    planned_course, _ = create_planned_course(storage, **planned_course_input)
    huge = 10**5000
    saved = replace(planned_course, revision=huge)
    assert saved.to_dict()["revision"] == "1" + "0" * 5000
    assert type(saved).from_dict(saved.to_dict()) == saved
