from datetime import date
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from aweille.core import (
    PlannedCourseConflict,
    PlannedCourseNotFound,
    PlannedCourseRevisionConflict,
    PlannedCourseStorage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_planned_course,
    delete_planned_course,
    read_planned_course,
    read_planned_courses,
    update_planned_course,
)


def test_deletion_removes_planned_course_and_reserves_identity(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    saved, _ = create_planned_course(storage, **planned_course_input)
    assert delete_planned_course(storage, id=saved.id, expected_revision=1) is None
    assert (
        read_planned_courses(storage, start=date(2026, 1, 1), end=date(2027, 1, 1))
        == []
    )
    for operation in (
        lambda: read_planned_course(storage, id=saved.id),
        lambda: delete_planned_course(storage, id=saved.id, expected_revision=1),
        lambda: update_planned_course(storage, id=saved.id, expected_revision=1),
        lambda: delete_planned_course(storage, id=uuid4(), expected_revision=1),
    ):
        with pytest.raises(PlannedCourseNotFound):
            operation()
    with pytest.raises(PlannedCourseConflict):
        create_planned_course(storage, **planned_course_input)


def test_stale_deletion_keeps_current_workout(
    storage: PlannedCourseStorage, planned_course_input: dict[str, Any]
) -> None:
    saved, _ = create_planned_course(storage, **planned_course_input)
    current = update_planned_course(
        storage, id=saved.id, expected_revision=1, trainer_note="new"
    )
    with pytest.raises(PlannedCourseRevisionConflict):
        delete_planned_course(storage, id=saved.id, expected_revision=1)
    assert read_planned_course(storage, id=saved.id) == current


@pytest.mark.parametrize(
    "changes,location",
    [
        ({"id": "private"}, ("id",)),
        *[
            ({"expected_revision": value}, ("expected_revision",))
            for value in (False, 0, -1, "1", 1.0)
        ],
    ],
)
def test_invalid_deletion_is_rejected_before_storage(changes, location) -> None:
    storage = Mock(spec=PlannedCourseStorage)
    with pytest.raises(ValidationError) as failure:
        delete_planned_course(
            storage, **({"id": uuid4(), "expected_revision": 1} | changes)
        )
    assert failure.value.problems[0].loc == location
    assert storage.mock_calls == []


@pytest.mark.parametrize("error", [StorageFailure, StorageUnavailable])
def test_deletion_preserves_storage_failure_category(error) -> None:
    storage = Mock(spec=PlannedCourseStorage)
    storage.delete.side_effect = error("Safe failure")
    with pytest.raises(error, match="Safe failure"):
        delete_planned_course(storage, id=uuid4(), expected_revision=1)
