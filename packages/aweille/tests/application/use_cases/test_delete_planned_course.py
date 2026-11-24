from dataclasses import replace
from typing import Any
from unittest.mock import create_autospec
from uuid import UUID

import pytest
from aweille.application import (
    DeletePlannedCourseCommand,
    InvalidPlannedCourse,
    PlannedCourseNotFound,
    PlannedCourseRepository,
    PlannedCourseRevisionConflict,
    StorageFailure,
    StorageUnavailable,
)


@pytest.fixture
def repository() -> Any:
    return create_autospec(PlannedCourseRepository, instance=True)


@pytest.fixture
def command(repository: Any) -> DeletePlannedCourseCommand:
    return DeletePlannedCourseCommand(repository)


@pytest.fixture
def input_data() -> DeletePlannedCourseCommand.InputData:
    return DeletePlannedCourseCommand.InputData(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"), expected_revision=2
    )


def test_deletion_removes_the_planned_course_at_its_revision(
    command: DeletePlannedCourseCommand,
    repository: Any,
    input_data: DeletePlannedCourseCommand.InputData,
) -> None:
    """Deletion asks the repository to remove the ID at the expected revision."""
    assert command.execute(input_data) == DeletePlannedCourseCommand.OutputData()

    repository.delete.assert_called_once_with(input_data.id, expected_revision=2)


@pytest.mark.parametrize(
    ("changes", "field_path"),
    [
        ({"id": "54d97d4d-fadb-4d50-926e-af1bb26c711a"}, ("id",)),
        ({"expected_revision": 0}, ("expected_revision",)),
        ({"expected_revision": True}, ("expected_revision",)),
    ],
)
def test_invalid_deletion_is_rejected_before_deleting(
    command: DeletePlannedCourseCommand,
    repository: Any,
    input_data: DeletePlannedCourseCommand.InputData,
    changes: dict[str, Any],
    field_path: tuple[str, ...],
) -> None:
    """An invalid ID or revision reports its field and deletes nothing."""
    with pytest.raises(InvalidPlannedCourse) as failure:
        command.execute(replace(input_data, **changes))

    assert failure.value.problems[0].loc == field_path
    repository.delete.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        PlannedCourseNotFound(),
        PlannedCourseRevisionConflict(),
        StorageUnavailable("Storage unavailable."),
        StorageFailure("Storage failed."),
    ],
)
def test_repository_failures_reach_the_caller(
    command: DeletePlannedCourseCommand,
    repository: Any,
    input_data: DeletePlannedCourseCommand.InputData,
    error: Exception,
) -> None:
    """Missing, stale and storage failures keep their category."""
    repository.delete.side_effect = error

    with pytest.raises(type(error)) as reported:
        command.execute(input_data)

    assert reported.value is error
