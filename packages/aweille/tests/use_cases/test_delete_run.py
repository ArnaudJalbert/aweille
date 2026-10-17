from datetime import date
from typing import Any
from unittest.mock import Mock
from uuid import uuid4

import pytest
from aweille.core import (
    RunConflict,
    RunNotFound,
    RunRevisionConflict,
    RunStorage,
    StorageFailure,
    StorageUnavailable,
    ValidationError,
    create_run,
    delete_run,
    read_run,
    read_runs,
    update_run,
)


def test_deletion_removes_run_and_reserves_identity(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    saved, _ = create_run(storage, **run_input)
    assert delete_run(storage, id=saved.id, expected_revision=1) is None
    assert read_runs(storage, start=date(2026, 1, 1), end=date(2027, 1, 1)) == []
    for operation in (
        lambda: read_run(storage, id=saved.id),
        lambda: delete_run(storage, id=saved.id, expected_revision=1),
        lambda: update_run(storage, id=saved.id, expected_revision=1),
        lambda: delete_run(storage, id=uuid4(), expected_revision=1),
    ):
        with pytest.raises(RunNotFound):
            operation()
    with pytest.raises(RunConflict):
        create_run(storage, **run_input)


def test_stale_deletion_keeps_current_workout(
    storage: RunStorage, run_input: dict[str, Any]
) -> None:
    saved, _ = create_run(storage, **run_input)
    current = update_run(storage, id=saved.id, expected_revision=1, trainer_note="new")
    with pytest.raises(RunRevisionConflict):
        delete_run(storage, id=saved.id, expected_revision=1)
    assert read_run(storage, id=saved.id) == current


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
    storage = Mock(spec=RunStorage)
    with pytest.raises(ValidationError) as failure:
        delete_run(storage, **({"id": uuid4(), "expected_revision": 1} | changes))
    assert failure.value.problems[0].loc == location
    assert storage.mock_calls == []


@pytest.mark.parametrize("error", [StorageFailure, StorageUnavailable])
def test_deletion_preserves_storage_failure_category(error) -> None:
    storage = Mock(spec=RunStorage)
    storage.delete.side_effect = error("Safe failure")
    with pytest.raises(error, match="Safe failure"):
        delete_run(storage, id=uuid4(), expected_revision=1)
