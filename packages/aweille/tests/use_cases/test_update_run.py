from dataclasses import replace
from datetime import date, time
from typing import Any

import pytest
from aweille.core import (
    RunRevisionConflict,
    RunStorage,
    ValidationError,
    create_run,
    read_run,
    update_run,
)


def test_partial_edit_increments_revision_and_retry_matches_current_content(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    original, _ = create_run(storage, **run_input)
    changed = update_run(
        storage, id=original.id, expected_revision=1, user_note="  edited  "
    )
    assert changed.revision == 2
    assert changed.user_note == "edited"
    assert changed.sections == original.sections
    assert read_run(storage, id=original.id) == changed
    with pytest.raises(RunRevisionConflict):
        update_run(storage, id=original.id, expected_revision=1, user_note="edited")
    assert (
        update_run(storage, id=original.id, expected_revision=2, user_note=" edited ")
        == changed
    )
    retry_input: dict[str, Any] = {**run_input, "user_note": "edited"}
    assert create_run(storage, **retry_input) == (changed, False)


def test_complete_result_validation_precedes_replacement(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    original, _ = create_run(storage, **run_input, planned_start_time=time(2, 30))
    with pytest.raises(ValidationError) as failure:
        update_run(
            storage, id=original.id, expected_revision=1, planned_date=date(2026, 3, 8)
        )
    assert failure.value.problems[0].loc == ("planned_start_time",)
    assert read_run(storage, id=original.id) == original
    changed = update_run(
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
    storage: RunStorage, run_input: dict[str, Any], invalid: Any
) -> None:
    original, _ = create_run(storage, **run_input)
    with pytest.raises(ValidationError) as failure:
        update_run(storage, id=original.id, expected_revision=invalid)
    assert failure.value.problems[0].loc == ("expected_revision",)


def test_exact_huge_revision_round_trip(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    run, _ = create_run(storage, **run_input)
    huge = 10**5000
    saved = replace(run, revision=huge)
    assert saved.to_dict()["revision"] == "1" + "0" * 5000
    assert type(saved).from_dict(saved.to_dict()) == saved
