from dataclasses import replace
from datetime import date, time
from typing import Any
from unittest.mock import create_autospec
from uuid import UUID

import pytest
from aweille.application import (
    InvalidPlannedCourse,
    PlannedCourseNotFound,
    PlannedCourseRepository,
    PlannedCourseRevisionConflict,
    SectionReadModel,
    StorageFailure,
    UpdatePlannedCourseCommand,
)
from aweille.domain import CourseType, Distance, Pace, PlannedCourse, Section

SectionInput = UpdatePlannedCourseCommand.InputData.SectionInput


@pytest.fixture
def current() -> PlannedCourse:
    return PlannedCourse(
        id=UUID("54d97d4d-fadb-4d50-926e-af1bb26c711a"),
        planned_date=date(2026, 10, 14),
        planned_start_time=time(7, 30),
        course_type=CourseType.INTERVAL,
        sections=(Section(Distance(1000), Pace(390)),),
        user_note="Keep it easy.",
        trainer_note="Finish relaxed.",
        revision=1,
    )


@pytest.fixture
def repository(current: PlannedCourse) -> Any:
    repository = create_autospec(PlannedCourseRepository, instance=True)
    repository.load.return_value = current
    repository.replace.side_effect = lambda planned_course, *, expected_revision: (
        replace(planned_course, revision=expected_revision + 1)
    )
    return repository


@pytest.fixture
def command(repository: Any) -> UpdatePlannedCourseCommand:
    return UpdatePlannedCourseCommand(repository)


def test_partial_edit_replaces_only_supplied_fields(
    command: UpdatePlannedCourseCommand, repository: Any, current: PlannedCourse
) -> None:
    """Supplied fields are normalized and replaced; omitted fields keep saved values."""
    output = command.execute(
        UpdatePlannedCourseCommand.InputData(
            id=current.id,
            expected_revision=1,
            planned_date=date(2026, 11, 1),
            planned_start_time=time(1, 30, fold=1),
            course_type="long",
            sections=(SectionInput(metres=21097, seconds_per_km=330),),
            user_note="  New note.  ",
        )
    )

    assert output == UpdatePlannedCourseCommand.OutputData(
        id=current.id,
        planned_date=date(2026, 11, 1),
        planned_start_time=time(1, 30),
        course_type="long",
        sections=(SectionReadModel(metres=21097, seconds_per_km=330),),
        user_note="New note.",
        trainer_note="Finish relaxed.",
        revision=2,
    )
    assert output.planned_start_time is not None
    assert output.planned_start_time.fold == 0
    assert repository.replace.call_args.kwargs == {"expected_revision": 1}


def test_none_clears_the_start_time_and_notes(
    command: UpdatePlannedCourseCommand, current: PlannedCourse
) -> None:
    """None clears an optional field, and a blank note clears it too."""
    output = command.execute(
        UpdatePlannedCourseCommand.InputData(
            id=current.id,
            expected_revision=1,
            planned_start_time=None,
            user_note=None,
            trainer_note="   ",
        )
    )

    assert output.planned_start_time is None
    assert output.user_note is None
    assert output.trainer_note is None


def test_missing_planned_course_is_not_found(
    command: UpdatePlannedCourseCommand, repository: Any, current: PlannedCourse
) -> None:
    """Editing an absent planned course reports it missing and writes nothing."""
    repository.load.return_value = None

    with pytest.raises(PlannedCourseNotFound):
        command.execute(
            UpdatePlannedCourseCommand.InputData(id=current.id, expected_revision=1)
        )

    repository.replace.assert_not_called()


def test_stale_revision_is_rejected_before_replacing(
    command: UpdatePlannedCourseCommand, repository: Any, current: PlannedCourse
) -> None:
    """A revision older than the saved one is a stale write and writes nothing."""
    repository.load.return_value = replace(current, revision=2)

    with pytest.raises(PlannedCourseRevisionConflict):
        command.execute(
            UpdatePlannedCourseCommand.InputData(
                id=current.id, expected_revision=1, user_note="lost"
            )
        )

    repository.replace.assert_not_called()


@pytest.mark.parametrize(
    ("changes", "field_path", "code"),
    [
        ({"expected_revision": False}, ("expected_revision",), "invalid_revision"),
        ({"expected_revision": 0}, ("expected_revision",), "invalid_revision"),
        ({"expected_revision": "1"}, ("expected_revision",), "invalid_revision"),
        ({"expected_revision": 1.0}, ("expected_revision",), "invalid_revision"),
        ({"id": "54d97d4d-fadb-4d50-926e-af1bb26c711a"}, ("id",), "invalid_id"),
        ({"course_type": "long_run"}, ("course_type",), "invalid_course_type"),
        ({"sections": ()}, ("sections",), "invalid_sections"),
        (
            {"planned_date": date(2026, 3, 8), "planned_start_time": time(2, 30)},
            ("planned_start_time",),
            "nonexistent_start_time",
        ),
    ],
)
def test_invalid_input_or_resulting_planned_course_is_rejected_before_replacing(
    command: UpdatePlannedCourseCommand,
    repository: Any,
    current: PlannedCourse,
    changes: dict[str, Any],
    field_path: tuple[str | int, ...],
    code: str,
) -> None:
    """Invalid input or an invalid complete result writes nothing."""
    input_data = UpdatePlannedCourseCommand.InputData(
        id=current.id, expected_revision=1
    )

    with pytest.raises(InvalidPlannedCourse) as failure:
        command.execute(replace(input_data, **changes))

    assert failure.value.problems[0].loc == field_path
    assert failure.value.problems[0].code == code
    repository.replace.assert_not_called()


def test_exact_huge_revision_is_kept(
    command: UpdatePlannedCourseCommand, repository: Any, current: PlannedCourse
) -> None:
    """Revisions have no upper limit."""
    revision = 10**5000
    repository.load.return_value = replace(current, revision=revision)

    output = command.execute(
        UpdatePlannedCourseCommand.InputData(
            id=current.id, expected_revision=revision, user_note="Edited."
        )
    )

    assert output.revision == revision + 1


def test_storage_failure_reaches_the_caller(
    command: UpdatePlannedCourseCommand, repository: Any, current: PlannedCourse
) -> None:
    """A failed replacement keeps its category; the commit outcome is uncertain."""
    failure = StorageFailure("Storage could not complete the operation.")
    repository.replace.side_effect = failure

    with pytest.raises(StorageFailure) as reported:
        command.execute(
            UpdatePlannedCourseCommand.InputData(
                id=current.id, expected_revision=1, user_note="Edited."
            )
        )

    assert reported.value is failure
